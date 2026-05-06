#!/usr/bin/env python3
import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from sidot_common import build_authenticated_session, write_json


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch SIDOT hospitals catalog.")
    parser.add_argument(
        "--project-root",
        "--proyect-root",
        default=str(Path.cwd().resolve()),
        help="Project root path (default: current working directory).",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.2,
        help="Wait time between page fetches.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print result JSON to stdout.")
    return parser.parse_args()


def parse_hospitals_from_html(html_text: str) -> list[dict]:
    # Minimal parser based on row shape used in SIDOT table.
    row_pattern = re.compile(
        r'<tr[^>]*class="clickZone"[^>]*>(.*?)</tr>', re.IGNORECASE | re.DOTALL
    )
    cell_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
    tag_pattern = re.compile(r"<[^>]+>")
    id_pattern = re.compile(r"/pref/hospital/(\d+)")

    hospitals: list[dict] = []
    for row in row_pattern.findall(html_text):
        cols = cell_pattern.findall(row)
        if len(cols) < 7:
            continue
        values = []
        for col in cols:
            clean = tag_pattern.sub("", col)
            clean = " ".join(clean.replace("&nbsp;", " ").split())
            values.append(clean)

        hospital_id = None
        link_match = id_pattern.search(cols[6])
        if link_match:
            hospital_id = int(link_match.group(1))

        hospitals.append(
            {
                "codigo": values[0],
                "nombre": values[1],
                "servicio": values[2],
                "region": values[3],
                "comuna": values[4],
                "actividad": values[5],
                "hospital_id": hospital_id,
            }
        )
    return hospitals


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    # Output requerido: $PROJECT_ROOT/doc/.sidot/hospitales.json
    output_path = project_root / "doc" / ".sidot" / "hospitales.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    session, session_meta = build_authenticated_session(project_root)
    base_url = session_meta["base_url"]
    url_template = f"{base_url}/pref/hospital/?pageIndex={{}}"

    all_hospitals: list[dict] = []
    seen_codes: set[str] = set()
    page_index = 0

    while True:
        url = url_template.format(page_index)
        response = session.get(url, timeout=30)
        response.raise_for_status()

        page_hospitals = parse_hospitals_from_html(response.text)
        if not page_hospitals:
            break

        new_rows = 0
        for item in page_hospitals:
            code = item.get("codigo", "")
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            all_hospitals.append(item)
            new_rows += 1

        if new_rows == 0:
            break

        page_index += 1
        time.sleep(args.sleep_seconds)

    payload = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "total_hospitales": len(all_hospitals),
        "hospitales": all_hospitals,
    }
    write_json(output_path, payload)

    print(f"Done. Hospitals fetched: {len(all_hospitals)}")
    print(f"Output: {output_path}")
    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
