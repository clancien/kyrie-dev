#!/usr/bin/env python3
"""Controlador de alertas para pasastesintag.cl, pensado para crontab.

Configura `PASASTESINTAG_PLATE_EMAIL_MAP` en `.env` con la relacion
patente -> email.
El script ejecuta `pasastesintag_consulta.py` para cada patente y, si detecta
deuda, envia un correo al destinatario configurado.

Para evitar spam, por defecto solo reenvia un aviso cuando cambia el contenido
de la deuda detectada. Usa `--send-always` si quieres enviar correo en cada
ejecucion con deuda.

Configura tambien las variables SMTP en `.env`.
Para Gmail normalmente seria algo como:
  PASASTESINTAG_PLATE_EMAIL_MAP={"PDHT36":"destino@example.com"}
  PASASTESINTAG_SMTP_HOST=smtp.gmail.com
  PASASTESINTAG_SMTP_PORT=587
  PASASTESINTAG_SMTP_USERNAME=tu_cuenta@gmail.com
  PASASTESINTAG_SMTP_PASSWORD=tu_app_password
  PASASTESINTAG_SMTP_FROM_EMAIL=tu_cuenta@gmail.com
  PASASTESINTAG_SMTP_USE_TLS=true
  PASASTESINTAG_ERROR_EMAILS=admin@example.com,soporte@example.com

Uso:
  python3 doc/script/pasastesintag_alerta_cron.py
  python3 doc/script/pasastesintag_alerta_cron.py --send-always
  python3 doc/script/pasastesintag_alerta_cron.py --mock-debt --send-always --debug
"""

from __future__ import annotations

import argparse
import html
import hashlib
import json
import logging
import os
import shlex
import smtplib
import subprocess
import sys
import traceback
from email.message import EmailMessage
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
CONSULTA_SCRIPT = BASE_DIR / "pasastesintag_consulta.py"
DEFAULT_STATE_FILE = BASE_DIR / "pasastesintag_alerta_state.json"
PASASTE_SIN_TAG_URL = "https://pasastesintag.cl/"
ENV_FILE_CANDIDATES = (
    BASE_DIR.parents[1] / ".env",
    BASE_DIR / ".env",
)

PLATE_EMAIL_MAP_ENV = "PASASTESINTAG_PLATE_EMAIL_MAP"
ERROR_EMAILS_ENV = "PASASTESINTAG_ERROR_EMAILS"
SMTP_ENV_KEYS = {
    "host": "PASASTESINTAG_SMTP_HOST",
    "port": "PASASTESINTAG_SMTP_PORT",
    "username": "PASASTESINTAG_SMTP_USERNAME",
    "password": "PASASTESINTAG_SMTP_PASSWORD",
    "from_email": "PASASTESINTAG_SMTP_FROM_EMAIL",
    "use_tls": "PASASTESINTAG_SMTP_USE_TLS",
}


class AlertaError(RuntimeError):
    """Error controlado del controlador de alertas."""


logger = logging.getLogger("pasastesintag_alerta_cron")


def load_env_files() -> None:
    for env_file in ENV_FILE_CANDIDATES:
        if not env_file.exists():
            continue
        logger.debug("Cargando variables desde %s", env_file)
        lines = env_file.read_text(encoding="utf-8").splitlines()
        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line.removeprefix("export ").strip()
            if "=" not in line:
                logger.debug("Linea .env ignorada sin '=' en %s:%s", env_file, line_number)
                continue
            key, raw_value = line.split("=", 1)
            key = key.strip()
            if not key:
                logger.debug("Linea .env ignorada con clave vacia en %s:%s", env_file, line_number)
                continue
            value = raw_value.strip()
            if (
                value
                and len(value) >= 2
                and value[0] == value[-1]
                and value[0] in {"'", '"'}
            ):
                try:
                    value = shlex.split(value, comments=False, posix=True)[0]
                except ValueError:
                    logger.debug(
                        "No se pudo interpretar comillas en %s:%s; se usa valor literal.",
                        env_file,
                        line_number,
                    )
            os.environ.setdefault(key, value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Controlador de alertas de deuda para pasastesintag.cl.")
    parser.add_argument(
        "--state-file",
        default=str(DEFAULT_STATE_FILE),
        help="Ruta del archivo JSON para recordar alertas ya enviadas.",
    )
    parser.add_argument(
        "--send-always",
        action="store_true",
        help="Envia correo en cada ejecucion si existe deuda, aunque no haya cambios.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activa logs detallados por stderr.",
    )
    parser.add_argument(
        "--mock-debt",
        action="store_true",
        help="Simula una respuesta con deuda sin consultar el sitio externo.",
    )
    return parser


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )


