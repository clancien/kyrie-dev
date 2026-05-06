import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = None
DOC_DIR = None
TRELLO_DIR = None
DONE_DIR = None
CARDS_JSON = None
ENV_FILE_PATH = None
LIST_ID = None
FILTER_ASSIGNEE = ""
TRELLO_CLIENT = None


def load_env_file(env_path):
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env_var(var_name):
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {var_name}. "
            f"Define it in {ENV_FILE_PATH}"
        )
    return value


def configure_runtime(project_root):
    global BASE_DIR, DOC_DIR, TRELLO_DIR, DONE_DIR, CARDS_JSON, ENV_FILE_PATH
    global LIST_ID, FILTER_ASSIGNEE, TRELLO_CLIENT

    base_dir = Path(project_root).resolve()
    BASE_DIR = str(base_dir)
    DOC_DIR = str(base_dir / "doc")
    TRELLO_DIR = str(base_dir / "doc" / ".trello")
    DONE_DIR = str(base_dir / "doc" / ".trello" / ".done")
    CARDS_JSON = str(base_dir / "doc" / ".trello" / "cards.json")
    ENV_FILE_PATH = str(base_dir / ".env")

    os.makedirs(TRELLO_DIR, exist_ok=True)
    os.makedirs(DONE_DIR, exist_ok=True)

    load_env_file(ENV_FILE_PATH)
    LIST_ID = require_env_var("TRELLO_LIST_ID")
    FILTER_ASSIGNEE = (os.getenv("TRELLO_FILTER_ASIGNEE") or "").strip()

    trello_assets = base_dir / ".agents" / "skills" / "trello-connect" / "assets"
    if str(trello_assets) not in sys.path:
        sys.path.insert(0, str(trello_assets))
    from api import TrelloClient  # noqa: E402

    TRELLO_CLIENT = TrelloClient.from_project_root(base_dir)


def normalize_assignee_filter(value):
    normalized = (value or "").strip().lower()
    if normalized.startswith("@"):
        normalized = normalized[1:]
    return normalized


def fetch_cards():
    cards = TRELLO_CLIENT.get(
        f"lists/{LIST_ID}/cards",
        filter="open",
        members="true",
        member_fields="username,fullName",
        fields="id,name,desc,dateLastActivity,idBoard,idList,url",
    )
    list_data = TRELLO_CLIENT.get(f"lists/{LIST_ID}", fields="id,name,idBoard")
    board_data = {}
    if list_data.get("idBoard"):
        board_data = TRELLO_CLIENT.get(
            f"boards/{list_data['idBoard']}", fields="id,name"
        )
    filter_assignee = normalize_assignee_filter(FILTER_ASSIGNEE)
    if not filter_assignee:
        return cards, {"list": list_data, "board": board_data}

    filtered_cards = []
    for card in cards:
        members = card.get("members", []) or []
        usernames = []
        for member in members:
            if not isinstance(member, dict):
                continue
            username = normalize_assignee_filter(member.get("username"))
            if username:
                usernames.append(username)
        if filter_assignee in usernames:
            filtered_cards.append(card)

    return filtered_cards, {"list": list_data, "board": board_data}


def fetch_list_context():
    list_data = TRELLO_CLIENT.get(f"lists/{LIST_ID}", fields="id,name,idBoard")
    board_data = {}
    if list_data.get("idBoard"):
        board_data = TRELLO_CLIENT.get(
            f"boards/{list_data['idBoard']}", fields="id,name"
        )
    return {
        "list_id": LIST_ID,
        "list_name": list_data.get("name", "Unknown"),
        "board_id": board_data.get("id"),
        "board_name": board_data.get("name", "Unknown"),
    }


def fetch_card_details(card_id):
    return TRELLO_CLIENT.get(
        f"cards/{card_id}",
        fields="id,name,desc,dateLastActivity,idBoard,idList,url",
        attachments="true",
        members="true",
        member_fields="fullName,username",
        actions="commentCard",
        actions_limit="100",
    )


def extract_members(details):
    members = []
    for member in details.get("members", []):
        if not isinstance(member, dict):
            continue
        members.append(
            {
                "id": member.get("id"),
                "full_name": member.get("fullName"),
                "username": member.get("username"),
            }
        )
    return members


def extract_comments(details):
    comments = []
    for action in details.get("actions", []):
        if not isinstance(action, dict) or action.get("type") != "commentCard":
            continue
        member = action.get("memberCreator") or {}
        comments.append(
            {
                "id": action.get("id"),
                "date": action.get("date"),
                "text": ((action.get("data") or {}).get("text") or ""),
                "member": {
                    "id": member.get("id"),
                    "full_name": member.get("fullName"),
                    "username": member.get("username"),
                },
            }
        )
    comments.sort(key=lambda item: item.get("date") or "")
    return comments


def download_attachment(card_folder, card_id, attachment_id, filename):
    response = TRELLO_CLIENT.download_card_attachment(card_id, attachment_id, filename)
    filepath = os.path.join(card_folder, filename)
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return filepath


