#!/usr/bin/env python3
"""Version alternativa de login que requiere UI (headful)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from bancochile_login import DEFAULT_SESSION_DIR, DEFAULT_STORAGE_STATE, ensure_logged_in_page, load_credentials_from_env, open_context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Login UI obligatorio para Banco de Chile.")
    parser.add_argument(
        "--browser",
        choices=["auto", "chromium", "firefox"],
        default="auto",
        help="Navegador a usar. auto prueba chromium y luego firefox.",
    )
    parser.add_argument(
        "--session-dir",
        default=str(DEFAULT_SESSION_DIR),
        help="Directorio de perfil persistente del navegador.",
    )
    parser.add_argument(
        "--storage-state-out",
        default=str(DEFAULT_STORAGE_STATE),
        help="Ruta de salida para storage_state.json.",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Mantener UI abierta luego de login para inspeccion.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    session_dir = Path(args.session_dir).resolve()
    storage_state_out = Path(args.storage_state_out).resolve()

    try:
        creds = load_credentials_from_env()
        with sync_playwright() as pw:
            # UI obligatoria: headless siempre False.
            context = open_context(
                playwright=pw,
                session_dir=session_dir,
                headless=False,
                browser=args.browser,
            )
            page = ensure_logged_in_page(context, creds=creds, check_antibot=False)

            storage_state_out.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(storage_state_out))
            print(f"[OK] Login UI completado. URL: {page.url}", file=sys.stderr)
            print(f"[OK] Storage state guardado en: {storage_state_out}", file=sys.stderr)

            if args.keep_open:
                print("[INFO] UI abierta. Presiona Ctrl+C para cerrar.", file=sys.stderr)
                try:
                    page.wait_for_timeout(24 * 60 * 60 * 1000)
                except KeyboardInterrupt:
                    pass

            context.close()
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