def canonical_plate(plate: str) -> str:
    return "".join(char for char in plate.upper() if char.isalnum())


def parse_bool_env(value: str, var_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on", "si", "s"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise AlertaError(f"Valor booleano invalido en {var_name}: {value!r}")


def parse_plate_email_map(value: str) -> dict[str, str]:
    raw_value = value.strip()
    if not raw_value:
        return {}

    if raw_value.startswith("{"):
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise AlertaError(f"{PLATE_EMAIL_MAP_ENV} contiene JSON invalido: {exc}") from exc
        if not isinstance(parsed, dict):
            raise AlertaError(f"{PLATE_EMAIL_MAP_ENV} debe ser un objeto JSON patente -> email.")
        return {
            canonical_plate(str(plate)): str(email).strip()
            for plate, email in parsed.items()
            if canonical_plate(str(plate)) and str(email).strip()
        }

    plate_email_map: dict[str, str] = {}
    for item in raw_value.split(","):
        pair = item.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise AlertaError(
                f"{PLATE_EMAIL_MAP_ENV} debe usar JSON o pares separados por coma: PATENTE=email."
            )
        plate, email = pair.split("=", 1)
        normalized_plate = canonical_plate(plate)
        normalized_email = email.strip()
        if normalized_plate and normalized_email:
            plate_email_map[normalized_plate] = normalized_email
    return plate_email_map


def get_plate_email_map() -> dict[str, str]:
    logger.debug("Validando configuracion de patentes desde %s.", PLATE_EMAIL_MAP_ENV)
    plate_email_map = parse_plate_email_map(os.getenv(PLATE_EMAIL_MAP_ENV, ""))
    if not plate_email_map:
        raise AlertaError(
            f"{PLATE_EMAIL_MAP_ENV} esta vacio. Configura al menos una patente y un email."
        )
    return plate_email_map


def parse_email_list(value: str) -> list[str]:
    emails: list[str] = []
    for item in value.split(","):
        email = item.strip()
        if email and email not in emails:
            emails.append(email)
    return emails


def get_error_recipients(plate_email_map: dict[str, str] | None = None) -> list[str]:
    configured_recipients = parse_email_list(os.getenv(ERROR_EMAILS_ENV, ""))
    if configured_recipients:
        return configured_recipients

    if plate_email_map:
        recipients: list[str] = []
        for email in plate_email_map.values():
            normalized_email = str(email).strip()
            if normalized_email and normalized_email not in recipients:
                recipients.append(normalized_email)
        if recipients:
            return recipients

    fallback_email = os.getenv(SMTP_ENV_KEYS["from_email"], "").strip()
    return [fallback_email] if fallback_email else []


def load_state(state_file: Path) -> dict[str, Any]:
    logger.debug("Cargando archivo de estado: %s", state_file)
    if not state_file.exists():
        logger.debug("El archivo de estado no existe, se parte con estado vacio.")
        return {}
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        logger.debug("Archivo de estado cargado correctamente.")
        return state
    except json.JSONDecodeError as exc:
        raise AlertaError(f"No se pudo leer el archivo de estado {state_file}: {exc}") from exc


def save_state(state_file: Path, state: dict[str, Any]) -> None:
    logger.debug("Guardando archivo de estado: %s", state_file)
    state_file.write_text(
        json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    logger.debug("Archivo de estado guardado correctamente.")


def run_consulta(plate: str) -> dict[str, Any]:
    logger.debug("Ejecutando script de consulta para patente %s", plate)
    process = subprocess.run(
        [sys.executable, str(CONSULTA_SCRIPT), plate],
        check=False,
        capture_output=True,
        text=True,
    )

    stdout = process.stdout.strip()
    if not stdout:
        raise AlertaError(f"La consulta para {plate} no devolvio salida JSON.")

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AlertaError(f"La consulta para {plate} devolvio JSON invalido: {exc}") from exc

    payload["_exit_code"] = process.returncode
    if process.stderr.strip():
        payload["_stderr"] = process.stderr.strip()
        logger.debug("La consulta devolvio stderr para %s: %s", plate, payload["_stderr"])
    logger.debug("Consulta terminada para %s con codigo %s", plate, process.returncode)
    return payload


def build_mock_debt_payload(plate: str) -> dict[str, Any]:
    logger.debug("Generando payload mock con deuda para patente %s", plate)
    return {
        "ok": True,
        "plate": plate,
        "response": {
            "status": True,
            "code": 200,
            "message": f"La patente {plate} registra deuda pendiente.",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2026-04-06",
            "data": [
                {
                    "concesionaria": "Autopista Central",
                    "patente": plate,
                    "monto": 12500,
                    "estado": "pendiente",
                    "fecha_transito": "2026-03-20",
                }
            ],
        },
        "_exit_code": 0,
        "_mock": True,
    }


def message_indicates_debt(message: str) -> bool:
    normalized = message.strip().lower()
    negative_patterns = (
        "no registra deuda",
        "no registra deudas",
        "sin deuda",
        "sin deudas",
        "no presenta deuda",
        "no presenta deudas",
        "no registra transitos",
        "no registra tránsitos",
    )
    if any(pattern in normalized for pattern in negative_patterns):
        return False

    positive_patterns = (
        "registra deuda",
        "registra deudas",
        "mantiene deuda",
        "deuda pendiente",
        "deudas pendientes",
    )
    return any(pattern in normalized for pattern in positive_patterns)


def detect_debt(payload: dict[str, Any]) -> bool:
    if not payload.get("ok"):
        return False

    response = payload.get("response")
    if not isinstance(response, dict):
        return False

    message = response.get("message")
    if isinstance(message, str) and message_indicates_debt(message):
        return True

    data = response.get("data")
    if isinstance(data, list):
        return len(data) > 0
    if isinstance(data, dict):
        return bool(data)

    return False


def debt_fingerprint(payload: dict[str, Any]) -> str:
    response = payload.get("response", {})
    canonical_json = json.dumps(response, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def get_smtp_config() -> dict[str, Any]:
    logger.debug("Validando configuracion SMTP desde variables de entorno.")
    required_keys = ("host", "port", "username", "password", "from_email")
    missing_keys = [
        key for key in required_keys if not os.getenv(SMTP_ENV_KEYS[key], "").strip()
    ]
    if missing_keys:
        missing = ", ".join(SMTP_ENV_KEYS[key] for key in missing_keys)
        raise AlertaError(f"Faltan variables SMTP en entorno/.env: {missing}")

    port_value = os.getenv(SMTP_ENV_KEYS["port"], "").strip()
    try:
        port = int(port_value)
    except ValueError as exc:
        raise AlertaError(
            f"{SMTP_ENV_KEYS['port']} debe ser un numero entero: {port_value!r}"
        ) from exc

    use_tls_value = os.getenv(SMTP_ENV_KEYS["use_tls"], "true")

    smtp = {
        "host": os.getenv(SMTP_ENV_KEYS["host"], "").strip(),
        "port": port,
        "username": os.getenv(SMTP_ENV_KEYS["username"], "").strip(),
        "password": os.getenv(SMTP_ENV_KEYS["password"], "").strip(),
        "from_email": os.getenv(SMTP_ENV_KEYS["from_email"], "").strip(),
        "use_tls": parse_bool_env(use_tls_value, SMTP_ENV_KEYS["use_tls"]),
    }
    logger.debug(
        "Configuracion SMTP validada: host=%s port=%s username=%s from_email=%s use_tls=%s",
        smtp["host"],
        smtp["port"],
        smtp["username"],
        smtp["from_email"],
        smtp["use_tls"],
    )
    return smtp


def flatten_json_to_kv_rows(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_json_to_kv_rows(item, new_prefix))
        return rows
    if isinstance(value, list):
        for index, item in enumerate(value):
            new_prefix = f"{prefix}[{index}]"
            rows.extend(flatten_json_to_kv_rows(item, new_prefix))
        if not value:
            rows.append((prefix, "[]"))
        return rows
    if value is None:
        rows.append((prefix, "null"))
        return rows
    if isinstance(value, bool):
        rows.append((prefix, "true" if value else "false"))
        return rows
    rows.append((prefix, str(value)))
    return rows


def render_kv_table(rows: list[tuple[str, str]]) -> str:
    body = "".join(
        (
            f"<tr><td style='padding:8px;border:1px solid #d9dee7;background:#f8fafc;"
            f"font-family:Arial,sans-serif;font-size:12px;color:#1f2937;vertical-align:top;"
            f"font-weight:600'>{html.escape(key)}</td>"
            f"<td style='padding:8px;border:1px solid #d9dee7;background:#ffffff;"
            f"font-family:Arial,sans-serif;font-size:12px;color:#111827;vertical-align:top;"
            f"white-space:pre-wrap'>{html.escape(value)}</td></tr>"
        )
        for key, value in rows
    )
    if not body:
        body = (
            "<tr><td colspan='2' style='padding:8px;border:1px solid #d9dee7;background:#ffffff;"
            "font-family:Arial,sans-serif;font-size:12px;color:#6b7280'>Sin datos</td></tr>"
        )
    return (
        "<table role='presentation' cellspacing='0' cellpadding='0' width='100%' "
        "style='border-collapse:collapse;border:1px solid #d9dee7'>"
        "<thead><tr>"
        "<th style='padding:10px;border:1px solid #d9dee7;background:#eaf0f8;"
        "text-align:left;font-family:Arial,sans-serif;font-size:12px;color:#1f2937'>Campo</th>"
        "<th style='padding:10px;border:1px solid #d9dee7;background:#eaf0f8;"
        "text-align:left;font-family:Arial,sans-serif;font-size:12px;color:#1f2937'>Valor</th>"
        "</tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def deliver_email(email: EmailMessage, smtp: dict[str, Any] | None = None) -> None:
    smtp = smtp or get_smtp_config()
    with smtplib.SMTP(smtp["host"], smtp["port"], timeout=30) as server:
        if smtp["use_tls"]:
            logger.debug("Iniciando TLS con servidor SMTP %s:%s", smtp["host"], smtp["port"])
            server.starttls()
        logger.debug("Autenticando en servidor SMTP como %s", smtp["username"])
        server.login(smtp["username"], smtp["password"])
        logger.debug("Enviando correo a %s", email["To"])
        server.send_message(email)


def send_email(
    recipient: str,
    plate: str,
    payload: dict[str, Any],
    _step_log: list[str],
    debt_detected: bool,
) -> None:
    smtp = get_smtp_config()
    logger.debug("Preparando correo para patente %s a destinatario %s", plate, recipient)

    response = payload.get("response", {})
    message = response.get("message", "Sin mensaje de respuesta del servicio.")
    status_label = "CON DEUDA" if debt_detected else "SIN DEUDA"
    status_color = "#b91c1c" if debt_detected else "#0f766e"
    payload_rows = flatten_json_to_kv_rows(payload)

    email = EmailMessage()
    email["Subject"] = f"[PasasteSinTag] Estado patente {plate}: {status_label}"
    email["From"] = smtp["from_email"]
    email["To"] = recipient
    email.set_content(
        "\n".join(
            [
                (
                    f"Se detecto deuda para la patente {plate}."
                    if debt_detected
                    else f"No se detecto deuda para la patente {plate}."
                ),
                "",
                f"Mensaje: {message}",
                "",
                "Verificacion manual:",
                PASASTE_SIN_TAG_URL,
                "",
                "JSON completo obtenido en la consulta:",
                json.dumps(payload, indent=2, ensure_ascii=False),
            ]
        )
    )
    email.add_alternative(
        f"""
<html>
  <body style="margin:0;padding:0;background:#f3f6fb;">
    <table role="presentation" cellspacing="0" cellpadding="0" width="100%" style="padding:24px 0;background:#f3f6fb;">
      <tr>
        <td align="center">
          <table role="presentation" cellspacing="0" cellpadding="0" width="760" style="width:760px;max-width:760px;background:#ffffff;border:1px solid #d9dee7;border-radius:8px;">
            <tr>
              <td style="padding:20px 24px;border-bottom:1px solid #d9dee7;">
                <h2 style="margin:0 0 8px 0;font-family:Arial,sans-serif;font-size:20px;color:#0f172a;">Reporte PasasteSinTag</h2>
                <p style="margin:0;font-family:Arial,sans-serif;font-size:14px;color:#334155;">
                  Patente: <strong>{html.escape(plate)}</strong> |
                  Estado: <strong style="color:{status_color};">{status_label}</strong>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 24px;">
                <p style="margin:0 0 12px 0;font-family:Arial,sans-serif;font-size:14px;color:#111827;">
                  {message}
                </p>
                <p style="margin:0 0 20px 0;font-family:Arial,sans-serif;font-size:14px;color:#111827;">
                  Verificacion manual:
                  <a href="{PASASTE_SIN_TAG_URL}" style="color:#1d4ed8;text-decoration:none;">{PASASTE_SIN_TAG_URL}</a>
                </p>

                {render_kv_table(payload_rows)}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""",
        subtype="html",
    )

    deliver_email(email, smtp=smtp)
    logger.debug("Correo enviado correctamente para patente %s", plate)


def send_error_email(
    recipients: list[str],
    title: str,
    details: dict[str, Any],
) -> None:
    if not recipients:
        raise AlertaError(
            f"No hay destinatarios para avisos de error. Define {ERROR_EMAILS_ENV} "
            f"o configura {PLATE_EMAIL_MAP_ENV}."
        )

    smtp = get_smtp_config()
    details_json = json.dumps(details, indent=2, ensure_ascii=False, sort_keys=True)
    email = EmailMessage()
    email["Subject"] = f"[PasasteSinTag] Error en ejecucion: {title}"
    email["From"] = smtp["from_email"]
    email["To"] = ", ".join(recipients)
    email.set_content(
        "\n".join(
            [
                "Se detecto un error durante la ejecucion del cron PasasteSinTag.",
                "",
                f"Error: {title}",
                "",
                "Detalle:",
                details_json,
            ]
        )
    )
    email.add_alternative(
        f"""
<html>
  <body style="margin:0;padding:0;background:#f3f6fb;">
    <table role="presentation" cellspacing="0" cellpadding="0" width="100%" style="padding:24px 0;background:#f3f6fb;">
      <tr>
        <td align="center">
          <table role="presentation" cellspacing="0" cellpadding="0" width="760" style="width:760px;max-width:760px;background:#ffffff;border:1px solid #d9dee7;border-radius:8px;">
            <tr>
              <td style="padding:20px 24px;border-bottom:1px solid #d9dee7;">
                <h2 style="margin:0;font-family:Arial,sans-serif;font-size:20px;color:#b91c1c;">Error PasasteSinTag</h2>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 24px;">
                <p style="margin:0 0 12px 0;font-family:Arial,sans-serif;font-size:14px;color:#111827;">
                  Se detecto un error durante la ejecucion del cron PasasteSinTag.
                </p>
                <p style="margin:0 0 20px 0;font-family:Arial,sans-serif;font-size:14px;color:#111827;">
                  <strong>Error:</strong> {html.escape(title)}
                </p>
                <pre style="white-space:pre-wrap;background:#f8fafc;border:1px solid #d9dee7;border-radius:6px;padding:12px;font-family:Consolas,monospace;font-size:12px;color:#111827;">{html.escape(details_json)}</pre>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""",
        subtype="html",
    )
    deliver_email(email, smtp=smtp)
    logger.debug("Correo de error enviado correctamente a %s", recipients)


def notify_execution_error(
    title: str,
    details: dict[str, Any],
    plate_email_map: dict[str, str] | None = None,
) -> str | None:
    try:
        recipients = get_error_recipients(plate_email_map)
        send_error_email(recipients, title, details)
        return None
    except Exception as exc:
        logger.exception("Fallo el envio del correo de error")
        return str(exc)


def build_result(
    plate: str,
    recipient: str,
    status: str,
    payload: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "plate": plate,
        "recipient": recipient,
        "status": status,
    }
    if payload is not None:
        result["query_ok"] = payload.get("ok", False)
        result["query_exit_code"] = payload.get("_exit_code")
        result["debt_detected"] = detect_debt(payload)
        result["response_message"] = payload.get("response", {}).get("message")
    if error is not None:
        result["error"] = error
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.debug)
    load_env_files()
    state_file = Path(args.state_file)
    logger.info(
        "Inicio de ejecucion. state_file=%s send_always=%s debug=%s mock_debt=%s",
        state_file,
        args.send_always,
        args.debug,
        args.mock_debt,
    )

    try:
        plate_email_map = get_plate_email_map()
        if not CONSULTA_SCRIPT.exists():
            logger.debug("No existe el script de consulta: %s", CONSULTA_SCRIPT)
            details = {
                "ok": False,
                "error": f"No existe el script de consulta: {CONSULTA_SCRIPT}",
                "script": str(CONSULTA_SCRIPT),
            }
            notification_error = notify_execution_error(
                "No existe el script de consulta",
                details,
                plate_email_map=plate_email_map,
            )
            if notification_error:
                details["error_notification_error"] = notification_error
            print(json.dumps(details, ensure_ascii=False))
            return 1

        state = load_state(state_file)
        results: list[dict[str, Any]] = []
        email_sent = 0
        debt_found = 0
        errors = 0

        for raw_plate, recipient in plate_email_map.items():
            logger.debug("Procesando configuracion patente=%s recipient=%s", raw_plate, recipient)
            plate = canonical_plate(raw_plate)
            plate_log = [
                f"patente_configurada={raw_plate}",
                f"patente_normalizada={plate}",
                f"destinatario={recipient}",
                f"mock_debt={args.mock_debt}",
                f"send_always={args.send_always}",
            ]
            if not plate:
                logger.debug("Patente invalida luego de normalizar: %s", raw_plate)
                errors += 1
                plate_log.append("estado=invalid_plate")
                results.append(
                    build_result(
                        plate=raw_plate,
                        recipient=recipient,
                        status="invalid_plate",
                        error="La patente configurada es invalida.",
                    )
                )
                continue

            try:
                payload = build_mock_debt_payload(plate) if args.mock_debt else run_consulta(plate)
                plate_log.append(f"consulta_exit_code={payload.get('_exit_code')}")
                plate_log.append(f"consulta_ok={payload.get('ok')}")
            except Exception as exc:
                logger.exception("Fallo la consulta para %s", plate)
                errors += 1
                plate_log.append(f"estado=query_error excepcion={exc}")
                results.append(
                    build_result(
                        plate=plate,
                        recipient=recipient,
                        status="query_error",
                        error=str(exc),
                    )
                )
                continue

            if not payload.get("ok"):
                logger.debug("La consulta para %s devolvio error de aplicacion: %s", plate, payload)
                errors += 1
                plate_log.append(f"estado=query_error message={payload.get('message')}")
                results.append(
                    build_result(
                        plate=plate,
                        recipient=recipient,
                        status="query_error",
                        payload=payload,
                        error=payload.get("message", "La consulta devolvio ok=false."),
                    )
                )
                continue

            has_debt = detect_debt(payload)
            logger.debug("Resultado consulta patente=%s has_debt=%s", plate, has_debt)
            plate_log.append(f"debt_detected={has_debt}")
            if not has_debt:
                logger.debug("No se detecta deuda para %s. Se limpia estado previo si existe.", plate)
                state.pop(plate, None)
                plate_log.append("estado=no_debt")
                if args.send_always:
                    plate_log.append("accion=send_email_por_send_always")
                    try:
                        send_email(recipient, plate, payload, plate_log, debt_detected=False)
                    except Exception as exc:
                        logger.exception("Fallo el envio de correo (sin deuda) para %s", plate)
                        errors += 1
                        plate_log.append(f"estado=email_error error={exc}")
                        results.append(
                            build_result(
                                plate=plate,
                                recipient=recipient,
                                status="email_error",
                                payload=payload,
                                error=str(exc),
                            )
                        )
                        continue
                    email_sent += 1
                    plate_log.append("estado=no_debt_report_sent")
                    results.append(build_result(plate, recipient, "no_debt_report_sent", payload=payload))
                    continue
                results.append(build_result(plate, recipient, "no_debt", payload=payload))
                continue

            debt_found += 1
            fingerprint = debt_fingerprint(payload)
            previous_fingerprint = state.get(plate, {}).get("fingerprint")
            should_send = args.send_always or previous_fingerprint != fingerprint
            plate_log.append(f"fingerprint={fingerprint}")
            plate_log.append(f"previous_fingerprint={previous_fingerprint}")
            plate_log.append(f"should_send={should_send}")
            logger.debug(
                "Deuda detectada para %s. previous_fingerprint=%s should_send=%s",
                plate,
                previous_fingerprint,
                should_send,
            )

            if should_send:
                try:
                    plate_log.append("accion=send_email")
                    send_email(recipient, plate, payload, plate_log, debt_detected=True)
                except Exception as exc:
                    logger.exception("Fallo el envio de correo para %s", plate)
                    errors += 1
                    plate_log.append(f"estado=email_error error={exc}")
                    results.append(
                        build_result(
                            plate=plate,
                            recipient=recipient,
                            status="email_error",
                            payload=payload,
                            error=str(exc),
                        )
                    )
                    continue

                email_sent += 1
                state[plate] = {
                    "fingerprint": fingerprint,
                    "recipient": recipient,
                }
                logger.debug("Se actualiza estado para %s luego del envio.", plate)
                plate_log.append("estado=alert_sent")
                results.append(build_result(plate, recipient, "alert_sent", payload=payload))
                continue

            logger.debug("No se envia correo para %s porque la deuda no cambio.", plate)
            plate_log.append("estado=debt_unchanged")
            results.append(build_result(plate, recipient, "debt_unchanged", payload=payload))

        save_state(state_file, state)
        summary = {
            "ok": errors == 0,
            "checked": len(plate_email_map),
            "debt_found": debt_found,
            "email_sent": email_sent,
            "errors": errors,
            "results": results,
        }
        if errors:
            notification_error = notify_execution_error(
                "Errores durante la ejecucion",
                summary,
                plate_email_map=plate_email_map,
            )
            if notification_error:
                summary["error_notification_error"] = notification_error
        logger.info(
            "Ejecucion finalizada. checked=%s debt_found=%s email_sent=%s errors=%s",
            summary["checked"],
            summary["debt_found"],
            summary["email_sent"],
            summary["errors"],
        )
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if errors == 0 else 1
    except AlertaError as exc:
        logger.exception("Error controlado en el controlador de alertas")
        details = {"ok": False, "error": str(exc)}
        notification_error = notify_execution_error("Error controlado", details)
        if notification_error:
            details["error_notification_error"] = notification_error
        print(json.dumps(details, ensure_ascii=False))
        return 1
    except Exception as exc:
        logger.exception("Error no controlado en el controlador de alertas")
        details = {
            "ok": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        notification_error = notify_execution_error("Error no controlado", details)
        if notification_error:
            details["error_notification_error"] = notification_error
        print(json.dumps(details, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
