import argparse, datetime as dt, json, secrets, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from santander_server_core import ROOT, Store, BankError, Busy, TZ, months, update


def make_server(port=8031, store=None):
    if port == 8030:
        raise BankError("Puerto 8030 reservado; configure SANTANDER_PORT")
    store = store or Store()
    token = secrets.token_urlsafe(32)
    state = {"state": "preparando", "active": False}
    guard = threading.Lock()
    allowed = {
        "/": ("index.html", "text/html"),
        "/app.js": ("app.js", "text/javascript"),
        "/styles.css": ("styles.css", "text/css"),
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, body, kind="application/json"):
            if kind == "application/json":
                body = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; object-src 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def valid_host(self):
            return self.headers.get("Host") in (
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            )

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, {"error": "Host denegado"})
            if self.path == "/api/data":
                return self.send(200, store.public_projection())
            if self.path == "/api/status":
                with guard:
                    result = dict(state, token=token)
                return self.send(200, result)
            if self.path not in allowed:
                return self.send(404, {"error": "Ruta no disponible"})
            name, kind = allowed[self.path]
            self.send(200, (ROOT / "web" / name).read_bytes(), kind)

        def do_POST(self):
            if self.path != "/api/update":
                return self.send(404, {"error": "Ruta no disponible"})
            if (
                not self.valid_host()
                or self.headers.get("Origin")
                not in (
                    f"http://localhost:{self.server.server_port}",
                    f"http://127.0.0.1:{self.server.server_port}",
                )
                or not secrets.compare_digest(
                    self.headers.get("X-Instance-Token", ""), token
                )
            ):
                return self.send(403, {"error": "Origen o token denegado"})
            with guard:
                if state["active"]:
                    return self.send(409, {"error": "Otra actualización está activa"})
                try:
                    with store.writer():
                        pass
                except Busy:
                    return self.send(409, {"error": "Otra actualización está activa"})
                state.update(active=True, state="preparando", error=None)

            def progress(value):
                with guard:
                    state["state"] = value

            def job():
                try:
                    stored = store.projection()["partitions"]
                    latest = max(
                        (p["month"] for p in stored if p["movements"]), default=None
                    )
                    update(
                        store,
                        months(desde=latest),
                        interactive=True,
                        force=True,
                        progress=progress,
                    )
                except BankError as error:
                    with guard:
                        state.update(state="error", error=str(error))
                except Exception:
                    with guard:
                        state.update(
                            state="error",
                            error="Actualización fallida; revise configuración",
                        )
                finally:
                    with guard:
                        state["active"] = False

            threading.Thread(target=job, daemon=True).start()
            self.send(202, {"state": "preparando"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8031)
    args = parser.parse_args()
    try:
        make_server(args.port).serve_forever()
    except (BankError, OSError):
        raise SystemExit(
            "No se pudo iniciar Santander; compruebe puerto y configuración"
        )
