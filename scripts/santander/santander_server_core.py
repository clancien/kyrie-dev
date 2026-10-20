"""Private Santander read adapter and transactional monthly history."""

from __future__ import annotations
import calendar, contextlib, datetime as dt, decimal, fcntl, json, os, re, sqlite3, tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

os.umask(0o077)
ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo("America/Santiago")
DSK = "https://api-dsk.santander.cl/perdsk/"
OB = "https://openbanking.santander.cl/"
PRODUCTS = DSK + "datosCliente/cruceProductosOnline"
BALANCES = (
    OB
    + "account_balances_transactions_and_withholdings_retail/v1/current-accounts/balances"
)
TRANSACTIONS = (
    OB
    + "account_balances_transactions_and_withholdings_retail/v1/current-accounts/transactions"
)
CARDS = DSK + "tarjetasDeCredito/consultaUltimosMovimientos"


class BankError(RuntimeError):
    pass


class SessionExpired(BankError):
    pass


class Busy(BankError):
    pass


def private_dir(path, restrict_existing=True):
    path = Path(path)
    existed = path.exists()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if restrict_existing or not existed:
        path.chmod(0o700)


def atomic_json(path, value):
    path = Path(path)
    private_dir(path.parent, restrict_existing=False)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as file:
            json.dump(value, file, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def amount(value):
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
        raise BankError("Formato monetario no verificado")
    number = decimal.Decimal(text)
    if not number.is_finite():
        raise BankError("Importe inválido")
    return format(number, "f")


def months(desde=None, hasta=None, now=None):
    now = now or dt.datetime.now(TZ)

    def parse(value):
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value or ""):
            raise BankError("Fecha inválida: use YYYY-MM")
        return dt.date.fromisoformat(value + "-01")

    end = parse(hasta) if hasta else now.astimezone(TZ).date().replace(day=1)
    start = parse(desde) if desde else shift_month(end, -2)
    if start > end:
        raise BankError("Rango invertido")
    result = []
    while start <= end:
        result.append(start.strftime("%Y-%m"))
        start = shift_month(start, 1)
    return result


