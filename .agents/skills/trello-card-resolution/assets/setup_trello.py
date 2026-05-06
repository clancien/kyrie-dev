#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

TRELLO_CONNECT_ASSETS = Path(__file__).resolve().parents[2] / "trello-connect" / "assets"
if str(TRELLO_CONNECT_ASSETS) not in sys.path:
    sys.path.insert(0, str(TRELLO_CONNECT_ASSETS))

from api import TrelloClient, load_env_file  # noqa: E402


def resolve_project_root(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg).resolve()
    return Path.cwd().resolve()


def usage() -> None:
    print(
        "Uso:\n"
        "  ./setup.sh [--project-root <ruta>]          # Modo interactivo (seleccionar board y lista)\n"
        "  ./setup.sh --read [--project-root <ruta>]   # Solo leer configuracion actual y resolver nombres"
    )


def get_env_value(key: str, env_values: dict[str, str]) -> str:
    return env_values.get(key) or os.environ.get(key, "")


def upsert_env(path: Path, key: str, value: str) -> None:
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    target = f"{key}="
    updated = False
    for index, line in enumerate(lines):
        if line.startswith(target):
            lines[index] = f"{key}={value}"
            updated = True
            break

    if not updated:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"{key}={value}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "********"
    return f"{value[:4]}...{value[-4:]}"


def build_token_url(trello_key: str) -> str:
    if not trello_key:
        return "<define TRELLO_KEY para generar URL>"
    query = urlencode(
        {
            "expiration": "never",
            "name": "SIDOT",
            "scope": "read,write",
            "response_type": "token",
            "key": trello_key,
        }
    )
    return f"https://trello.com/1/authorize?{query}"


def print_token_help(trello_key: str) -> None:
    print("URL para obtener TRELLO_TOKEN:")
    print(f"  {build_token_url(trello_key)}")
    print("")


def print_key_help() -> None:
    print("TRELLO_KEY no configurado.")
    print("Para crear/configurar una app de Power-Up en Trello:")
    print("  https://trello.com/power-ups/admin")
    print("Para obtener tu API key directamente:")
    print("  https://trello.com/app-key")
    print("")


def select_index(count: int, prompt: str) -> int:
    while True:
        selected = input(prompt).strip()
        if selected.isdigit():
            numeric = int(selected)
            if 1 <= numeric <= count:
                return numeric
        print(f"Seleccion invalida. Ingresa un numero entre 1 y {count}.")


def resolve_board_name(board_id: str, client: TrelloClient) -> str:
    if not board_id:
        return "<no resuelto>"
    try:
        data = client.get(f"boards/{board_id}", fields="name")
        return data.get("name", "<no resuelto>")
    except Exception:
        return "<no resuelto>"


def resolve_list_name(list_id: str, client: TrelloClient) -> str:
    if not list_id:
        return "<no resuelto>"
    try:
        data = client.get(f"lists/{list_id}", fields="name")
        return data.get("name", "<no resuelto>")
    except Exception:
        return "<no resuelto>"


def read_mode(env_values: dict[str, str], env_file: Path, project_root: Path) -> int:
    trello_key = get_env_value("TRELLO_KEY", env_values)
    trello_token = get_env_value("TRELLO_TOKEN", env_values)
    configured_board_id = get_env_value("TRELLO_BOARD_ID", env_values)
    configured_list_id = get_env_value("TRELLO_LIST_ID", env_values)
    filter_assignee = get_env_value("TRELLO_FILTER_ASIGNEE", env_values)

    print(f"Configuracion actual en {env_file}:")
    print(f"  TRELLO_KEY={mask_secret(trello_key)}")
    print(f"  TRELLO_TOKEN={mask_secret(trello_token)}")
    print(f"  TRELLO_BOARD_ID={configured_board_id or '<no configurado>'}")
    print(f"  TRELLO_LIST_ID={configured_list_id or '<no configurado>'}")
    print(f"  TRELLO_FILTER_ASIGNEE={filter_assignee or '<no configurado>'}")
    print("")

    if not trello_key:
        print_key_help()
        print("No se pueden resolver nombres de board/lista sin TRELLO_KEY.")
        print("Configura en .env:")
        print("  TRELLO_KEY=tu_trello_key")
        print("  TRELLO_TOKEN=tu_trello_token")
        return 1

    if not trello_token:
        print("No se pueden resolver nombres de board/lista sin credenciales.")
        print("Configura en .env:")
        print("  TRELLO_KEY=tu_trello_key")
        print("  TRELLO_TOKEN=tu_trello_token")
        print_token_help(trello_key)
        return 1

    client = TrelloClient.from_project_root(project_root)
    board_name = resolve_board_name(configured_board_id, client)
    list_name = resolve_list_name(configured_list_id, client)

    print(f"# Board: {board_name}")
    print(f"# Lista: {list_name}")
    return 0


