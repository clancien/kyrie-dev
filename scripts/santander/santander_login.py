"""Visible parent/iframe login; capture and validate real requests per host."""

import os, time
from urllib.parse import urlsplit
from santander_server_core import (
    ROOT,
    PRODUCTS,
    BALANCES,
    CARDS,
    Adapter,
    BankError,
    SessionExpired,
    atomic_json,
    private_dir,
)


def login(expected_holder=None):
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    load_dotenv(ROOT / ".env")
    rut = os.getenv("SANTANDER_RUT", "").strip()
    password = os.getenv("SANTANDER_PASSWORD", "")
    if not rut or not password:
        raise BankError("Configure SANTANDER_RUT y SANTANDER_PASSWORD en .env")
    if len(password) > 10:
        raise BankError("Clave configurada supera maxlength=10; no se truncó")
    private_dir(ROOT / ".cache")
    private_dir(ROOT / ".cache/browser")
    captured = dict(holder=rut, hosts={}, probes={})
    with sync_playwright() as playwright:
        try:
            context = playwright.chromium.launch_persistent_context(
                str(ROOT / ".cache/browser"), headless=False
            )
        except Exception:
            raise BankError(
                "Se requiere escritorio visible; renueve con run.sh en entorno gráfico"
            ) from None

        def response_seen(response):
            url = next(
                (
                    url
                    for url in (PRODUCTS, BALANCES, CARDS)
                    if response.url.split("?")[0] == url
                ),
                None,
            )
            if not url or response.request.method != "POST" or response.status != 200:
                return
            request = response.request
            host = urlsplit(url).hostname
            try:
                body = request.post_data_json
                data = response.json()
                headers = request.all_headers()
            except Exception:
                return
            captured["hosts"][host] = {
                k: v
                for k, v in headers.items()
                if k.lower()
                not in (
                    "host",
                    "content-length",
                    "connection",
                    "cookie",
                    "accept-encoding",
                )
                and not k.startswith(":")
            }
            if url in (PRODUCTS, BALANCES):
                captured["probes"][host] = dict(url=url, body=body)
            if url == CARDS:
                captured["card_template"] = body
            atomic_json(
                ROOT / ".cache" / ("capture-" + url.split("/")[-1] + ".json"), data
            )

        context.on("response", response_seen)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto(
                "https://banco.santander.cl/personas", wait_until="domcontentloaded"
            )
            page.get_by_role(
                "button", name="Ingresar al sitio privado", exact=True
            ).click()
            frame = page.frame_locator("iframe#login-frame")
            frame.locator("input#rut").fill(rut)
            frame.locator("input#pass").fill(password)
            frame.get_by_text("Ingresar", exact=True).first.click()
            deadline = time.monotonic() + 180
            private = None
            while time.monotonic() < deadline:
                page.wait_for_timeout(1000)
                private = next(
                    (
                        frame
                        for tab in context.pages
                        for frame in tab.frames
                        if "/private/" in frame.url and "santander.cl" in frame.url
                    ),
                    None,
                )
                if private and "api-dsk.santander.cl" in captured["probes"]:
                    break
            if not private:
                raise SessionExpired(
                    "Acceso pendiente o rechazado; complete desafíos manualmente y vuelva a ejecutar run.sh"
                )
            # Read-only screens trigger legitimate requests in their original browser context.
            for route in (
                "/private/saldos/main/mi-cuenta",
                "/private/Saldos_TC/main/bill",
            ):
                private.evaluate("(route)=>location.hash=route", route)
                page.wait_for_timeout(6000)
                private = next(
                    (
                        frame
                        for tab in context.pages
                        for frame in tab.frames
                        if "/private/" in frame.url and "santander.cl" in frame.url
                    ),
                    private,
                )
            captured["cookies"] = context.cookies()
            Adapter(captured).validate(expected_holder)
            context.storage_state(path=str(ROOT / ".cache/browser-state.json"))
            os.chmod(ROOT / ".cache/browser-state.json", 0o600)
            atomic_json(ROOT / ".cache/session.json", captured)
            return captured
        except BankError:
            raise
        except Exception:
            raise SessionExpired(
                "Acceso pendiente o rechazado; complete desafíos manualmente; vuelva a ejecutar run.sh"
            ) from None
        finally:
            context.close()
