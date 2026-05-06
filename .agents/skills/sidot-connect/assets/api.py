#!/usr/bin/env python3
import os
import re
from pathlib import Path

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:138.0) "
        "Gecko/20100101 Firefox/138.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
}


def load_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_get(key: str, env_values: dict[str, str], env_path: Path, required: bool = True) -> str:
    value = env_values.get(key) or os.environ.get(key, "")
    if required and not value:
        raise RuntimeError(f"Missing required variable {key} in {env_path}")
    return value


def extract_csrf_token(html_text: str) -> str:
    match = re.search(r'name="__csrftoken"\s+value="([^"]+)"', html_text)
    if not match:
        raise RuntimeError("Could not find __csrftoken in SIDOT login page.")
    return match.group(1)


class SidotClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._authenticated = False

    @classmethod
    def from_project_root(cls, project_root: Path) -> "SidotClient":
        env_path = project_root / ".env"
        env_values = load_env_file(env_path)
        base_url = env_get("SIDOT_URL", env_values, env_path).rstrip("/")
        username = env_get("SIDOT_USER", env_values, env_path)
        password = env_get("SIDOT_PWD", env_values, env_path)
        return cls(base_url=base_url, username=username, password=password)

    def login(self) -> dict:
        login_page = f"{self.base_url}/login"
        logon_post = f"{self.base_url}/logon"

        login_response = self.session.get(login_page, timeout=30)
        login_response.raise_for_status()
        csrf_token = extract_csrf_token(login_response.text)

        payload = {
            "__csrftoken": csrf_token,
            "username": self.username,
            "password": self.password,
        }
        post_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.base_url,
            "Referer": login_page,
        }
        auth_response = self.session.post(logon_post, data=payload, headers=post_headers, timeout=30)
        auth_response.raise_for_status()

        authenticated = (
            "JSESSIONID" in self.session.cookies.get_dict()
            and "/login" not in auth_response.url.rstrip("/")
        )
        if not authenticated:
            raise RuntimeError("SIDOT login failed. Check SIDOT_USER/SIDOT_PWD and CSRF flow.")
        self._authenticated = True
        return {
            "username": self.username,
            "base_url": self.base_url,
            "csrf_token_used": csrf_token,
            "auth_url": auth_response.url,
            "status_code": auth_response.status_code,
            "authenticated": authenticated,
            "login_page_html": login_response.text,
            "auth_response_html": auth_response.text,
        }

    def ensure_login(self) -> None:
        if not self._authenticated:
            self.login()

    def get(self, path_or_url: str, **kwargs):
        self.ensure_login()
        if path_or_url.startswith("http"):
            url = path_or_url
        else:
            url = f"{self.base_url}/{path_or_url.lstrip('/')}"
        return self.session.get(url, timeout=30, **kwargs)
