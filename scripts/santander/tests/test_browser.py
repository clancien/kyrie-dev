"""Panel smoke test with synthetic data; never contacts a banking host."""

import datetime as dt
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from santander_server_core import BankError, Store, TZ
from santander_web_server import make_server


class BrowserTests(unittest.TestCase):
    def test_filters_currencies_failure_and_mobile(self):
        with tempfile.TemporaryDirectory() as path:
            store = Store(Path(path) / "history.sqlite")
            rows = [
                dict(
                    accounting_date="2026-10-01",
                    transaction_date="2026-09-30",
                    time="0930",
                    description="Compra",
                    kind="cargo",
                    amount="0.10",
                    balance="1.00",
                    currency="USD",
                ),
                dict(
                    accounting_date="2026-10-02",
                    transaction_date="2026-10-02",
                    time=None,
                    description="Compra",
                    kind="cargo",
                    amount="0.20",
                    balance=None,
                    currency="USD",
                ),
            ]
            store.products(
                [
                    dict(
                        id="account",
                        type="vista",
                        label="Cuenta de prueba",
                        mask="••••0001",
                        lines=[
                            dict(currency="USD", available="0", used=None, limit=None)
                        ],
                    ),
                    dict(
                        id="card",
                        type="tarjeta",
                        label="Tarjeta de prueba",
                        mask="••••0002",
                        lines=[
                            dict(
                                currency="CLP",
                                movements=[
                                    dict(
                                        rows[0],
                                        currency="CLP",
                                        amount="100",
                                        merchant="Tienda",
                                    )
                                ],
                            ),
                            dict(
                                currency="USD",
                                movements=[dict(rows[1], merchant="Tienda")],
                            ),
                        ],
                    ),
                ],
                "synthetic-holder",
            )
            store.commit_month(
                "synthetic-holder",
                "account",
                "USD",
                "2026-10",
                rows,
                dt.datetime(2026, 10, 14, tzinfo=TZ),
            )
            server = make_server(0, store)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    page = browser.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(f"http://127.0.0.1:{server.server_port}")
                    page.locator("#products button").first.click()
                    expect(page.locator("#rows tr")).to_have_count(2)
                    self.assertIn("0,30", page.locator("#summary").inner_text())
                    page.locator("#search").fill("sin-coincidencia")
                    self.assertEqual(
                        page.locator("#empty").inner_text(), "Filtros sin coincidencias"
                    )
                    page.locator("#clear").click()
                    page.locator("#kind").select_option("abono")
                    self.assertEqual(page.locator("#rows tr").count(), 0)
                    page.locator("#clear").click()
                    with patch(
                        "santander_web_server.update",
                        side_effect=BankError("Fallo sintético"),
                    ):
                        page.locator("#update").click()
                        expect(page.locator("#status")).to_contain_text(
                            "Fallo sintético"
                        )
                    self.assertEqual(page.locator("#rows tr").count(), 2)
                    self.assertEqual(
                        page.locator("button[aria-pressed=true]").count(), 1
                    )
                    page.locator("#products button").nth(1).click()
                    self.assertIn("por facturar", page.locator("#scope").inner_text())
                    self.assertIn("CLP:", page.locator("#summary").inner_text())
                    self.assertIn("USD:", page.locator("#summary").inner_text())
                    self.assertNotIn("Saldo", page.locator("#columns").inner_text())
                    page.set_viewport_size({"width": 390, "height": 844})
                    self.assertLessEqual(
                        page.locator("main").bounding_box()["width"], 390
                    )
                    self.assertEqual(errors, [])
                    browser.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
