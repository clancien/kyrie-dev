#!/usr/bin/env python3
import argparse
import getpass
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from api import SidotClient, env_get, load_env_file


def parse_args():
    parser = argparse.ArgumentParser(description="Verify SIDOT login for a specific user without persisting the password.")
    parser.add_argument(
        "--project-root",
        "--proyect-root",
        default=str(Path.cwd().resolve()),
        help="Project root path (default: current working directory).",
    )
    parser.add_argument("--username", required=True, help="SIDOT username to verify.")
    parser.add_argument(
        "--password",
        default="",
        help="SIDOT password to verify. Prefer --password-stdin or interactive prompt.",
    )
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="Read password from stdin. The password is never printed.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print safe verification metadata as JSON.",
    )
    return parser.parse_args()


def read_password(args) -> str:
    if args.password_stdin:
        password = sys.stdin.read().strip()
    elif args.password:
        password = args.password
    else:
        password = getpass.getpass("SIDOT password: ")

    if not password:
        raise RuntimeError("Password is required.")
    return password


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    env_path = project_root / ".env"
    env_values = load_env_file(env_path)
    base_url = env_get("SIDOT_URL", env_values, env_path).rstrip("/")
    password = read_password(args)

    client = SidotClient(base_url=base_url, username=args.username, password=password)
    try:
        metadata = client.login()
    except Exception as exc:
        print(f"Login verified for {args.username}: False", file=sys.stderr)
        print(f"Reason: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    payload = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "base_url": metadata["base_url"],
        "username": metadata["username"],
        "authenticated": metadata["authenticated"],
        "auth_url": metadata["auth_url"],
        "status_code": metadata["status_code"],
    }

    print(f"Login verified for {args.username}: {payload['authenticated']}")
    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
