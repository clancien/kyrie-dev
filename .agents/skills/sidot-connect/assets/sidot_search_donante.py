#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from sidot_common import build_authenticated_session, ensure_dir, write_json


def parse_args():
    parser = argparse.ArgumentParser(description="Search SIDOT donor by codigo SIDOT.")
    parser.add_argument(
        "--project-root",
        "--proyect-root",
        default=str(Path.cwd().resolve()),
        help="Project root path (default: current working directory).",
    )
    parser.add_argument(
        "--codigo-sidot",
        required=True,
        help="SIDOT code to search, e.g., 2025094935.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print parsed JSON to stdout.")
    return parser.parse_args()


def extract_donante_ids(html_text: str) -> list[int]:
    matches = re.findall(
        r"/donante/(?:identificacion|extraccion|datos|antecedentes)/(\d+)",
        html_text,
        flags=re.I,
    )
    ids: list[int] = []
    seen: set[int] = set()
    for raw in matches:
        donor_id = int(raw)
        if donor_id in seen:
            continue
        seen.add(donor_id)
        ids.append(donor_id)
    return ids


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    out_dir = project_root / "doc" / ".sidot" / "donante_search"
    ensure_dir(out_dir)

    session, session_meta = build_authenticated_session(project_root)
    base_url = session_meta["base_url"]
    query = urlencode({"busqueda": "", "busqueda.codigoSidot": args.codigo_sidot})
    url = f"{base_url}/donante/?{query}"

    response = session.get(url, timeout=30)
    response.raise_for_status()

    donor_ids = extract_donante_ids(response.text)
    payload = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "codigo_sidot": args.codigo_sidot,
        "base_url": base_url,
        "url": url,
        "status_code": response.status_code,
        "donante_ids": donor_ids,
        "donante_count": len(donor_ids),
    }

    html_path = out_dir / f"donante_{args.codigo_sidot}.html"
    json_path = out_dir / f"donante_{args.codigo_sidot}.json"
    html_path.write_text(response.text, encoding="utf-8")
    write_json(json_path, payload)

    print(f"Search done. Parsed {len(donor_ids)} donor id(s).")
    print(f"JSON: {json_path}")
    print(f"HTML: {html_path}")
    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