def extract_pdf_text(pdf_path):
    txt_path = pdf_path.replace(".pdf", ".txt")
    subprocess.run(["pdftotext", pdf_path, txt_path])
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def load_cards_index():
    existing_cards = {}
    if os.path.exists(CARDS_JSON):
        with open(CARDS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for row in data:
                    if isinstance(row, dict) and row.get("id"):
                        existing_cards[row["id"]] = row
    return existing_cards


def save_cards_index(cards_map):
    payload = [cards_map[cid] for cid in sorted(cards_map.keys())]
    with open(CARDS_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def safe_card_folder_name(card_name):
    return card_name.replace("/", "_").replace("\\", "_")


def card_analysis_relative_path(card_name, done=False):
    base_done = ".done" if done else ""
    parts = ["doc", ".trello"]
    if base_done:
        parts.append(base_done)
    parts.extend([card_name, "analysis.md"])
    return "/".join(parts)


def move_card_folder_to_done(card_name):
    source_folder = os.path.join(TRELLO_DIR, card_name)
    if not os.path.isdir(source_folder):
        return None
    target_folder = os.path.join(DONE_DIR, card_name)
    if os.path.exists(target_folder):
        target_folder = os.path.join(DONE_DIR, f"{card_name}__closed")
        suffix = 1
        while os.path.exists(target_folder):
            target_folder = os.path.join(DONE_DIR, f"{card_name}__closed_{suffix}")
            suffix += 1
    shutil.move(source_folder, target_folder)
    return os.path.relpath(target_folder, DOC_DIR).replace("\\", "/")


def ensure_active_card_folder(card_name):
    active_folder = os.path.join(TRELLO_DIR, card_name)
    done_folder = os.path.join(DONE_DIR, card_name)
    if not os.path.isdir(active_folder) and os.path.isdir(done_folder):
        shutil.move(done_folder, active_folder)


def is_card_in_done(card_name):
    return os.path.isdir(os.path.join(DONE_DIR, card_name))


def reconcile_cards_moved_to_done(cards_map):
    for card_data in cards_map.values():
        card_name = safe_card_folder_name(card_data.get("name", ""))
        if not card_name or not is_card_in_done(card_name):
            continue
        card_data["md_link"] = card_analysis_relative_path(card_name, done=True)
        card_data["status"] = "CERRADO"


def refresh_cards_ui():
    render_script = os.path.join(
        BASE_DIR, ".agents", "skills", "trello-card-resolution", "assets", "render_cards_html.py"
    )
    if not os.path.exists(render_script):
        print(f"UI refresh skipped: render script not found at {render_script}")
        return
    result = subprocess.run(
        ["python3", render_script, "--project-root", BASE_DIR],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        error_output = result.stderr.strip() or "Unknown error"
        print(f"UI refresh failed: {error_output}")


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Trello cards and write artifacts or print JSON.")
    parser.add_argument("--project-root", default=str(Path.cwd().resolve()))
    parser.add_argument("--stdout", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    configure_runtime(args.project_root)
    list_context = fetch_list_context()
    print(f"Working on Trello board: {list_context['board_name']} ({list_context['board_id'] or 'unknown'})")
    print(f"Working on Trello list: {list_context['list_name']} ({list_context['list_id']})")
    print(f"Fetching open cards from list {LIST_ID}...")
    cards, list_payload = fetch_cards()

    if args.stdout:
        payload = {
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "board": {
                "id": list_payload.get("board", {}).get("id"),
                "name": list_payload.get("board", {}).get("name"),
            },
            "list": {
                "id": list_payload.get("list", {}).get("id") or list_context["list_id"],
                "name": list_payload.get("list", {}).get("name") or list_context["list_name"],
            },
            "total_cards": len(cards),
            "cards": cards,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    try:
        existing_cards = load_cards_index()
        reconcile_cards_moved_to_done(existing_cards)
        open_card_ids = set()

        for card in cards:
            card_id = card["id"]
            card_name = safe_card_folder_name(card["name"])
            open_card_ids.add(card_id)
            ensure_active_card_folder(card_name)

            card_folder = os.path.join(TRELLO_DIR, card_name)
            os.makedirs(card_folder, exist_ok=True)

            print(f"Processing card: {card_name}...")
            details = fetch_card_details(card_id)
            desc = details.get("desc", "")
            members = extract_members(details)
            comments = extract_comments(details)
            attachments_text = ""

            for att in details.get("attachments", []):
                if att["name"].lower().endswith(".pdf"):
                    print(f"  Downloading and reading: {att['name']}")
                    pdf_path = download_attachment(card_folder, card_id, att["id"], att["name"])
                    attachments_text += f"\n\n--- Content from {att['name']} ---\n"
                    attachments_text += extract_pdf_text(pdf_path)

            full_content = desc + attachments_text
            summary_path = os.path.join(card_folder, "analysis.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"# Información de Tarjeta: {card_name}\n\n")
                f.write(f"**Trello ID:** {card_id}\n")
                f.write(f"**Fecha Descarga:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## Contenido Extraído\n")
                f.write(full_content)

            previous_created = existing_cards.get(card_id, {}).get("created_date")
            existing_cards[card_id] = {
                "id": card_id,
                "name": card_name,
                "description": desc[:100].replace("\n", " "),
                "md_link": card_analysis_relative_path(card_name),
                "created_date": previous_created or datetime.now().strftime("%Y-%m-%d"),
                "members": members,
                "comments": comments,
                "status": "DESCARGADO",
            }

        for card_id, card_data in existing_cards.items():
            if card_id in open_card_ids:
                continue
            card_name = safe_card_folder_name(card_data.get("name", card_id))
            done_rel_path = move_card_folder_to_done(card_name)
            if done_rel_path or is_card_in_done(card_name):
                card_data["md_link"] = card_analysis_relative_path(card_name, done=True)
            card_data["status"] = "CERRADO"

        reconcile_cards_moved_to_done(existing_cards)
        save_cards_index(existing_cards)
        print(f"\nDone! Processed {len(cards)} cards.")
        print(f"Index updated at {CARDS_JSON}")
    finally:
        refresh_cards_ui()


if __name__ == "__main__":
    main()