def interactive_mode(env_values: dict[str, str], env_file: Path, project_root: Path) -> int:
    trello_key = get_env_value("TRELLO_KEY", env_values)
    trello_token = get_env_value("TRELLO_TOKEN", env_values)

    if not trello_key:
        print(f"Falta TRELLO_KEY en {env_file}.")
        print_key_help()
        print("Configura estas variables y vuelve a ejecutar:")
        print("  TRELLO_KEY=tu_trello_key")
        print("  TRELLO_TOKEN=tu_trello_token")
        return 1

    if not trello_token:
        print(f"Falta TRELLO_TOKEN en {env_file}.")
        print("Configura estas variables y vuelve a ejecutar:")
        print("  TRELLO_KEY=tu_trello_key")
        print("  TRELLO_TOKEN=tu_trello_token")
        print_token_help(trello_key)
        return 1

    client = TrelloClient.from_project_root(project_root)

    print("Obteniendo boards de Trello...")
    try:
        boards = client.get("members/me/boards", fields="id,name,closed", filter="open")
    except Exception:
        print("No se pudieron obtener boards. Verifica TRELLO_KEY/TRELLO_TOKEN.", file=sys.stderr)
        return 1

    open_boards = [(board["id"], board["name"]) for board in boards if not board.get("closed")]
    if not open_boards:
        print("No hay boards abiertos disponibles para este usuario/token.")
        return 1

    print("")
    print("Boards disponibles:")
    for index, (board_id, board_name) in enumerate(open_boards, start=1):
        print(f"  {index}) {board_name} ({board_id})")

    board_idx = select_index(len(open_boards), f"Selecciona board [1-{len(open_boards)}]: ")
    selected_board_id, selected_board_name = open_boards[board_idx - 1]

    print("")
    print("Obteniendo listas del board seleccionado...")
    try:
        lists = client.get(
            f"boards/{selected_board_id}/lists",
            fields="id,name,closed,pos",
        )
    except Exception:
        print(f"No se pudieron obtener listas del board {selected_board_id}.", file=sys.stderr)
        return 1

    open_lists = [(item["id"], item["name"]) for item in lists if not item.get("closed")]
    if not open_lists:
        print("El board seleccionado no tiene listas abiertas.")
        return 1

    print("")
    print("Listas disponibles:")
    for index, (list_id, list_name) in enumerate(open_lists, start=1):
        print(f"  {index}) {list_name} ({list_id})")

    list_idx = select_index(len(open_lists), f"Selecciona lista de trabajo [1-{len(open_lists)}]: ")
    selected_list_id, selected_list_name = open_lists[list_idx - 1]

    upsert_env(env_file, "TRELLO_BOARD_ID", selected_board_id)
    upsert_env(env_file, "TRELLO_LIST_ID", selected_list_id)

    print("")
    print(f"Configuracion aplicada en {env_file}:")
    print(f"  TRELLO_KEY={mask_secret(trello_key)}")
    print(f"  TRELLO_TOKEN={mask_secret(trello_token)}")
    print("")
    print(f"# Board: {selected_board_name}")
    print(f"TRELLO_BOARD_ID={selected_board_id}")
    print(f"# Lista: {selected_list_name}")
    print(f"TRELLO_LIST_ID={selected_list_id}")
    return 0


def main(argv: list[str]) -> int:
    mode = ""
    project_root_arg = None
    index = 1
    while index < len(argv):
        arg = argv[index]
        if arg == "--read":
            mode = "--read"
            index += 1
            continue
        if arg == "--project-root":
            if index + 1 >= len(argv):
                usage()
                return 1
            project_root_arg = argv[index + 1]
            index += 2
            continue
        usage()
        return 1

    project_root = resolve_project_root(project_root_arg)
    env_file = project_root / ".env"

    if not env_file.exists():
        print(f"No existe {env_file}")
        print("Crea el archivo con al menos:")
        print("  TRELLO_KEY=tu_trello_key")
        print("  TRELLO_TOKEN=tu_trello_token")
        print("")
        print("Si aun no tienes TRELLO_KEY:")
        print("  https://trello.com/power-ups/admin")
        print("  https://trello.com/app-key")
        print("")
        print("Luego podras generar TRELLO_TOKEN desde:")
        print("  https://trello.com/1/authorize?expiration=never&name=SIDOT&scope=read,write&response_type=token&key=TU_TRELLO_KEY")
        return 1

    env_values = load_env_file(env_file)
    if mode == "--read":
        return read_mode(env_values, env_file, project_root)
    return interactive_mode(env_values, env_file, project_root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
