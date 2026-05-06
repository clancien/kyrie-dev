#!/usr/bin/env python3
import json
from pathlib import Path

from api import SidotClient, load_env_file, env_get, extract_csrf_token


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def session_cookies_to_json(session) -> list[dict]:
    cookies: list[dict] = []
    for cookie in session.cookies:
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
            }
        )
    return cookies


def build_authenticated_session(project_root: Path):
    client = SidotClient.from_project_root(project_root)
    metadata = client.login()
    metadata["cookies"] = session_cookies_to_json(client.session)
    return client.session, metadata


def write_json(path: Path, payload: object) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


__all__ = [
    "SidotClient",
    "build_authenticated_session",
    "ensure_dir",
    "write_json",
    "load_env_file",
    "env_get",
    "extract_csrf_token",
]
