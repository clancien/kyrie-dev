import datetime as dt, json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from santander_server_core import *


class CoreTests(unittest.TestCase):
    def test_range(self):
        now = dt.datetime(2026, 10, 14, tzinfo=TZ)
        self.assertEqual(months(now=now), ["2026-08", "2026-09", "2026-10"])
        for a, b in [("2026-13", None), ("2026-10", "2026-09")]:
            with self.assertRaises(BankError):
                months(a, b, now)

    def test_partition(self):
        a, b = bounds("2026-09")
        calls = []

        def fetch(start, end):
            calls.append((start, end))
            count = 50 if (start, end) == (a, b) else 31 if start == a else 20
            return [
                {"accountingDate": start.isoformat(), "id": i} for i in range(count)
            ]

        self.assertEqual(len(partition(fetch, a, b)), 51)
        self.assertEqual(calls[1][1] + dt.timedelta(days=1), calls[2][0])

    def test_saturated_day(self):
        day = dt.date(2026, 9, 1)
        with self.assertRaisesRegex(BankError, "truncado"):
            partition(lambda a, b: [{"accountingDate": a.isoformat()}] * 50, day, day)

    def test_foreign_date(self):
        with self.assertRaises(BankError):
            partition(
                lambda a, b: [{"accountingDate": "2026-08-31"}], *bounds("2026-09")
            )

    def test_exact_and_unknown(self):
        self.assertEqual(amount("12345678901234567890.01"), "12345678901234567890.01")
        self.assertEqual(amount("0"), "0")
        self.assertIsNone(amount(None))
        with self.assertRaises(BankError):
            amount("1.234,56")

    def test_dates_and_duplicates(self):
        raw = {
            "accountingDate": "2026-10-15",
            "transactionDate": "2026-10-14",
            "chargePaymentFlag": "D",
            "movementAmount": "0.10",
        }
        row = normalize_movement(raw, "USD")
        self.assertEqual(row["accounting_date"], "2026-10-15")
        self.assertEqual(row["transaction_date"], "2026-10-14")
        with tempfile.TemporaryDirectory() as path:
            s = Store(Path(path) / "db")
            s.commit_month(
                "h",
                "a",
                "USD",
                "2026-10",
                [row, row],
                dt.datetime(2026, 10, 14, tzinfo=TZ),
            )
            self.assertEqual(len(s.projection()["partitions"][0]["movements"]), 2)

    def test_closure_new_empty_and_failure(self):
        for initial in ([], [{"amount": "1"}]):
            with self.subTest(initial=initial), tempfile.TemporaryDirectory() as path:
                s = Store(Path(path) / "db")
                s.commit_month(
                    "h",
                    "a",
                    "CLP",
                    "2026-10",
                    initial,
                    dt.datetime(2026, 10, 14, tzinfo=TZ),
                )
                self.assertFalse(s.reusable("h", "a", "CLP", "2026-10"))
                try:
                    partition(
                        lambda a, b: (_ for _ in ()).throw(BankError("red")),
                        *bounds("2026-10"),
                    )
                except BankError:
                    pass
                self.assertEqual(s.projection()["partitions"][0]["movements"], initial)
                self.assertFalse(s.reusable("h", "a", "CLP", "2026-10"))
                s.commit_month(
                    "h",
                    "a",
                    "CLP",
                    "2026-10",
                    initial + [{"amount": "2"}],
                    dt.datetime(2026, 11, 1, tzinfo=TZ),
                )
                self.assertTrue(s.projection()["partitions"][0]["closed"])
                s.export()
                self.assertEqual(
                    len(
                        json.loads((Path(path) / "history.json").read_text())[
                            "partitions"
                        ]
                    ),
                    1,
                )

    def test_lock(self):
        with tempfile.TemporaryDirectory() as path:
            s = Store(Path(path) / "db")
            with s.writer():
                with self.assertRaises(Busy):
                    with Store(s.path).writer():
                        pass


if __name__ == "__main__":
    unittest.main()

from unittest.mock import patch


