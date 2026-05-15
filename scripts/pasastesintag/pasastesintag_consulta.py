#!/usr/bin/env python3
"""Consulta de deudas en pasastesintag.cl.

Implementa el flujo observado en el frontend público:
1. GET /resumen-pagos y extrae el JWT temporal de la cookie authorization
   o desde __NEXT_DATA__ en versiones antiguas del frontend
2. Genera un token de reCAPTCHA invisible usando la sitekey pública
3. POST /api/consulta_patente con patente + token + authorization

Dependencias: requests
Uso:
  python3 doc/script/pasastesintag_consulta.py PDHT36
  python3 doc/script/pasastesintag_consulta.py PDHT36 --pretty
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from dataclasses import dataclass
from typing import Any

import requests


SITE_URL = "https://pasastesintag.cl"
RESUMEN_URL = f"{SITE_URL}/resumen-pagos"
CONSULTA_URL = f"{SITE_URL}/api/consulta_patente"
RECAPTCHA_API_JS = "https://www.google.com/recaptcha/api.js?render=explicit"
RECAPTCHA_ANCHOR_URL = "https://www.google.com/recaptcha/api2/anchor"
RECAPTCHA_RELOAD_URL = "https://www.google.com/recaptcha/api2/reload"
RECAPTCHA_SITE_KEY = "6Ld2OMcoAAAAAL_CG7xwF_5v_AVZwF2g5fKqvJaG"
DEFAULT_TIMEOUT = 30


class PasasteSinTagError(RuntimeError):
    """Error controlado para el flujo de consulta."""


@dataclass
class ConsultaResult:
    plate: str
    jwt: str
    recaptcha_token: str
    response: dict[str, Any]


def encode_origin(origin: str) -> str:
    return base64.urlsafe_b64encode(origin.encode("utf-8")).decode("ascii").rstrip("=")


def normalize_plate(plate: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", plate).upper()
    if not normalized:
        raise PasasteSinTagError("La patente no puede quedar vacia luego de normalizarla.")
    return normalized


def extract_next_data(html: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise PasasteSinTagError("No se encontro __NEXT_DATA__ en /resumen-pagos.")
    return json.loads(match.group(1))


def get_jwt(session: requests.Session) -> str:
    response = session.get(
        RESUMEN_URL,
        headers={"Referer": f"{SITE_URL}/"},
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()

    jwt = response.cookies.get("authorization") or session.cookies.get("authorization")
    if jwt:
        return jwt

    next_data = extract_next_data(response.text)
    jwt = next_data.get("props", {}).get("pageProps", {}).get("jwt")
    if not jwt:
        raise PasasteSinTagError(
            "No se pudo extraer el jwt temporal desde cookie authorization ni desde __NEXT_DATA__."
        )
    return jwt


def get_recaptcha_release(session: requests.Session) -> str:
    response = session.get(RECAPTCHA_API_JS, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    match = re.search(r"releases/([^/]+)/", response.text)
    if not match:
        raise PasasteSinTagError("No se pudo detectar la version release de reCAPTCHA.")
    return match.group(1)


def get_recaptcha_anchor_token(session: requests.Session, release: str) -> str:
    response = session.get(
        RECAPTCHA_ANCHOR_URL,
        params={
            "ar": "1",
            "k": RECAPTCHA_SITE_KEY,
            "co": encode_origin(SITE_URL),
            "hl": "es",
            "v": release,
            "size": "invisible",
            "cb": "pasastesintag-script",
        },
        headers={"Referer": f"{SITE_URL}/"},
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    match = re.search(r'id="recaptcha-token" value="([^"]+)"', response.text)
    if not match:
        raise PasasteSinTagError("No se pudo extraer el recaptcha anchor token.")
    return match.group(1)


def get_recaptcha_token(session: requests.Session) -> str:
    release = get_recaptcha_release(session)
    anchor_token = get_recaptcha_anchor_token(session, release)
    response = session.post(
        RECAPTCHA_RELOAD_URL,
        params={"k": RECAPTCHA_SITE_KEY},
        data={
            "v": release,
            "reason": "q",
            "c": anchor_token,
            "k": RECAPTCHA_SITE_KEY,
            "co": encode_origin(SITE_URL),
            "hl": "es",
            "size": "invisible",
        },
        headers={
            "Referer": RECAPTCHA_ANCHOR_URL,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    match = re.search(r'\["rresp","([^"]+)"', response.text)
    if not match:
        raise PasasteSinTagError("No se pudo extraer el token rresp de reCAPTCHA.")
    return match.group(1)


def consultar_patente(session: requests.Session, plate: str, jwt: str, recaptcha_token: str) -> dict[str, Any]:
    response = session.post(
        CONSULTA_URL,
        json={
            "patente": plate,
            "token": recaptcha_token,
            "authorization": f"Bearer {jwt}",
        },
        headers={
            "Origin": SITE_URL,
            "Referer": RESUMEN_URL,
            "authorization": f"Bearer {jwt}",
        },
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, str):
        raise PasasteSinTagError(f"Respuesta inesperada del servicio: {payload}")
    return payload


def run_query(plate: str) -> ConsultaResult:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        }
    )

    normalized_plate = normalize_plate(plate)
    jwt = get_jwt(session)
    recaptcha_token = get_recaptcha_token(session)
    response = consultar_patente(session, normalized_plate, jwt, recaptcha_token)
    return ConsultaResult(
        plate=normalized_plate,
        jwt=jwt,
        recaptcha_token=recaptcha_token,
        response=response,
    )


def print_human_summary(result: ConsultaResult) -> None:
    payload = result.response
    print(f"Patente: {result.plate}")
    print(f"Status: {payload.get('status')}")
    print(f"Code: {payload.get('code')}")
    if payload.get("message"):
        print(f"Mensaje: {payload['message']}")
    data = payload.get("data")
    if isinstance(data, list):
        print(f"Bloques de deuda: {len(data)}")
    if payload.get("fecha_inicio") or payload.get("fecha_fin"):
        print(
            "Ventana consultada: "
            f"{payload.get('fecha_inicio', '?')} -> {payload.get('fecha_fin', '?')}"
        )


def build_success_payload(result: ConsultaResult, show_tokens: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "plate": result.plate,
        "response": result.response,
    }
    if show_tokens:
        payload["jwt"] = result.jwt
        payload["recaptcha_token"] = result.recaptcha_token
    return payload


def build_error_payload(error_type: str, message: str, status_code: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "error_type": error_type,
        "message": message,
    }
    if status_code is not None:
        payload["status_code"] = status_code
    return payload


def print_json_payload(payload: dict[str, Any], pretty: bool) -> None:
    if pretty:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(json.dumps(payload, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consulta pases sin TAG por patente.")
    parser.add_argument("plate", help="Patente del vehiculo, por ejemplo PDHT36")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Imprime la respuesta JSON completa en formato legible.",
    )
    parser.add_argument(
        "--show-tokens",
        action="store_true",
        help="Tambien imprime el JWT y el token reCAPTCHA obtenidos.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = run_query(args.plate)
    except requests.HTTPError as exc:
        body = exc.response.text[:500] if exc.response is not None else str(exc)
        print_json_payload(
            build_error_payload(
                error_type="http_error",
                message=body,
                status_code=exc.response.status_code if exc.response is not None else None,
            ),
            pretty=args.pretty,
        )
        return 1
    except PasasteSinTagError as exc:
        print_json_payload(
            build_error_payload(error_type="pasastesintag_error", message=str(exc)),
            pretty=args.pretty,
        )
        return 1
    except requests.RequestException as exc:
        print_json_payload(
            build_error_payload(error_type="network_error", message=str(exc)),
            pretty=args.pretty,
        )
        return 1

    print_json_payload(
        build_success_payload(result, show_tokens=args.show_tokens),
        pretty=args.pretty,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