def shift_month(date, delta):
    index = date.year * 12 + date.month - 1 + delta
    return dt.date(index // 12, index % 12 + 1, 1)


def bounds(month):
    start = dt.date.fromisoformat(month + "-01")
    return start, start.replace(day=calendar.monthrange(start.year, start.month)[1])


def normalize_movement(row, currency):
    try:
        accounting = dt.date.fromisoformat(row["accountingDate"]).isoformat()
        transaction = (
            dt.date.fromisoformat(row["transactionDate"]).isoformat()
            if row.get("transactionDate")
            else None
        )
        kind = {"D": "cargo", "H": "abono"}[row["chargePaymentFlag"]]
    except (KeyError, ValueError, TypeError):
        raise BankError("Esquema de movimiento no verificado") from None
    return dict(
        accounting_date=accounting,
        transaction_date=transaction,
        time=row.get("operationTime"),
        description=row.get("observation"),
        kind=kind,
        amount=amount(
            str(row["movementAmount"])[:-1]
            if currency == "CLP"
            and re.fullmatch(r"\d+-", str(row.get("movementAmount")))
            and kind == "cargo"
            else row.get("movementAmount")
        ),
        balance=amount(row.get("newBalance")),
        bank_id=row.get("movementNumber"),
        currency=currency,
    )


def partition(fetch, start, end):
    rows = fetch(start, end)
    if not isinstance(rows, list):
        raise BankError("Esquema de movimientos desconocido")
    for row in rows:
        try:
            date = dt.date.fromisoformat(row["accountingDate"])
        except (KeyError, ValueError, TypeError):
            raise BankError("Fecha contable inválida") from None
        if not start <= date <= end:
            raise BankError("Respuesta fuera de cobertura solicitada")
    if len(rows) < 50:
        return rows
    if start == end:
        raise BankError("Mes posiblemente truncado: día con 50 o más movimientos")
    middle = start + dt.timedelta(days=(end - start).days // 2)
    return partition(fetch, start, middle) + partition(
        fetch, middle + dt.timedelta(days=1), end
    )


class Store:
    def __init__(self, path=ROOT / "data/history.sqlite"):
        self.path = Path(path).expanduser().resolve()
        private_dir(self.path.parent, restrict_existing=False)
        with self.connect() as db:
            db.executescript(
                "CREATE TABLE IF NOT EXISTS identity(holder TEXT PRIMARY KEY); CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY, holder TEXT NOT NULL, payload TEXT NOT NULL); CREATE TABLE IF NOT EXISTS partitions(holder TEXT,product TEXT,currency TEXT,month TEXT,started TEXT,closed INTEGER,payload TEXT,PRIMARY KEY(holder,product,currency,month)); CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY,updated TEXT,error TEXT);"
            )
        os.chmod(self.path, 0o600)

    @contextlib.contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @contextlib.contextmanager
    def writer(self):
        lock = open(str(self.path) + ".lock", "a")
        os.chmod(lock.name, 0o600)
        try:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Busy("Otra actualización está activa") from None
            yield
        finally:
            lock.close()

    def holder(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT holder FROM identity UNION SELECT DISTINCT holder FROM products"
            ).fetchall()
        return rows[0][0] if rows else None

    def products(self, products, holder):
        if self.holder() not in (None, holder):
            raise BankError("Titular distinto; no se guardaron datos")
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO identity VALUES(?)", (holder,))
            for item in products:
                old = db.execute(
                    "SELECT payload FROM products WHERE id=?", (item["id"],)
                ).fetchone()
                if old:
                    old_lines = {
                        line["currency"]: line for line in json.loads(old[0])["lines"]
                    }
                    for line in item["lines"]:
                        previous = old_lines.get(line["currency"], {})
                        for key in ("balance", "movements", "scope"):
                            if key not in line and key in previous:
                                line[key] = previous[key]
                db.execute(
                    "INSERT OR REPLACE INTO products VALUES(?,?,?)",
                    (item["id"], holder, json.dumps(item)),
                )

    def reusable(self, holder, product, currency, month):
        if month >= dt.datetime.now(TZ).strftime("%Y-%m"):
            return False
        with self.connect() as db:
            row = db.execute(
                "SELECT closed FROM partitions WHERE holder=? AND product=? AND currency=? AND month=?",
                (holder, product, currency, month),
            ).fetchone()
        return bool(row and row[0])

    def commit_month(self, holder, product, currency, month, rows, started):
        end = shift_month(bounds(month)[0], 1)
        closed = started.astimezone(TZ).date() >= end
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO partitions VALUES(?,?,?,?,?,?,?)",
                (
                    holder,
                    product,
                    currency,
                    month,
                    started.isoformat(),
                    int(closed),
                    json.dumps(rows),
                ),
            )

    def resource(self, id, error=None):
        with self.connect() as db:
            old = db.execute(
                "SELECT updated FROM resources WHERE id=?", (id,)
            ).fetchone()
            updated = (
                old[0]
                if error and old
                else None
                if error
                else dt.datetime.now(TZ).isoformat()
            )
            db.execute(
                "INSERT OR REPLACE INTO resources VALUES(?,?,?)", (id, updated, error)
            )

    def projection(self):
        with self.connect() as db:
            products = [
                json.loads(x[0]) for x in db.execute("SELECT payload FROM products")
            ]
            partitions = [
                dict(
                    holder=h,
                    product=p,
                    currency=c,
                    month=m,
                    started=s,
                    closed=bool(cl),
                    complete=True,
                    source="Santander current-accounts/transactions",
                    coverage={
                        "from": bounds(m)[0].isoformat(),
                        "to": bounds(m)[1].isoformat(),
                    },
                    movements=json.loads(v),
                )
                for h, p, c, m, s, cl, v in db.execute(
                    "SELECT * FROM partitions ORDER BY month"
                )
            ]
            resources = [
                dict(id=i, updated=u, error=e)
                for i, u, e in db.execute("SELECT * FROM resources")
            ]
        return dict(products=products, partitions=partitions, resources=resources)

    def public_projection(self):
        value = self.projection()
        for product in value["products"]:
            for line in product["lines"]:
                line.pop("contract", None)
                line.pop("commercial_group", None)
                line.pop("office", None)
        for part in value["partitions"]:
            part.pop("holder", None)
        return value

    def export(self):
        atomic_json(self.path.parent / "history.json", self.projection())


class Adapter:
    def __init__(self, session):
        import requests

        self.session = session
        self.http = requests.Session()
        for cookie in session.get("cookies", []):
            self.http.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie["domain"],
                path=cookie.get("path", "/"),
            )

    def post(self, url, body):
        from urllib.parse import urlsplit

        headers = self.session.get("hosts", {}).get(urlsplit(url).hostname)
        if not headers:
            raise SessionExpired(
                "Falta contexto privado; ejecute run.sh para renovar acceso"
            )
        try:
            response = self.http.post(
                url, json=body, headers=headers, timeout=40, allow_redirects=False
            )
        except Exception:
            raise BankError(
                "Consulta bancaria fallida; revise conexión y renueve acceso"
            ) from None
        if response.status_code in (301, 302, 303, 401, 403):
            raise SessionExpired("Sesión vencida; ejecute run.sh para renovar acceso")
        if response.status_code != 200:
            raise BankError("Banco no disponible")
        try:
            data = response.json()
        except ValueError:
            raise BankError("Respuesta bancaria no reconocida") from None
        if not isinstance(data, dict):
            raise BankError("Esquema bancario desconocido")
        if url.startswith(OB):
            info = data.get("additionalInfo", {})
            if isinstance(info, list):
                info = {
                    item.get("key"): item.get("value")
                    for item in info
                    if isinstance(item, dict)
                }
            if not isinstance(info, dict) or info.get("code-ms") != "00":
                raise BankError("Consulta rechazada por el banco")
        else:
            if data.get("METADATA", {}).get("STATUS") != "0":
                raise BankError("Consulta DSK rechazada")
            if url == PRODUCTS:
                info = data.get("DATA", {}).get("OUTPUT", {}).get("INFO", {})
                if info.get("CODERR") != "00":
                    raise BankError("Consulta de productos rechazada")
            elif url == CARDS:
                info = data.get("DATA", {}).get("Informacion", {})
                if not isinstance(info, dict) or info.get("Codigo") != "00":
                    raise BankError("Resultado de tarjeta no verificado")
        atomic_json(
            ROOT
            / ".cache/raw"
            / (__import__("hashlib").sha256(url.encode()).hexdigest() + ".json"),
            data,
        )
        return data

    def validate(self, expected_holder=None):
        holder = self.session.get("holder")
        normalize = lambda value: (
            re.sub(r"[^0-9kK]", "", str(value)).lower().lstrip("0")
        )
        if (
            not holder
            or expected_holder is not None
            and normalize(expected_holder) != normalize(holder)
        ):
            raise BankError("No se verificó titular de sesión")
        # Require an independently successful request for both hosts.
        probes = self.session.get("probes", {})
        if not all(
            host in probes
            for host in ("api-dsk.santander.cl", "openbanking.santander.cl")
        ):
            raise SessionExpired(
                "Capture productos y saldos en el navegador antes de guardar sesión"
            )
        data = self.post(PRODUCTS, probes["api-dsk.santander.cl"]["body"])
        actual = (
            data.get("DATA", {})
            .get("OUTPUT", {})
            .get("ESCALARES", {})
            .get("NUMERODOCUMENTO")
        )
        normalize = lambda value: (
            re.sub(r"[^0-9kK]", "", str(value)).lower().lstrip("0")
        )
        if not actual or normalize(actual) != normalize(holder):
            raise BankError(
                "Titular no verificado en respuesta bancaria; no se guardaron datos"
            )
        self.post(
            probes["openbanking.santander.cl"]["url"],
            probes["openbanking.santander.cl"]["body"],
        )
        holder = expected_holder if expected_holder is not None else normalize(holder)
        self.session["holder"] = holder
        return holder

    def products(self):
        data = self.post(
            PRODUCTS, self.session["probes"]["api-dsk.santander.cl"]["body"]
        )
        try:
            rows = data["DATA"]["OUTPUT"]["MATRICES"]["MATRIZCAPTACIONES"]["e1"]
        except (KeyError, TypeError):
            raise BankError("Matriz de productos desconocida") from None
        if isinstance(rows, dict):
            rows = [rows]
        result = []
        for row in rows:
            mapping = {
                "00:3000": "corriente",
                "70:0070": "vista",
                "80:2005": "tarjeta",
            }.get(str(row.get("PRODUCTO")) + ":" + str(row.get("SUBPRODUCTO")))
            if mapping == "excluded":
                continue
            if mapping not in ("corriente", "vista", "tarjeta"):
                raise BankError("Código de producto pendiente de verificar")
            currency = row.get("CODIGOMONEDA")
            if currency not in ("CLP", "USD"):
                raise BankError("Código de moneda pendiente de verificar")
            contract = str(row["NUMEROCONTRATO"])
            holder = self.session["holder"]
            id = (
                __import__("hashlib")
                .sha256(
                    json.dumps(
                        ["santander", holder, contract, mapping], separators=(",", ":")
                    ).encode()
                )
                .hexdigest()
            )
            result.append(
                dict(
                    id=id,
                    contract=contract,
                    type=mapping,
                    currency=currency,
                    label=row.get("GLOSACORTA"),
                    mask="••••" + contract[-4:],
                    available=amount(row.get("MONTODISPONIBLE")),
                    used=amount(row.get("MONTOUTILIZADO")),
                    limit=amount(row.get("CUPO")),
                    commercial_group="",
                    office=str(row["OFICINACONTRATO"]),
                )
            )
        # Keep multiple currency lines in one stable product.
        grouped = {}
        for item in result:
            root = grouped.setdefault(
                item["id"],
                dict(
                    id=item["id"],
                    type=item["type"],
                    label=item["label"],
                    mask=item["mask"],
                    lines=[],
                ),
            )
            root["lines"].append(item)
        return list(grouped.values())

    def account_body(self, line):
        return dict(
            accountId=line["office"] + line["contract"],
            currency=line["currency"],
            commercialGroup=line["commercial_group"],
        )

    def card_movements(self, line):
        import copy

        body = copy.deepcopy(self.session.get("card_template"))
        if not body:
            raise SessionExpired("Falta consulta real de tarjeta; renueve con run.sh")
        body["Entrada"].update(
            Centro=line["office"], Cuenta=line["contract"], Moneda=line["currency"]
        )
        data = self.post(CARDS, body)
        rows = data.get("DATA", {}).get("MatrizMovimientos")
        if not isinstance(rows, list):
            raise BankError("Matriz de tarjeta desconocida")
        result = []
        for row in rows:
            try:
                date = dt.datetime.strptime(row["Fecha"], "%d/%m/%Y").date().isoformat()
                kind = {"D": "cargo", "H": "abono"}[row["IndicadorDebeHaber"]]
            except (KeyError, ValueError, TypeError):
                raise BankError("Código o fecha de tarjeta desconocido") from None
            result.append(
                dict(
                    accounting_date=date,
                    transaction_date=None,
                    time=None,
                    description=row.get("Descripcion"),
                    merchant=row.get("Comercio"),
                    kind=kind,
                    amount=amount(
                        str(row["Importe"]).replace(",", ".")
                        if line["currency"] == "USD"
                        and re.fullmatch(r"[+-]?\d+,\d{2}", str(row.get("Importe")))
                        else row.get("Importe")
                    ),
                    balance=None,
                    bank_id=None,
                    currency=line["currency"],
                )
            )
        return result

    def movements(self, line, start, end):
        body = self.account_body(line)
        body.update(openingDate=start.isoformat(), closingDate=end.isoformat())
        data = self.post(TRANSACTIONS, body)
        if not isinstance(data.get("movements"), list):
            raise BankError("Matriz de movimientos desconocida")
        return data["movements"]