class UpdateClosureTests(unittest.TestCase):
    def test_full_update_closure(self):
        import santander_server_core as core

        class Clock(dt.datetime):
            current = dt.datetime(2026, 10, 14, tzinfo=TZ)

            @classmethod
            def now(cls, tz=None):
                return cls.current

        class Fake:
            calls = []
            rows = []
            fail = False

            def __init__(self, session):
                pass

            def validate(self, holder=None):
                return "h"

            def products(self):
                return [
                    dict(
                        id="a",
                        type="vista",
                        label="Vista",
                        mask="••••0001",
                        lines=[
                            dict(currency="CLP", contract="1", commercial_group="g")
                        ],
                    )
                ]

            def post(self, *args):
                return {"balance": {"totalBalance": "0", "availableBalance": "0"}}

            def account_body(self, line):
                return {}

            def movements(self, line, start, end):
                self.calls.append((start, end))
                if self.fail:
                    raise BankError("Fallo final")
                return self.rows

        for initially_empty in (False, True):
            with (
                self.subTest(empty=initially_empty),
                tempfile.TemporaryDirectory() as path,
                patch.object(core, "Adapter", Fake),
                patch.object(core, "load_session", return_value={}),
                patch.object(core.dt, "datetime", Clock),
            ):
                store = Store(Path(path) / "db")
                Fake.calls = []
                Fake.fail = False
                Clock.current = Clock(2026, 10, 14, tzinfo=TZ)
                row = dict(
                    accountingDate="2026-10-10",
                    transactionDate="2026-10-09",
                    chargePaymentFlag="D",
                    movementAmount="1",
                )
                Fake.rows = [] if initially_empty else [row]
                update(store, ["2026-10"])
                self.assertFalse(store.reusable("h", "a", "CLP", "2026-10"))
                Clock.current = Clock(2026, 11, 1, tzinfo=TZ)
                Fake.fail = True
                with self.assertRaises(BankError):
                    update(store, ["2026-10"])
                self.assertFalse(store.reusable("h", "a", "CLP", "2026-10"))
                self.assertEqual(
                    len(store.projection()["partitions"][0]["movements"]),
                    0 if initially_empty else 1,
                )
                Fake.fail = False
                Fake.rows = Fake.rows + [dict(row, accountingDate="2026-10-31")]
                update(store, ["2026-10"])
                self.assertTrue(store.reusable("h", "a", "CLP", "2026-10"))
                count = len(Fake.calls)
                update(store, ["2026-10"])
                self.assertEqual(len(Fake.calls), count)
                self.assertEqual(
                    len(store.projection()["partitions"][0]["movements"]),
                    1 if initially_empty else 2,
                )

    def test_previous_balance_survives(self):
        with tempfile.TemporaryDirectory() as path:
            store = Store(Path(path) / "db")
            p = dict(
                id="a", lines=[dict(currency="CLP", balance={"availableBalance": "19"})]
            )
            store.products([p], "h")
            store.products([dict(id="a", lines=[dict(currency="CLP")])], "h")
            self.assertEqual(
                store.projection()["products"][0]["lines"][0]["balance"][
                    "availableBalance"
                ],
                "19",
            )
            store.resource("balance")
            success = store.projection()["resources"][0]["updated"]
            store.resource("balance", "error")
            self.assertEqual(store.projection()["resources"][0]["updated"], success)


class AdapterTests(unittest.TestCase):
    def session(self):
        return dict(
            holder="123456785",
            hosts={
                "api-dsk.santander.cl": {"authorization": "synthetic"},
                "openbanking.santander.cl": {"authorization": "synthetic"},
            },
            probes={
                "api-dsk.santander.cl": dict(url=PRODUCTS, body={}),
                "openbanking.santander.cl": dict(url=BALANCES, body={}),
            },
        )

    def test_http_business_and_holder(self):
        import santander_server_core as core
        from unittest.mock import Mock

        adapter = Adapter(self.session())
        response = Mock(status_code=200)
        response.json.return_value = {
            "additionalInfo": [{"key": "code-ms", "value": "00"}],
            "balance": {},
        }
        adapter.http.post = Mock(return_value=response)
        with (
            tempfile.TemporaryDirectory() as path,
            patch.object(core, "ROOT", Path(path)),
        ):
            self.assertIn("balance", adapter.post(BALANCES, {}))
        response.status_code = 401
        with self.assertRaises(SessionExpired):
            adapter.post(BALANCES, {})
        response.status_code = 200
        response.json.side_effect = ValueError()
        with self.assertRaises(BankError):
            adapter.post(BALANCES, {})
        response.json.side_effect = None
        response.json.return_value = {
            "additionalInfo": [{"key": "code-ms", "value": "99"}]
        }
        with self.assertRaises(BankError):
            adapter.post(BALANCES, {})
        adapter.post = Mock(
            side_effect=[
                {"DATA": {"OUTPUT": {"ESCALARES": {"NUMERODOCUMENTO": "999999999"}}}}
            ]
        )
        with self.assertRaisesRegex(BankError, "Titular"):
            adapter.validate()

    def test_card_decimal_and_codes(self):
        from unittest.mock import Mock

        session = self.session()
        session["card_template"] = {"Entrada": {}}
        a = Adapter(session)
        a.post = Mock(
            return_value={
                "DATA": {
                    "MatrizMovimientos": [
                        {
                            "Fecha": "14/10/2026",
                            "IndicadorDebeHaber": "H",
                            "Importe": "19,03",
                            "Descripcion": "PAGO",
                        }
                    ]
                }
            }
        )
        line = dict(currency="USD", office="0001", contract="synthetic")
        row = a.card_movements(line)[0]
        self.assertEqual(row["amount"], "19.03")
        self.assertEqual(row["kind"], "abono")
        self.assertIsNone(row["balance"])
        a.post.return_value["DATA"]["MatrizMovimientos"][0]["IndicadorDebeHaber"] = "X"
        with self.assertRaises(BankError):
            a.card_movements(line)

    def test_verified_account_format(self):
        row = normalize_movement(
            dict(
                accountingDate="2026-09-01",
                transactionDate="2026-08-31",
                chargePaymentFlag="D",
                movementAmount="00000000002500-",
                newBalance="000000000001000",
            ),
            "CLP",
        )
        self.assertEqual(row["amount"], "2500")
        self.assertEqual(row["balance"], "1000")


