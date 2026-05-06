#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from sidot_common import build_authenticated_session, ensure_dir, write_json


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch SIDOT extraction page by donante_id.")
    parser.add_argument(
        "--project-root",
        "--proyect-root",
        default=str(Path.cwd().resolve()),
        help="Project root path (default: current working directory).",
    )
    parser.add_argument(
        "--donante-id",
        required=True,
        type=int,
        help="Donor id from SIDOT (e.g. 5714).",
    )
    parser.add_argument("--stdout", action="store_true", help="Print parsed JSON to stdout.")
    return parser.parse_args()


def extract_trasplante_ids(html_text: str) -> list[int]:
    matches = re.findall(r"trasplante[_/-]?id[^0-9]*(\d+)|/trasplante/(\d+)", html_text, flags=re.I)
    ids: list[int] = []
    seen: set[int] = set()
    for m1, m2 in matches:
        value = m1 or m2
        if not value:
            continue
        tx_id = int(value)
        if tx_id in seen:
            continue
        seen.add(tx_id)
        ids.append(tx_id)
    return ids


def extract_receptor_names(html_text: str) -> list[str]:
    # Heuristic extraction for fields that commonly appear as "Receptor: NOMBRE".
    matches = re.findall(r"Receptor\s*[:\-]\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.]{4,})", html_text)
    names: list[str] = []
    seen: set[str] = set()
    for raw in matches:
        name = " ".join(raw.split())
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def extract_extraible_ids(html_text: str, donante_id: int) -> list[int]:
    matches = re.findall(
        rf"/donante/extraccion/extraible/{donante_id}/(\d+)",
        html_text,
        flags=re.I,
    )
    ids: list[int] = []
    seen: set[int] = set()
    for raw in matches:
        value = int(raw)
        if value in seen:
            continue
        seen.add(value)
        ids.append(value)
    return ids


def extract_trasplante_ids_from_extraible_detail(html_text: str) -> list[int]:
    matches = re.findall(r"/trasplante/(\d+)", html_text, flags=re.I)
    ids: list[int] = []
    seen: set[int] = set()
    for raw in matches:
        value = int(raw)
        if value in seen:
            continue
        seen.add(value)
        ids.append(value)
    return ids


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    out_dir = project_root / "doc" / ".sidot" / "extracciones"
    ensure_dir(out_dir)

    session, session_meta = build_authenticated_session(project_root)
    base_url = session_meta["base_url"]
    url = f"{base_url}/donante/extraccion/{args.donante_id}"
    response = session.get(url, timeout=30)
    response.raise_for_status()

    trasplante_ids = extract_trasplante_ids(response.text)
    receptor_names = extract_receptor_names(response.text)
    extraible_ids = extract_extraible_ids(response.text, args.donante_id)
    extraible_details = []

    # Fallback robusto: visitar detalle de cada extraible para detectar enlaces /trasplante/<id>.
    # Esta ruta fue necesaria en casos donde el listado no expone el trasplante_id directamente.
    if not trasplante_ids and extraible_ids:
        for extraible_id in extraible_ids:
            detail_url = f"{base_url}/donante/extraccion/extraible/{args.donante_id}/{extraible_id}"
            detail_response = session.get(detail_url, timeout=30)
            detail_response.raise_for_status()

            detail_tx_ids = extract_trasplante_ids_from_extraible_detail(detail_response.text)
            if detail_tx_ids:
                trasplante_ids = sorted(set(trasplante_ids).union(detail_tx_ids))

            detail_html_path = out_dir / f"extraible_{args.donante_id}_{extraible_id}.html"
            detail_html_path.write_text(detail_response.text, encoding="utf-8")
            extraible_details.append(
                {
                    "extraible_id": extraible_id,
                    "url": detail_url,
                    "trasplante_ids_detected": detail_tx_ids,
                    "html_path": str(detail_html_path),
                }
            )

    payload = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "donante_id": args.donante_id,
        "base_url": base_url,
        "url": url,
        "status_code": response.status_code,
        "extraible_ids_detected": extraible_ids,
        "extraible_details": extraible_details,
        "trasplante_ids_detected": trasplante_ids,
        "receptores_detectados": receptor_names,
    }

    html_path = out_dir / f"extracciones_donante_{args.donante_id}.html"
    json_path = out_dir / f"extracciones_donante_{args.donante_id}.json"
    html_path.write_text(response.text, encoding="utf-8")
    write_json(json_path, payload)

    print(f"Extracciones fetched for donante_id={args.donante_id}")
    print(f"JSON: {json_path}")
    print(f"HTML: {html_path}")
    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
