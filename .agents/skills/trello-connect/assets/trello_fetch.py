#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

CURRENT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = CURRENT_DIR.parent / "assets"
if str(ASSETS_DIR) not in sys.path:
    sys.path.insert(0, str(ASSETS_DIR))

from api import TrelloClient  # noqa: E402


def payload(data):
    return {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


def cmd_ping(args, client: TrelloClient):
    me = client.get("members/me", fields="id,fullName,username")
    return payload({"ok": True, "member": me})


def cmd_boards(args, client: TrelloClient):
    boards = client.get(
        "members/me/boards",
        fields="id,name,desc,closed,url,idOrganization",
        filter="open",
    )
    boards = sorted(boards, key=lambda item: (item.get("name") or "").lower())
    return payload({"total_boards": len(boards), "boards": boards})


def resolve_board_id(args):
    return args.board_id or os.getenv("TRELLO_BOARD_ID")


def resolve_list_id(args):
    return args.list_id or os.getenv("TRELLO_LIST_ID")


def cmd_lists(args, client: TrelloClient):
    board_id = resolve_board_id(args)
    if not board_id:
        raise RuntimeError("Missing board id. Use --board-id or define TRELLO_BOARD_ID")

    lists = client.get(f"boards/{board_id}/lists", fields="id,name,closed,pos")
    lists = sorted(lists, key=lambda item: (item.get("name") or "").lower())
    board = client.get(f"boards/{board_id}", fields="id,name")
    return payload(
        {
            "board": {"id": board.get("id"), "name": board.get("name")},
            "total_lists": len(lists),
            "lists": lists,
        }
    )


def cmd_cards(args, client: TrelloClient):
    list_id = resolve_list_id(args)
    if not list_id:
        raise RuntimeError("Missing list id. Use --list-id or define TRELLO_LIST_ID")

    cards = client.get(
        f"lists/{list_id}/cards",
        filter="open",
        members="true",
        member_fields="username,fullName",
        fields="id,name,desc,dateLastActivity,idBoard,idList,url",
    )
    list_data = client.get(f"lists/{list_id}", fields="id,name,idBoard")
    board = {}
    if list_data.get("idBoard"):
        board_raw = client.get(f"boards/{list_data['idBoard']}", fields="id,name")
        board = {"id": board_raw.get("id"), "name": board_raw.get("name")}
    return payload(
        {
            "board": board,
            "list": {
                "id": list_data.get("id"),
                "name": list_data.get("name"),
                "board_id": list_data.get("idBoard"),
            },
            "total_cards": len(cards),
            "cards": cards,
        }
    )


def cmd_card(args, client: TrelloClient):
    card = client.get(
        f"cards/{args.card_id}",
        fields="id,name,desc,dateLastActivity,idBoard,idList,url",
        attachments="true",
        members="true",
        member_fields="fullName,username",
        actions="commentCard",
        actions_limit="100",
    )
    return payload({"card": card})


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Trello resources to stdout (JSON).")
    parser.add_argument("--project-root", default=str(Path.cwd().resolve()))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("ping")
    subparsers.add_parser("boards")
    lists = subparsers.add_parser("lists")
    lists.add_argument("--board-id")
    cards = subparsers.add_parser("cards")
    cards.add_argument("--list-id")
    card = subparsers.add_parser("card")
    card.add_argument("--card-id", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    client = TrelloClient.from_project_root(Path(args.project_root).resolve())

    command_handlers = {
        "ping": cmd_ping,
        "boards": cmd_boards,
        "lists": cmd_lists,
        "cards": cmd_cards,
        "card": cmd_card,
    }

    try:
        result = command_handlers[args.command](args, client)
    except requests.HTTPError as exc:
        message = f"HTTP {exc.response.status_code} - {exc.response.text}" if exc.response is not None else str(exc)
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False, indent=2))
        return 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
