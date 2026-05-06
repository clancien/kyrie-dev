#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from sidot_common import build_authenticated_session, ensure_dir, write_json


def parse_args():
    parser = argparse.ArgumentParser(description="Search SIDOT users by query text.")
    parser.add_argument(
        "--project-root",
        "--proyect-root",
        default=str(Path.cwd().resolve()),
        help="Project root path (default: current working directory).",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Search query for users, e.g. apellido, nombre, username.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print parsed JSON to stdout.")
    return parser.parse_args()


def extract_user_ids(html_text: str) -> list[int]:
    patterns = [
        r"/pref/usuario/editar/(\d+)",
        r"/pref/usuario/edit/(\d+)",
        r"/pref/usuario/ver/(\d+)",
        r"/pref/usuario/(\d+)\b",
    ]
    ids: list[int] = []
    seen: set[int] = set()
    for pattern in patterns:
        for raw in re.findall(pattern, html_text, flags=re.I):
            value = int(raw)
            if value in seen:
                continue
            seen.add(value)
            ids.append(value)
    return ids


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    out_dir = project_root / "doc" / ".sidot" / "usuarios"
    ensure_dir(out_dir)

    session, session_meta = build_authenticated_session(project_root)
    base_url = session_meta["base_url"]
    query = urlencode({"busqueda.query": args.query})
    url = f"{base_url}/pref/usuario/?{query}"

    response = session.get(url, timeout=30)
    response.raise_for_status()

    user_ids = extract_user_ids(response.text)
    payload = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query": args.query,
        "base_url": base_url,
        "url": url,
        "status_code": response.status_code,
        "user_ids": user_ids,
        "user_count": len(user_ids),
    }

    safe_query = re.sub(r"[^a-zA-Z0-9_-]+", "_", args.query).strip("_") or "query"
    html_path = out_dir / f"usuarios_{safe_query}.html"
    json_path = out_dir / f"usuarios_{safe_query}.json"
    html_path.write_text(response.text, encoding="utf-8")
    write_json(json_path, payload)

    print(f"User search done. Parsed {len(user_ids)} user id(s).")
    print(f"JSON: {json_path}")
    print(f"HTML: {html_path}")
    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
