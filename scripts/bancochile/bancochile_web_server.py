#!/usr/bin/env python3
"""Panel local y actualización de cartola en segundo plano."""

import argparse
import json
import secrets
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from bancochile_server_core import (
    BASE_DIR, DEFAULT_DATABASE, DEFAULT_CACHE_DIR, DEFAULT_OUTPUT_DIR, ZoneInfo,
    SELECTOR_PRODUCTOS_ENDPOINT, ServerApiError, build_session, call_get,
    extract_movements, load_storage_state_cookies, resolve_months,
)

TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()
STATE = {"status": "idle", "message": ""}


def set_state(**fields):
    with LOCK:
        STATE.update(fields)


def latest_month_with_data(database=DEFAULT_DATABASE):
    if not database.exists():
        return resolve_months()[0]["month"]
    connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    try:
        for month, pages_json in connection.execute("SELECT month, pages_json FROM cartola_months ORDER BY month DESC"):
            if any(extract_movements(page["response"]) for page in json.loads(pages_json)):
                return month
    finally:
        connection.close()
    return resolve_months()[0]["month"]


def run_script(name, arguments, timeout):
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / name), *arguments], cwd=BASE_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=timeout,
    )
    if result.returncode:
        # No exponer respuestas bancarias ni credenciales en la web.
        raise RuntimeError(f"Falló {name}. Revisa la sesión y vuelve a intentar.")


def update_data():
    try:
        desde = latest_month_with_data()
        hasta = datetime.now(ZoneInfo("America/Santiago")).strftime("%Y-%m")
        resolve_months(desde, hasta)
        set_state(message="Comprobando la sesión…", desde=desde, hasta=hasta)
        valid_session = False
        try:
            session = build_session(load_storage_state_cookies(DEFAULT_CACHE_DIR))
            try:
                call_get(session, SELECTOR_PRODUCTOS_ENDPOINT + "?incluirTarjetas=false")
                valid_session = True
            finally:
                session.close()
        except ServerApiError:
            pass
        if not valid_session:
            set_state(message="Iniciando sesión en el navegador. Esperando que termine el acceso…")
            run_script("bancochile_login_ui.py", ["--browser", "chromium", "--storage-state-out", str(DEFAULT_CACHE_DIR / "session_storage_state.json")], 240)
        set_state(message=f"Descargando todas las páginas desde {desde} hasta {hasta}…")
        run_script("bancochile_server_api.py", ["--desde", desde, "--hasta", hasta, "--actualizar-desde", desde], 3600)
        payload = json.loads((DEFAULT_OUTPUT_DIR / "movimientos_server_latest.json").read_text())
        set_state(status="done", message=f"Actualización completada: {desde} a {hasta}. {payload['movimientos_total']} movimientos acumulados en {len(payload['movimientos_by_account'])} cuentas.", result={
            "desde": desde, "hasta": hasta, "movimientos_total": payload["movimientos_total"],
            "accounts_count": len(payload["movimientos_by_account"]),
        })
    except subprocess.TimeoutExpired:
        set_state(status="error", message="La actualización excedió el tiempo de espera. Vuelve a intentarlo; los meses completos ya guardados se conservan.")
    except Exception as error:
        message = str(error) if isinstance(error, (RuntimeError, ServerApiError)) else "No se pudo actualizar. Comprueba conexión, sesión y configuración del servidor."
        set_state(status="error", message=message)


class Handler(SimpleHTTPRequestHandler):
    def allowed_host(self):
        return urlsplit("http://" + self.headers.get("Host", "")).hostname in {"localhost", "127.0.0.1", "bancochile.local"}

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed_host():
            self.send_error(403)
            return
        if urlsplit(self.path).path == "/api/update":
            with LOCK:
                state = dict(STATE)
            self.send_json(200, {**state, "token": TOKEN})
            return
        super().do_GET()

    def do_POST(self):
        origin = urlsplit(self.headers.get("Origin", ""))
        if not self.allowed_host() or origin.netloc != self.headers.get("Host") or self.headers.get("X-Update-Token") != TOKEN:
            self.send_json(403, {"message": "Solicitud no permitida."})
            return
        if urlsplit(self.path).path != "/api/update":
            self.send_error(404)
            return
        with LOCK:
            if STATE["status"] == "running":
                self.send_json(409, {"message": "Ya hay una actualización en curso."})
                return
            STATE.clear()
            STATE.update(status="running", message="Preparando actualización…")
        threading.Thread(target=update_data, daemon=True).start()
        self.send_json(202, {"status": "running"})

    def translate_path(self, path):
        route = urlsplit(path).path
        files = {"/": BASE_DIR / "web/index.html", "/index.html": BASE_DIR / "web/index.html",
                 "/app.js": BASE_DIR / "web/app.js", "/styles.css": BASE_DIR / "web/styles.css",
                 "/assets/banco-chile.svg": BASE_DIR / "web/assets/banco-chile.svg"}
        for name in ("selector_productos", "saldos", "tarjetas", "movimientos", "movimientos_api"):
            files[f"/data/{name}_server_latest.json"] = DEFAULT_OUTPUT_DIR / f"{name}_server_latest.json"
        return str(files.get(route, BASE_DIR / "web/__not_found__"))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8030)
    args = parser.parse_args()
    load_dotenv(BASE_DIR / ".env")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Panel Banco Chile en http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
