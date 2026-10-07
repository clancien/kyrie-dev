#!/usr/bin/env python3
"""Core reutilizable para consultas API de Banco de Chile (modo server)."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CACHE_DIR = BASE_DIR / "cache"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_TIMEOUT = 30

BASE_URL = "https://portalpersonas.bancochile.cl"
BASE_API_URL = f"{BASE_URL}/mibancochile/rest/persona"
REFERER = f"{BASE_URL}/mibancochile-web/front/persona/index.html"
MOV_FRONT = f"{REFERER}#/movimientos/cuenta/saldos-movimientos/"

SALDOS_ENDPOINT = "bff-pp-prod-ctas-saldos/productos/cuentas/saldos"
MOV_ENDPOINT = "bff-pper-prd-cta-movimientos/movimientos/getCartola"
TARJETAS_ENDPOINT = "tarjetas/widget/informacion-tarjetas"
SELECTOR_PRODUCTOS_ENDPOINT = "selectorproductos/selectorProductos/obtenerProductos"


class ServerApiError(RuntimeError):
    """Error controlado en flujo server API."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def cleanup_cache_api_files(cache_dir: Path) -> None:
    stale_files = [
        "all_api_server_latest.json",
        "selector_productos_server_latest.json",
        "saldos_server_latest.json",
        "tarjetas_server_latest.json",
        "movimientos_api_server_latest.json",
        "movimientos_server_latest.json",
    ]
    for name in stale_files:
        p = cache_dir / name
        if p.exists():
            p.unlink()


def load_storage_state_cookies(cache_dir: Path) -> list[dict[str, Any]]:
    state_path = cache_dir / "session_storage_state.json"
    if not state_path.exists():
        raise ServerApiError(
            f"No existe {state_path}. Ejecuta primero bancochile_login_ui.py para cachear sesion."
        )
    state = read_json(state_path)
    cookies = state.get("cookies", [])
    if not isinstance(cookies, list) or not cookies:
        raise ServerApiError(f"Storage state invalido en {state_path}: sin cookies.")
    return cookies


def build_session(cookies: list[dict[str, Any]]) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": REFERER,
            "Origin": BASE_URL,
        }
    )

    for c in cookies:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain") or "portalpersonas.bancochile.cl"
        path = c.get("path") or "/"
        if name and value:
            session.cookies.set(name, value, domain=domain, path=path)
    return session


def cookie_value(session: requests.Session, name: str) -> str:
    for cookie in session.cookies:
        if cookie.name == name:
            return cookie.value
    return ""


def parse_response(endpoint: str, response: requests.Response) -> dict[str, Any] | list[Any]:
    text = response.text
    ctype = response.headers.get("Content-Type", "")
    if "application/json" not in ctype.lower():
        preview = text[:500].replace("\n", " ")
        raise ServerApiError(
            f"{endpoint} devolvio no-JSON (status={response.status_code}, content-type={ctype}, body='{preview}')"
        )
    try:
        payload = response.json()
    except Exception as exc:  # noqa: BLE001
        raise ServerApiError(f"{endpoint} JSON invalido: {exc}") from exc
    if response.status_code >= 400:
        raise ServerApiError(f"{endpoint} error {response.status_code}: {payload}")
    return payload


def call_get(session: requests.Session, endpoint: str) -> dict[str, Any] | list[Any]:
    url = f"{BASE_API_URL}/{endpoint}"
    headers = {}
    dtpc = cookie_value(session, "dtPC")
    if dtpc:
        headers["x-dtpc"] = dtpc
    response = session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    return parse_response(endpoint, response)


def call_post(session: requests.Session, endpoint: str, payload: dict[str, Any]) -> dict[str, Any] | list[Any]:
    url = f"{BASE_API_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    dtpc = cookie_value(session, "dtPC")
    if dtpc:
        headers["x-dtpc"] = dtpc
    response = session.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
    return parse_response(endpoint, response)


