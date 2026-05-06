#!/usr/bin/env python3
import argparse
import base64
import json
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from api import GmailApiClient  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Gmail read and draft client.")
    parser.add_argument("--project-root", "--proyect-root", default=str(Path.cwd().resolve()))
    sub = parser.add_subparsers(dest="cmd", required=True)

    read = sub.add_parser("read", help="Read messages from Gmail")
    read.add_argument("--query", default="", help="Gmail query (q=...)")
    read.add_argument("--max-results", type=int, default=10, help="Max messages to list")
    read.add_argument("--stdout", action="store_true", help="Print JSON payload")

    draft = sub.add_parser("draft", help="Create draft email")
    draft.add_argument("--to", required=True)
    draft.add_argument("--subject", required=True)
    draft.add_argument("--body", required=True)
    draft.add_argument("--cc", default="")
    draft.add_argument("--bcc", default="")
    draft.add_argument("--stdout", action="store_true", help="Print JSON payload")
    return parser.parse_args()


def message_headers_by_name(headers: list[dict]) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in headers or []:
        name = (item.get("name") or "").strip()
        value = (item.get("value") or "").strip()
        if name:
            output[name.lower()] = value
    return output


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    client = GmailApiClient.from_project_root(project_root)

    out_dir = project_root / "doc" / "gmail"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.cmd == "read":
        list_data = client.list_messages(query=args.query, max_results=args.max_results)
        messages = []
        for item in list_data.get("messages", []) or []:
            msg_id = item.get("id")
            if not msg_id:
                continue
            detail = client.get_message_metadata(msg_id)
            hdr = message_headers_by_name(((detail.get("payload") or {}).get("headers") or []))
            messages.append(
                {
                    "id": msg_id,
                    "threadId": detail.get("threadId"),
                    "snippet": detail.get("snippet"),
                    "from": hdr.get("from", ""),
                    "to": hdr.get("to", ""),
                    "subject": hdr.get("subject", ""),
                    "date": hdr.get("date", ""),
                }
            )

        payload = {
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "query": args.query,
            "max_results": args.max_results,
            "count": len(messages),
            "messages": messages,
        }
        json_path = out_dir / "messages_latest.json"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Read OK. Messages: {len(messages)}")
        print(f"Output: {json_path}")
        if args.stdout:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    msg = EmailMessage()
    msg["To"] = args.to
    if args.cc:
        msg["Cc"] = args.cc
    if args.bcc:
        msg["Bcc"] = args.bcc
    msg["Subject"] = args.subject
    msg.set_content(args.body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    data = client.create_draft(raw)
    payload = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "draft_id": (data.get("id") or ""),
        "message_id": ((data.get("message") or {}).get("id") or ""),
        "thread_id": ((data.get("message") or {}).get("threadId") or ""),
        "to": args.to,
        "subject": args.subject,
    }
    json_path = out_dir / "draft_latest.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Draft created.")
    print(f"Output: {json_path}")
    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
