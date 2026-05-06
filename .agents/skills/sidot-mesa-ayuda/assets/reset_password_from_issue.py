#!/usr/bin/env python3
import argparse
import re
import secrets
import string
import sys
import importlib.util
from pathlib import Path
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

GITLAB_API_PATH = Path(__file__).resolve().parents[2] / "gitlab-connect" / "assets" / "api.py"
SIDOT_API_PATH = Path(__file__).resolve().parents[2] / "sidot-connect" / "assets" / "api.py"


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gitlab_api = _load_module("gitlab_connect_api", GITLAB_API_PATH)
GitLabClient = gitlab_api.GitLabClient
load_env_file = gitlab_api.load_env_file
env_get = gitlab_api.env_get
SidotClient = _load_module("sidot_connect_api", SIDOT_API_PATH).SidotClient


def generate_password(length: int = 20) -> str:
    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()-_=+[]{}.?~"
    pool = lowers + uppers + digits + symbols
    while True:
        chars = [
            secrets.choice(lowers),
            secrets.choice(uppers),
            secrets.choice(digits),
            secrets.choice(symbols),
        ]
        chars += [secrets.choice(pool) for _ in range(length - len(chars))]
        secrets.SystemRandom().shuffle(chars)
        password = "".join(chars)
        if " " in password:
            continue
        if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password) and re.search(r"\d", password) and re.search(r"[^A-Za-z0-9]", password):
            return password


def parse_issue_username(description: str) -> str | None:
    for pattern in [r"Usuario:\s*([A-Za-z0-9._-]+)", r"usuario\s*sidot\s*:\s*([A-Za-z0-9._-]+)", r"login:\s*([A-Za-z0-9._-]+)"]:
        m = re.search(pattern, description or "", flags=re.I)
        if m:
            return m.group(1).strip()
    return None