def load_session():
    try:
        return json.loads((ROOT / ".cache/session.json").read_text())
    except (OSError, ValueError):
        raise SessionExpired(
            "Sin sesión validada; ejecute run.sh para iniciar acceso"
        ) from None


def update(
    store,
    requested,
    interactive=False,
    progress=lambda state: None,
    force=False,
    account=None,
):
    with store.writer():
        progress("comprobando sesión")
        try:
            adapter = Adapter(load_session())
            holder = adapter.validate(store.holder())
        except SessionExpired:
            if not interactive:
                raise
            progress("esperando acceso")
            from santander_login import login

            adapter = Adapter(login(store.holder()))
            holder = adapter.validate(store.holder())
        products = adapter.products()
        store.products(products, holder)
        failures = []
        for product in products:
            if account and account not in (
                product["id"],
                *(x["contract"] for x in product["lines"]),
            ):
                continue
            for line in product["lines"]:
                resource = product["id"] + ":" + line["currency"]
                if product["type"] == "tarjeta":
                    try:
                        line["movements"] = adapter.card_movements(line)
                        line["scope"] = "Últimos movimientos por facturar"
                        store.products([product], holder)
                        store.resource(resource)
                    except BankError as error:
                        store.resource(resource, str(error))
                        failures.append(str(error))
                    continue
                try:
                    data = adapter.post(BALANCES, adapter.account_body(line))
                    balance = data.get("balance")
                    if not isinstance(balance, dict):
                        raise BankError("Esquema de saldo desconocido")
                    line["balance"] = {
                        key: amount(balance.get(key))
                        for key in (
                            "totalBalance",
                            "availableBalance",
                            "overdraftAgreement",
                            "balanceLca",
                            "agreedTurns",
                            "draftsMade",
                        )
                    }
                    store.products([product], holder)
                    store.resource(resource)
                except BankError as error:
                    store.resource(resource, str(error))
                    failures.append(str(error))
                    continue
                for month in requested:
                    if not force and store.reusable(
                        holder, product["id"], line["currency"], month
                    ):
                        continue
                    progress("descargando " + month)
                    started = dt.datetime.now(TZ)
                    try:
                        raw = partition(
                            lambda a, b: adapter.movements(line, a, b), *bounds(month)
                        )
                        rows = [
                            normalize_movement(row, line["currency"]) for row in raw
                        ]
                        store.commit_month(
                            holder,
                            product["id"],
                            line["currency"],
                            month,
                            rows,
                            started,
                        )
                        store.resource(resource + ":" + month)
                    except BankError as error:
                        store.resource(resource + ":" + month, str(error))
                        failures.append(month + ": " + str(error))
        store.export()
        if failures:
            raise BankError("; ".join(dict.fromkeys(failures)))
        progress("completado")
