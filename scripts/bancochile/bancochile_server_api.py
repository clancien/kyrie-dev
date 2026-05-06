#!/usr/bin/env python3
"""CLI para consultar APIs de Banco de Chile reutilizando session cacheada."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bancochile_server_core import DEFAULT_CACHE_DIR, DEFAULT_OUTPUT_DIR, run_all_api


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="API Bancochile sin Playwright (sesion cacheada).")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--account-number", default="")
    parser.add_argument("--from-index", type=int, default=1)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--incluir-tarjetas-selector", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cache_dir = Path(args.cache_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    try:
        payload = run_all_api(
            cache_dir=cache_dir,
            output_dir=output_dir,
            account_number=args.account_number,
            from_index=args.from_index,
            step=args.step,
            max_pages=args.max_pages,
            incluir_tarjetas_selector=args.incluir_tarjetas_selector,
        )
        print(f"[OK] Archivo guardado: {output_dir / 'movimientos_server_latest.json'}", file=sys.stderr)
        print(f"[OK] Archivo guardado: {output_dir / 'selector_productos_server_latest.json'}", file=sys.stderr)
        print(f"[OK] Archivo guardado: {output_dir / 'saldos_server_latest.json'}", file=sys.stderr)
        print(f"[OK] Archivo guardado: {output_dir / 'tarjetas_server_latest.json'}", file=sys.stderr)
        print(f"[OK] Archivo guardado: {output_dir / 'movimientos_api_server_latest.json'}", file=sys.stderr)
        if args.print_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
