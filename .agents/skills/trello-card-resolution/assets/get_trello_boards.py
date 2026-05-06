import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TRELLO_CONNECT_ASSETS = Path(__file__).resolve().parents[2] / "trello-connect" / "assets"
if str(TRELLO_CONNECT_ASSETS) not in sys.path:
    sys.path.insert(0, str(TRELLO_CONNECT_ASSETS))

from api import TrelloClient  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Trello boards and write to file or stdout.")
    parser.add_argument("--project-root", default=str(Path.cwd().resolve()))
    parser.add_argument("--stdout", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    base_dir = Path(args.project_root).resolve()
    trello_dir = base_dir / "doc" / ".trello"
    output_path = trello_dir / "trello_boards.json"
    trello_dir.mkdir(parents=True, exist_ok=True)

    client = TrelloClient.from_project_root(base_dir)
    boards = client.get(
        "members/me/boards",
        fields="id,name,desc,closed,url,idOrganization",
        filter="open",
    )

    payload = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_boards": len(boards),
        "boards": sorted(boards, key=lambda item: item.get("name", "").lower()),
    }

    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Done! Updated {output_path} with {len(boards)} boards.")


if __name__ == "__main__":
    main()
