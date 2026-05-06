#!/usr/bin/env python3
"""Helper de login automatico para Banco de Chile usando Playwright.

Disenado para reutilizarse desde otros scripts y dejar sesion iniciada.
Credenciales por variables de entorno:
  BANCHILE_RUT
  BANCHILE_PASSWORD
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import time

from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Error as PlaywrightError
from playwright.sync_api import Page, Playwright, sync_playwright


PUBLIC_URL = "https://sitiospublicos.bancochile.cl/personas"
PORTAL_HOME_URL = "https://portalpersonas.bancochile.cl/mibancochile-web/front/persona/index.html#/home"

DEFAULT_SESSION_DIR = Path(__file__).resolve().parent / ".session"
DEFAULT_STORAGE_STATE = Path(__file__).resolve().parent / ".session" / "storage_state.json"


class BancoChileLoginError(RuntimeError):
    """Error controlado del flujo de login."""


@dataclass
class Credentials:
    rut: str
    password: str


def load_credentials_from_env() -> Credentials:
    # Cargar archivo .env desde la carpeta del script
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)

    rut = os.getenv("BANCHILE_RUT", "").strip()
    password = os.getenv("BANCHILE_PASSWORD", "").strip()

    if not rut or not password:
        raise BancoChileLoginError(
            "Faltan credenciales en entorno. Define BANCHILE_RUT y BANCHILE_PASSWORD."
        )
    return Credentials(rut=rut, password=password)


def open_context(
    playwright: Playwright,
    session_dir: Path,
    headless: bool,
    browser: str = "auto",
    downloads_path: Optional[Path] = None,
) -> BrowserContext:
    session_dir.mkdir(parents=True, exist_ok=True)
    base_kwargs = {
        "user_data_dir": str(session_dir),
        "headless": headless,
        "viewport": {"width": 1440, "height": 900},
        "accept_downloads": True,
    }
    if downloads_path:
        downloads_path.mkdir(parents=True, exist_ok=True)
        base_kwargs["downloads_path"] = str(downloads_path)

    def launch_chromium() -> BrowserContext:
        kwargs = dict(base_kwargs)
        kwargs["args"] = [
            "--disable-crash-reporter",
            "--disable-crashpad",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
        return playwright.chromium.launch_persistent_context(**kwargs)

    def launch_firefox() -> BrowserContext:
        kwargs = dict(base_kwargs)
        # Firefox no soporta args del mismo modo que chromium.
        kwargs.pop("downloads_path", None)
        return playwright.firefox.launch_persistent_context(**kwargs)

    order: list[str]
    if browser == "auto":
        order = ["chromium", "firefox"]
    else:
        order = [browser]

    last_error: Optional[Exception] = None
    for candidate in order:
        try:
            if candidate == "chromium":
                return launch_chromium()
            if candidate == "firefox":
                return launch_firefox()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    raise BancoChileLoginError(f"No se pudo abrir navegador ({browser}): {last_error}")


def _is_login_page(page: Page) -> bool:
    url = page.url.lower()
    if "login.portales.bancochile.cl" in url or "/login" in url:
        return True
    try:
        title = page.title().lower()
    except PlaywrightError:
        title = ""
    return "inicia sesión" in title or "inicia sesion" in title


def _looks_like_anti_bot(page: Page) -> bool:
    try:
        content = page.content().lower()
    except PlaywrightError:
        return False
    markers = [
        "liest-prested-the-comes-gread-then-be-my-spirity",
        "mes-is-their-sely-doct-grangely-in-meet-awayward",
        "headlesschrome",
    ]
    return any(m in content for m in markers)


def is_logged_in(page: Page) -> bool:
    try:
        url = page.url.lower()
        if _is_login_page(page):
            return False
        if "portalpersonas.bancochile.cl" not in url:
            return False
        home_markers = [
            "text=Mis Productos",
            "text=Saldos y Movimientos",
            "text=Mi Banco",
        ]
        for marker in home_markers:
            if page.locator(marker).first.is_visible(timeout=1200):
                return True
        # A veces la home carga sin todos los textos inmediatamente.
        if "#/home" in url or "/mibancochile-web/front/persona/index.html" in url:
            return True
        return False
    except PlaywrightError:
        return False


def perform_login(page: Page, creds: Credentials, timeout_ms: int = 45_000) -> None:
    page.goto(PUBLIC_URL, wait_until="domcontentloaded")
    page.get_by_role("link", name="Banco en Línea").click()
    page.get_by_role("textbox", name="RUT RUT").fill(creds.rut)
    password_input = page.get_by_role("textbox", name="Contraseña Contraseña")
    password_input.fill(creds.password)

    clicked = False
    button_candidates = [
        page.get_by_role("button", name="Ingresar a cuenta"),
        page.get_by_role("button", name="Ingresar"),
        page.get_by_text("Ingresar", exact=True),
        page.locator("button[type='submit']"),
        page.locator("input[type='submit']"),
    ]
    for candidate in button_candidates:
        try:
            candidate.first.click(timeout=2000)
            clicked = True
            break
        except PlaywrightError:
            continue

    if not clicked:
        # Fallback por si el boton cambia de estructura.
        password_input.press("Enter")

    # Espera redireccion al portal privado.
    page.wait_for_url("**portalpersonas.bancochile.cl/**", timeout=timeout_ms)
    page.goto(PORTAL_HOME_URL, wait_until="domcontentloaded")


def ensure_logged_in_page(
    context: BrowserContext,
    creds: Credentials,
    timeout_ms: int = 45_000,
    allow_headless_login: bool = False,
    check_antibot: bool = True,
) -> Page:
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(PUBLIC_URL, wait_until="domcontentloaded")
    if check_antibot and _looks_like_anti_bot(page) and not allow_headless_login:
        raise BancoChileLoginError(
            "Se detectó respuesta anti-automatización en página pública. "
            "Haz login inicial con UI (sin --headless) o prueba --allow-headless-login."
        )

    if not is_logged_in(page):
        perform_login(page, creds=creds, timeout_ms=timeout_ms)
    if not is_logged_in(page):
        raise BancoChileLoginError(
            "No se pudo confirmar sesión autenticada en portalpersonas después del login."
        )
    return page


def wait_for_logged_in(page: Page, timeout_seconds: int = 180) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_logged_in(page):
            return True
        page.wait_for_timeout(800)
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inicia sesion automatica en Banco de Chile.")
    parser.add_argument("--headless", action="store_true", help="Ejecutar sin UI.")
    parser.add_argument(
        "--browser",
        choices=["auto", "chromium", "firefox"],
        default="auto",
        help="Navegador a usar. auto prueba chromium y luego firefox.",
    )
    parser.add_argument(
        "--allow-headless-login",
        action="store_true",
        help="Permite intentar login completo en headless (puede fallar por anti-bot/MFA).",
    )
    parser.add_argument(
        "--session-dir",
        default=str(DEFAULT_SESSION_DIR),
        help="Directorio de perfil persistente del navegador.",
    )
    parser.add_argument(
        "--storage-state-out",
        default=str(DEFAULT_STORAGE_STATE),
        help="Ruta donde guardar storage state reutilizable para otros scripts.",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Mantiene el navegador abierto para inspeccion manual.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    session_dir = Path(args.session_dir).resolve()
    storage_state_out = Path(args.storage_state_out).resolve()

    try:
        creds = load_credentials_from_env()
        with sync_playwright() as pw:
            context = open_context(
                playwright=pw,
                session_dir=session_dir,
                headless=args.headless,
                browser=args.browser,
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(PUBLIC_URL, wait_until="domcontentloaded")

            if args.headless and not is_logged_in(page) and not args.allow_headless_login:
                raise BancoChileLoginError(
                    "No hay sesión activa para reutilizar en headless. "
                    "Ejecuta primero sin --headless para iniciar sesión una vez, "
                    "o usa --allow-headless-login bajo tu responsabilidad."
                )

            page = ensure_logged_in_page(
                context,
                creds=creds,
                allow_headless_login=args.allow_headless_login,
                check_antibot=args.headless,
            )
            storage_state_out.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(storage_state_out))
            print(f"[OK] Sesion iniciada. URL actual: {page.url}", file=sys.stderr)
            print(f"[OK] Storage state guardado en: {storage_state_out}", file=sys.stderr)

            if args.keep_open:
                print("[INFO] Browser abierto. Presiona Ctrl+C para salir.", file=sys.stderr)
                try:
                    page.wait_for_timeout(24 * 60 * 60 * 1000)
                except KeyboardInterrupt:
                    pass

            context.close()
        return 0
    except BancoChileLoginError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Fallo inesperado: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
