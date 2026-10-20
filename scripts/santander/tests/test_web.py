import json, sys, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from santander_server_core import Store
from santander_web_server import make_server


class WebTests(unittest.TestCase):
    def test_allowlist(self):
        with tempfile.TemporaryDirectory() as path:
            server = make_server(0, Store(Path(path) / "db"))
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for route in (
                    "/.env",
                    "/.cache/session.json",
                    "/../data/history.sqlite",
                    "/%2e%2e/.env",
                ):
                    request = urllib.request.Request(
                        f"http://127.0.0.1:{port}" + route,
                        headers={"Host": f"localhost:{port}"},
                    )
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(request)
                    self.assertEqual(error.exception.code, 404)
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/update",
                    method="POST",
                    headers={"Host": f"localhost:{port}", "Origin": "http://evil.test"},
                )
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(request)
                self.assertEqual(error.exception.code, 403)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


from unittest.mock import patch


class UpdateWebTests(unittest.TestCase):
    def test_update_background_and_writer_rejection(self):
        import time

        with tempfile.TemporaryDirectory() as path:
            store = Store(Path(path) / "db")
            server = make_server(0, store)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            entered = threading.Event()
            release = threading.Event()

            def get(route):
                with urllib.request.urlopen(
                    urllib.request.Request(
                        f"http://127.0.0.1:{port}" + route,
                        headers={"Host": f"localhost:{port}"},
                    )
                ) as r:
                    return json.load(r)

            def post(token):
                return urllib.request.urlopen(
                    urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/update",
                        method="POST",
                        headers={
                            "Host": f"localhost:{port}",
                            "Origin": f"http://localhost:{port}",
                            "X-Instance-Token": token,
                        },
                    )
                )

            def update(*args, **kwargs):
                entered.set()
                release.wait(3)
                kwargs["progress"]("completado")

            try:
                token = get("/api/status")["token"]
                with store.writer():
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        post(token)
                    self.assertEqual(error.exception.code, 409)
                with patch("santander_web_server.update", update):
                    with post(token) as r:
                        self.assertEqual(r.status, 202)
                    self.assertTrue(entered.wait(1))
                    self.assertTrue(get("/api/status")["active"])
                    self.assertIn("products", get("/api/data"))
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        post(token)
                    self.assertEqual(error.exception.code, 409)
                    release.set()
                    for _ in range(30):
                        if not get("/api/status")["active"]:
                            break
                        time.sleep(0.01)
                    self.assertEqual(get("/api/status")["state"], "completado")
            finally:
                release.set()
                server.shutdown()
                server.server_close()
                thread.join()