class IdentityExportTests(unittest.TestCase):
    def test_verified_product_fixture(self):
        from unittest.mock import Mock

        a = Adapter(
            dict(holder="synthetic", probes={"api-dsk.santander.cl": {"body": {}}})
        )
        a.post = Mock(
            return_value=json.loads(
                (Path(__file__).parent / "fixtures/products.json").read_text()
            )
        )
        products = a.products()
        self.assertEqual(len(products), 3)
        card = next(p for p in products if p["type"] == "tarjeta")
        self.assertEqual([x["currency"] for x in card["lines"]], ["CLP", "USD"])
        self.assertEqual(card["lines"][0]["available"], "0")
        self.assertIsNone(card["lines"][0]["used"])

    def test_export_historical_and_identity(self):
        with tempfile.TemporaryDirectory() as path:
            store = Store(Path(path) / "db")
            store.products(
                [
                    dict(
                        id="a",
                        lines=[
                            dict(
                                currency="CLP",
                                contract="private-contract",
                                office="private-office",
                            )
                        ],
                    )
                ],
                "private-holder",
            )
            store.products([dict(id="a0", lines=[])], "private-holder")
            for id in ("a", "a0"):
                store.commit_month(
                    "private-holder",
                    id,
                    "CLP",
                    "2026-09",
                    [{"bank_id": "same"}, {"bank_id": "same"}],
                    dt.datetime(2026, 10, 1, tzinfo=TZ),
                )
            store.export()
            export = json.loads((Path(path) / "history.json").read_text())
            self.assertEqual(len(export["products"]), 2)
            self.assertEqual(sum(len(x["movements"]) for x in export["partitions"]), 4)
            self.assertNotIn("private-contract", json.dumps(store.public_projection()))
            self.assertNotIn("private-holder", json.dumps(store.public_projection()))
            with self.assertRaises(BankError):
                store.products([], "foreign-holder")

    def test_empty_identity_and_alias_lock(self):
        with tempfile.TemporaryDirectory() as path:
            store = Store(Path(path) / "db")
            store.products([], "h")
            self.assertEqual(store.holder(), "h")
            with self.assertRaises(BankError):
                store.products([], "other")
            alias = Path(path) / "alias"
            alias.symlink_to(store.path)
            with store.writer():
                with self.assertRaises(Busy):
                    with Store(alias).writer():
                        pass


class FilePermissionsTests(unittest.TestCase):
    def test_custom_database_preserves_existing_parent_permissions(self):
        import stat

        with tempfile.TemporaryDirectory() as path:
            parent = Path(path)
            parent.chmod(0o755)
            store = Store(parent / "history.sqlite")
            store.export()
            self.assertEqual(stat.S_IMODE(parent.stat().st_mode), 0o755)
            self.assertEqual(stat.S_IMODE(store.path.stat().st_mode), 0o600)
            self.assertEqual(
                stat.S_IMODE((parent / "history.json").stat().st_mode), 0o600
            )


class CoverageRegressionTests(unittest.TestCase):
    def test_tiny_decimal_is_not_exponential(self):
        self.assertEqual(amount("0.0000001"), "0.0000001")

    def test_later_leaf_failure_keeps_previous_partition(self):
        import santander_server_core as core

        class Fake:
            def __init__(self, session):
                pass

            def validate(self, holder):
                return "h"

            def products(self):
                return [
                    dict(
                        id="a", type="vista", lines=[dict(currency="CLP", contract="1")]
                    )
                ]

            def account_body(self, line):
                return {}

            def post(self, *args):
                return {"balance": {"totalBalance": "0"}}

            def movements(self, line, start, end):
                if (end - start).days > 15:
                    return [dict(accountingDate=start.isoformat())] * 50
                if start.day > 1:
                    raise BankError("Segunda hoja fallida")
                return [
                    dict(
                        accountingDate=start.isoformat(),
                        chargePaymentFlag="D",
                        movementAmount="1",
                    )
                ]

        with tempfile.TemporaryDirectory() as path:
            store = Store(Path(path) / "history.sqlite")
            store.commit_month(
                "h",
                "a",
                "CLP",
                "2026-09",
                [{"previous": True}],
                dt.datetime(2026, 9, 10, tzinfo=TZ),
            )
            with (
                patch.object(core, "Adapter", Fake),
                patch.object(core, "load_session", return_value={}),
            ):
                with self.assertRaisesRegex(BankError, "Segunda hoja"):
                    update(store, ["2026-09"])
            self.assertEqual(
                store.projection()["partitions"][0]["movements"], [{"previous": True}]
            )
            self.assertFalse(store.reusable("h", "a", "CLP", "2026-09"))
            with store.writer():
                pass
