#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from api import AUTH_URL, SCOPES, GmailOAuthClient  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Gmail OAuth helper.")
    parser.add_argument("--project-root", "--proyect-root", default=str(Path.cwd().resolve()))
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth-url", help="Generate Google OAuth consent URL")

    exchange = sub.add_parser("exchange-code", help="Exchange OAuth code for refresh token")
    exchange.add_argument("--code", required=True, help="Authorization code from consent callback")
    exchange.add_argument("--stdout", action="store_true", help="Print full token payload")
    return parser.parse_args()


def main():
    args = parse_args()
    client = GmailOAuthClient.from_project_root(Path(args.project_root).resolve())

    if args.cmd == "auth-url":
        params = {
            "client_id": client.client_id,
            "redirect_uri": client.redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }
        url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
        print(url)
        return

    data = client.exchange_code(args.code)
    refresh_token = data.get("refresh_token", "")
    if refresh_token:
        print("GMAIL_REFRESH_TOKEN obtained.")
        print("Add this line to .env:")
        print(f"GMAIL_REFRESH_TOKEN={refresh_token}")
    else:
        print("No refresh_token returned. Ensure prompt=consent and access_type=offline.")

    if args.stdout:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
