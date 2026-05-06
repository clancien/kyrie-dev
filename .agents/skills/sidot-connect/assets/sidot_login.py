#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
from pathlib import Path

from sidot_common import build_authenticated_session, ensure_dir, write_json


def parse_args():
    parser = argparse.ArgumentParser(description="Login to SIDOT and persist session cookies.")
    parser.add_argument(
        "--project-root",
        "--proyect-root",
        default=str(Path.cwd().resolve()),
        help="Project root path (default: current working directory).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print metadata JSON to stdout.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    session_dir = project_root / "doc" / ".sidot" / "session"
    ensure_dir(session_dir)

    _, metadata = build_authenticated_session(project_root)
    payload = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "base_url": metadata["base_url"],
        "authenticated": metadata["authenticated"],
        "auth_url": metadata["auth_url"],
        "status_code": metadata["status_code"],
        "cookies": metadata["cookies"],
    }

    write_json(session_dir / "cookies.json", payload)
    (session_dir / "login_response.html").write_text(
        metadata["auth_response_html"], encoding="utf-8"
    )

    print(f"Login OK. Session saved to {session_dir / 'cookies.json'}")
    if args.stdout:
        import json

        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