def parse_issue_email(description: str) -> str | None:
    patterns = [
        r"Email(?:\s*\([^)]*\))?:\s*([^\s<]+@[^\s<]+)",
        r"Correo(?:\s+electr[oó]nico)?(?:\s*\([^)]*\))?:\s*([^\s<]+@[^\s<]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, description or "", flags=re.I)
        if m:
            return m.group(1).strip().rstrip(".,;")
    return None


def parse_issue_full_name(description: str) -> str | None:
    for pattern in [r"Nombre:\s*([^\n\r]+)", r"Nombre completo:\s*([^\n\r]+)", r"Solicitante:\s*([^\n\r]+)"]:
        m = re.search(pattern, description or "", flags=re.I)
        if m:
            name = " ".join(m.group(1).strip().rstrip(".").split())
            if name:
                return name
    return None


def infer_gender_from_name(full_name: str) -> str | None:
    first = (full_name.strip().split()[0] if full_name else "").lower()
    female_names = {"maria", "claudia", "paula", "carolina", "sofia", "camila", "valentina", "daniela", "andrea", "patricia", "gabriela", "fernanda"}
    male_names = {"juan", "carlos", "jaime", "pedro", "jose", "miguel", "cristian", "sebastian", "rodrigo", "ricardo", "manuel", "francisco"}
    if first in female_names:
        return "F"
    if first in male_names:
        return "M"
    if first.endswith("a"):
        return "F"
    if first.endswith(("o", "n", "r", "l", "s")):
        return "M"
    return None


def build_saludo(nombre: str, sexo: str | None) -> str:
    cleaned = " ".join((nombre or "").split())
    if not cleaned:
        raise RuntimeError("Missing applicant name for personalized greeting.")
    normalized = (sexo or "").strip().upper()
    if normalized not in {"F", "M"}:
        normalized = infer_gender_from_name(cleaned) or ""
        if normalized not in {"F", "M"}:
            raise RuntimeError("Could not infer applicant gender. Use --sexo F or --sexo M.")
    return f"{'Estimada' if normalized == 'F' else 'Estimado'} {cleaned}"


def parse_user_edit_link(html_text: str) -> str | None:
    m = re.search(r'href="(/pref/usuario/edit/\d+\?state=[^"]+)"', html_text, flags=re.I)
    return m.group(1) if m else None


def parse_user_edit_links(html_text: str) -> list[str]:
    links: list[str] = []
    for match in re.finditer(r'href="(/pref/usuario/edit/\d+\?state=[^"]+)"', html_text, flags=re.I):
        link = match.group(1)
        if link not in links:
            links.append(link)
    return links


def collect_multiple_select_values(form: BeautifulSoup, name: str, hidden_name: str) -> list[str]:
    select = form.find(attrs={"name": name})
    values = []
    if select is not None:
        values = [option.get("value", "") for option in select.find_all("option", selected=True)]

    if values:
        return values

    hidden = form.find(attrs={"name": hidden_name})
    raw_values = hidden.get("data-values", "") if hidden is not None else ""
    return re.findall(r"\d+", raw_values)


def collect_password_reset_payload(form: BeautifulSoup, new_password: str) -> list[tuple[str, str]]:
    required_fields = ["__csrftoken", "usuarioId", "state"]
    payload: list[tuple[str, str]] = []
    for field in required_fields:
        element = form.find(attrs={"name": field})
        if element is None:
            raise RuntimeError(f"Could not find expected SIDOT reset field: {field}")
        payload.append((field, element.get("value", "")))

    payload.append(("contrasenaNew", new_password))
    payload.append(("contrasenaRepeat", new_password))
    for value in collect_multiple_select_values(
        form,
        "hospitalesProcuramientoIds",
        "struts.hiddenHospitalesProcuramientoIds",
    ):
        payload.append(("hospitalesProcuramientoIds", value))
    for value in collect_multiple_select_values(
        form,
        "hospitalesTrasplantesIds",
        "struts.hiddenHospitalesTrasplantesIds",
    ):
        payload.append(("hospitalesTrasplantesIds", value))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="SIDOT Mesa Ayuda: reset password from a GitLab issue and close it.")
    parser.add_argument("--project-root", default=str(Path.cwd().resolve()))
    parser.add_argument("--issue-iid", required=True)
    parser.add_argument("--solicitante-nombre", default="")
    parser.add_argument("--sexo", default="")
    parser.add_argument("--sidot-user-query", default="")
    parser.add_argument("--skip-start-note", action="store_true")
    parser.add_argument("--skip-close", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    env_path = project_root / ".env"
    env_values = load_env_file(env_path)
    gitlab = GitLabClient.from_project_root(project_root)
    sidot = SidotClient.from_project_root(project_root)
    sidot.login()

    env_project = env_get("GITLAB_PROJECT_ID", env_values, env_path).strip()

    issue_data = gitlab.get(f"/projects/{quote(env_project, safe='')}/issues/{args.issue_iid}")
    description = issue_data.get("description") or ""
    sidot_user_query = (
        args.sidot_user_query.strip()
        or parse_issue_username(description)
        or parse_issue_email(description)
        or parse_issue_full_name(description)
    )
    if not sidot_user_query:
        raise RuntimeError("Could not determine SIDOT user query. Pass --sidot-user-query explicitly.")

    solicitante_nombre = args.solicitante_nombre.strip() or parse_issue_full_name(description) or sidot_user_query
    saludo = build_saludo(solicitante_nombre or "", args.sexo.strip() or None)

    start_note = None
    if not args.skip_start_note and "Estado: En proceso" not in (issue_data.get("labels") or []):
        note_start = (
            f"{saludo},\n\n"
            "Su solicitud está siendo tramitada, se ha solicitado la autorización al equipo que administra la plataforma SIDOT, "
            "teniendo su aprobación procederemos a generar una nueva clave y se la enviaremos por este mismo medio.\n\n"
            "Tenga en cuenta que el proceso puede demorarse hasta 24hs.\n\n"
            "Atte,\n\n"
            "Equipo Mesa de Ayuda SIDOT"
        )
        start_note = gitlab.post(f"/projects/{quote(env_project, safe='')}/issues/{args.issue_iid}/notes", form={"body": note_start})
        gitlab.put(f"/projects/{quote(env_project, safe='')}/issues/{args.issue_iid}", form={"add_labels": "Estado: En proceso"})

    search_resp = sidot.get(f"/pref/usuario/?busqueda.query={quote(sidot_user_query, safe='')}")
    search_resp.raise_for_status()
    edit_links = parse_user_edit_links(search_resp.text)
    if not edit_links:
        raise RuntimeError(f"No SIDOT user edit link found for query: {sidot_user_query}")
    if len(edit_links) > 1:
        raise RuntimeError(f"SIDOT query is ambiguous; found {len(edit_links)} users for query: {sidot_user_query}")
    edit_link = edit_links[0]

    edit_url = urljoin(f"{sidot.base_url}/", edit_link.lstrip("/"))
    edit_response = sidot.get(edit_url)
    edit_response.raise_for_status()

    soup = BeautifulSoup(edit_response.text, "html.parser")
    form = soup.find("form")
    if form is None:
        raise RuntimeError("Could not find edit form in SIDOT user page.")

    action = form.get("action") or edit_url
    post_url = urljoin(edit_url, action)

    new_password = generate_password(20)
    payload = collect_password_reset_payload(form, new_password)
    password_fields = ["contrasenaNew"]
    confirmation_fields = ["contrasenaRepeat"]

    save_response = sidot.session.post(post_url, data=payload, headers={"Referer": edit_url}, timeout=30)
    save_response.raise_for_status()

    note_end = (
        f"{saludo},\n\n"
        "A continuación su nueva clave de acceso temporal, se recomienda cambiar la misma ni bien logre tener acceso a la plataforma.\n\n"
        f"{new_password}\n\n"
        "Atte,\n\n"
        "Equipo Mesa de Ayuda SIDOT"
    )
    end_note = gitlab.post(f"/projects/{quote(env_project, safe='')}/issues/{args.issue_iid}/notes", form={"body": note_end})

    if not args.skip_close:
        gitlab.put(
            f"/projects/{quote(env_project, safe='')}/issues/{args.issue_iid}",
            form={"remove_labels": "Estado: En proceso", "add_labels": "Estado: Cerrado", "state_event": "close"},
        )

    print("Password reset workflow completed.")
    print(f"Issue IID: {args.issue_iid}")
    print(f"SIDOT query: {sidot_user_query}")
    print(f"SIDOT edit URL: {edit_url}")
    print(f"SIDOT password fields updated: {', '.join(password_fields)}")
    print(f"SIDOT password confirmation fields updated: {', '.join(confirmation_fields)}")
    print(f"GitLab start note id: {start_note.get('id') if start_note else '-'}")
    print(f"GitLab final note id: {end_note.get('id')}")
    print(f"Issue closed: {not args.skip_close}")


if __name__ == "__main__":
    main()
