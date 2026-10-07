import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bancochile_web_server as web
from bancochile_server_core import ServerApiError


class WebUpdateTests(unittest.TestCase):
    def test_latest_nonempty_month(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "cartola.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE cartola_months (month TEXT, pages_json TEXT)")
                connection.executemany("INSERT INTO cartola_months VALUES (?, ?)", [
                    ("2025-12", json.dumps([{"response": {"movimientos": [{"id": 1}]}}])),
                    ("2026-01", json.dumps([{"response": {"movimientos": []}}])),
                ])
            self.assertEqual(web.latest_month_with_data(database), "2025-12")

    def test_login_completes_before_download_and_result(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "movimientos_server_latest.json").write_text(json.dumps({
                "movimientos_total": 5, "movimientos_by_account": [{"account": {}}],
            }))
            with patch.object(web, "latest_month_with_data", return_value="2026-01"), \
                 patch.object(web, "load_storage_state_cookies", side_effect=ServerApiError("Sin sesión")), \
                 patch.object(web, "run_script") as run, \
                 patch.object(web, "DEFAULT_OUTPUT_DIR", output):
                web.update_data()
                self.assertEqual([call.args[0] for call in run.call_args_list], ["bancochile_login_ui.py", "bancochile_server_api.py"])
                self.assertIn("--actualizar-desde", run.call_args_list[1].args[1])
                self.assertEqual(web.STATE["status"], "done")
                self.assertEqual(web.STATE["result"]["movimientos_total"], 5)

    def test_failed_login_never_downloads(self):
        with patch.object(web, "latest_month_with_data", return_value="2026-01"), \
             patch.object(web, "load_storage_state_cookies", side_effect=ServerApiError("Sin sesión")), \
             patch.object(web, "run_script", side_effect=RuntimeError("Falló el acceso")) as run:
            web.update_data()
            self.assertEqual(run.call_count, 1)
            self.assertEqual(web.STATE["status"], "error")


if __name__ == "__main__":
    unittest.main()