def extract_accounts(saldos_raw: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    items = saldos_raw if isinstance(saldos_raw, list) else []
    accounts = []
    for item in items:
        if not isinstance(item, dict):
            continue
        numero = str(item.get("numero", "")).strip()
        cod = str(item.get("codProducto") or item.get("codigoProducto") or "").strip()
        moneda = str(item.get("moneda", "")).strip() or "CLP"
        if not numero or not cod:
            continue
        accounts.append(
            {
                "nombreCliente": str(item.get("nombreCliente", "")).strip(),
                "rutCliente": str(item.get("rutCliente", "")).strip(),
                "numero": numero,
                "mascara": str(item.get("mascara", "")).strip() or f"****{numero[-4:]}",
                "selected": bool(item.get("ctaCte", False) or item.get("selected", False)),
                "codigoProducto": cod,
                "claseCuenta": str(item.get("claseCuenta", "")).strip() or ("CCNMN1" if cod == "CTD" else ""),
                "moneda": moneda,
            }
        )
    return accounts


def extract_accounts_from_selector(selector_raw: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if not isinstance(selector_raw, dict):
        return []
    rut = str(selector_raw.get("rut", "")).strip()
    nombre = str(selector_raw.get("nombre", "")).strip()
    productos = selector_raw.get("productos", [])
    if not isinstance(productos, list):
        return []

    accounts: list[dict[str, Any]] = []
    for item in productos:
        if not isinstance(item, dict):
            continue
        numero = str(item.get("numero", "")).strip()
        codigo = str(item.get("codigo", "")).strip()
        moneda = str(item.get("codigoMoneda", "")).strip() or "CLP"
        tipo = str(item.get("tipo", "")).strip().lower()
        if not numero:
            continue
        # Nos interesan productos con cuenta real para construir cartola.
        if codigo != "CTD" and "cuenta" not in tipo and "linea" not in tipo:
            continue

        accounts.append(
            {
                "nombreCliente": nombre,
                "rutCliente": rut,
                "numero": numero,
                "mascara": str(item.get("mascara", "")).strip() or f"****{numero[-4:]}",
                "selected": bool(codigo == "CTD"),
                "codigoProducto": codigo,
                "claseCuenta": str(item.get("claseCuenta", "")).strip() or ("CCNMN1" if codigo == "CTD" else ""),
                "moneda": moneda,
                "tipoProducto": tipo,
                "labelProducto": str(item.get("label", "")).strip(),
            }
        )
    return accounts


def pick_account(accounts: list[dict[str, Any]], account_number: str) -> dict[str, Any]:
    if account_number:
        for account in accounts:
            if account["numero"] == account_number:
                return account
        raise ServerApiError(f"No se encontro cuenta {account_number}.")
    for account in accounts:
        if account.get("selected"):
            return account
    for account in accounts:
        if account.get("codigoProducto") == "CTD":
            return account
    if not accounts:
        raise ServerApiError("No se detectaron cuentas en saldos.")
    return accounts[0]


def format_rut(raw: str) -> str:
    cleaned = re.sub(r"[^0-9kK]", "", raw)
    if len(cleaned) <= 1:
        return raw
    return f"{cleaned[:-1]}-{cleaned[-1].upper()}"


def enrich_account_from_env(account: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(account)
    if not enriched.get("rutCliente"):
        rut_env = os.getenv("BANCHILE_RUT", "").strip()
        if rut_env:
            enriched["rutCliente"] = format_rut(rut_env)
    if not enriched.get("nombreCliente"):
        enriched["nombreCliente"] = os.getenv("BANCHILE_NOMBRE_CLIENTE", "").strip()
    if not enriched.get("claseCuenta") and str(enriched.get("codigoProducto", "")).upper() == "CTD":
        enriched["claseCuenta"] = os.getenv("BANCHILE_CLASE_CUENTA", "CCNMN1").strip()
    if not enriched.get("mascara"):
        numero = str(enriched.get("numero", "")).strip()
        if numero:
            enriched["mascara"] = f"****{numero[-4:]}"
    enriched["selected"] = True
    return enriched


def _find_candidate_lists(node: Any, found: list[list[dict[str, Any]]]) -> None:
    if isinstance(node, dict):
        for value in node.values():
            _find_candidate_lists(value, found)
    elif isinstance(node, list):
        if node and all(isinstance(x, dict) for x in node):
            found.append(node)
        for item in node:
            _find_candidate_lists(item, found)


def extract_movements(raw: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(raw, list) and all(isinstance(x, dict) for x in raw):
        return raw
    if not isinstance(raw, dict):
        return []

    # Es la estructura actual de getCartola. Priorizarla evita confundir listas
    # auxiliares de respuestas vacías con movimientos y seguir paginando sin fin.
    direct_movements = raw.get("movimientos")
    if isinstance(direct_movements, list) and all(isinstance(x, dict) for x in direct_movements):
        return direct_movements

    candidates: list[list[dict[str, Any]]] = []
    _find_candidate_lists(raw, candidates)
    if not candidates:
        return []

    ranked = []
    for candidate in candidates:
        first = candidate[0] if candidate else {}
        keys = {k.lower() for k in first.keys()}
        score = sum(
            1 for hint in ("fecha", "monto", "descripcion", "glosa", "saldo", "mov")
            if any(hint in key for key in keys)
        )
        ranked.append((score, len(candidate), candidate))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return ranked[0][2]


def parse_month(value: str) -> tuple[int, int]:
    """Valida un mes YYYY-MM y devuelve año y mes."""
    match = re.fullmatch(r"(\d{4})-(\d{2})", value)
    if not match:
        raise ServerApiError("El mes debe tener formato YYYY-MM.")
    year, month = (int(part) for part in match.groups())
    # 9999-12 no permite calcular el comienzo del mes siguiente con datetime.
    if not 1 <= year <= 9998 or not 1 <= month <= 12:
        raise ServerApiError("El mes debe tener formato YYYY-MM.")
    return year, month


def month_date_range(month_value: str) -> dict[str, str]:
    """Construye el intervalo [inicio de mes, inicio del siguiente) en hora Chile."""
    year, month = parse_month(month_value)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    timezone = ZoneInfo("America/Santiago")

    def to_utc_iso(value: datetime) -> str:
        return value.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    return {
        "month": month_value,
        "fechaInicio": to_utc_iso(datetime(year, month, 1, tzinfo=timezone)),
        "fechaFin": to_utc_iso(datetime(next_year, next_month, 1, tzinfo=timezone)),
    }


def month_ranges(from_month: str, to_month: str) -> list[dict[str, str]]:
    """Devuelve los rangos mensuales inclusivos desde from_month hasta to_month."""
    start_year, start_month = parse_month(from_month)
    end_year, end_month = parse_month(to_month)
    if (start_year, start_month) > (end_year, end_month):
        raise ServerApiError("--from-month no puede ser posterior a --to-month.")

    ranges = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        ranges.append(month_date_range(f"{year:04d}-{month:02d}"))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return ranges


def has_next_page(raw: dict[str, Any] | list[Any], movements: list[dict[str, Any]]) -> bool:
    """Respeta la bandera del backend y conserva un fallback para esquemas antiguos."""
    if isinstance(raw, dict):
        page_info = raw.get("pagina")
        if isinstance(page_info, list) and page_info and isinstance(page_info[0], dict):
            more = str(page_info[0].get("masPaginas", "")).strip().upper()
            if more:
                return more in {"S", "SI", "Y", "YES", "TRUE", "1"}
    return bool(movements)


def run_all_api(
    cache_dir: Path,
    output_dir: Path,
    account_number: str = "",
    from_index: int = 1,
    step: int = 100,
    max_pages: int = 2,
    incluir_tarjetas_selector: bool = False,
    from_month: str = "",
    to_month: str = "",
) -> dict[str, Any]:
    # Cache se usa solo para sesión (storage state), no para resultados API.
    cleanup_cache_api_files(cache_dir)

    cookies = load_storage_state_cookies(cache_dir)
    session = build_session(cookies)

    session.get(MOV_FRONT, timeout=DEFAULT_TIMEOUT)

    selector_endpoint = (
        f"{SELECTOR_PRODUCTOS_ENDPOINT}?incluirTarjetas="
        f"{'true' if incluir_tarjetas_selector else 'false'}"
    )
    selector_raw = call_get(session, selector_endpoint)
    # Siempre consultar saldos y guardar el raw en la salida final.
    saldos_raw = call_get(session, SALDOS_ENDPOINT)
    accounts = extract_accounts_from_selector(selector_raw)
    if not accounts:
        # Fallback de compatibilidad: si cambia selector, usar cuentas desde saldos.
        accounts = extract_accounts(saldos_raw)

    if account_number:
        accounts_to_query = [enrich_account_from_env(pick_account(accounts, account_number))]
    else:
        accounts_to_query = [enrich_account_from_env(a) for a in accounts]

    from_index = max(1, from_index)
    step = max(1, step)
    max_pages = max(1, max_pages)
    date_ranges = month_ranges(from_month, to_month) if from_month and to_month else [None]

    movements_all = []
    movimientos_raw_pages: list[dict[str, Any]] = []
    movements_by_account: list[dict[str, Any]] = []

    for account in accounts_to_query:
        pages = []
        account_movements = []
        for date_range in date_ranges:
            for i in range(max_pages):
                pag = from_index + (i * step)
                cabecera = {"statusGenerico": True, "paginacionDesde": pag}
                if date_range:
                    cabecera.update({"fechaInicio": date_range["fechaInicio"], "fechaFin": date_range["fechaFin"]})
                body = {"cuentaSeleccionada": account, "cabecera": cabecera}
                raw = call_post(session, MOV_ENDPOINT, body)
                movimientos_raw_pages.append({"request": body, "response": raw})
                list_candidate = extract_movements(raw)
                pages.append(
                    {
                        "month": date_range["month"] if date_range else None,
                        "paginacionDesde": pag,
                        "raw": raw,
                        "movements_count": len(list_candidate),
                    }
                )
                account_movements.extend(list_candidate)
                movements_all.extend(list_candidate)
                if not has_next_page(raw, list_candidate):
                    break

        movements_by_account.append(
            {
                "account": account,
                "movimientos_total": len(account_movements),
                "movimientos": account_movements,
                "movimientos_pages": pages,
            }
        )

    tarjetas_raw = call_post(session, TARJETAS_ENDPOINT, {})
    payload = {
        "ok": True,
        "mode": "server_no_playwright",
        "accounts_count": len(accounts),
        "accounts_queried_count": len(accounts_to_query),
        "accounts_queried": accounts_to_query,
        "months_queried": [date_range["month"] for date_range in date_ranges if date_range],
        # Respuestas raw exactamente como llegan desde la API.
        "api_raw": {
            "selector_productos": selector_raw,
            "saldos": saldos_raw,
            "movimientos_pages": movimientos_raw_pages,
            "tarjetas": tarjetas_raw,
        },
        # Campos derivados para facilitar consumo local (no alteran api_raw).
        "derived": {
            "movimientos_total": len(movements_all),
            "movimientos": movements_all,
            "movimientos_by_account": movements_by_account,
        },
    }

    # Archivos por endpoint (raw) para consumo modular.
    api_selector_payload = {"ok": True, "endpoint": selector_endpoint, "raw": selector_raw}
    api_saldos_payload = {"ok": True, "endpoint": SALDOS_ENDPOINT, "raw": saldos_raw}
    api_tarjetas_payload = {"ok": True, "endpoint": TARJETAS_ENDPOINT, "raw": tarjetas_raw}
    api_movimientos_payload = {"ok": True, "endpoint": MOV_ENDPOINT, "raw_pages": movimientos_raw_pages}

    movimientos_payload = {
        "ok": True,
        "mode": "server_no_playwright",
        "accounts_queried_count": len(accounts_to_query),
        "months_queried": [date_range["month"] for date_range in date_ranges if date_range],
        "movimientos_total": len(movements_all),
        "movimientos": movements_all,
        "movimientos_by_account": movements_by_account,
        "movimientos_pages_raw": movimientos_raw_pages,
    }

    write_json(output_dir / "selector_productos_server_latest.json", api_selector_payload)
    write_json(output_dir / "saldos_server_latest.json", api_saldos_payload)
    write_json(output_dir / "tarjetas_server_latest.json", api_tarjetas_payload)
    write_json(output_dir / "movimientos_api_server_latest.json", api_movimientos_payload)

    write_json(output_dir / "movimientos_server_latest.json", movimientos_payload)
    return payload
