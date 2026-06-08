#!/usr/bin/env python3
import os
from pathlib import Path

import requests


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


class TrelloClient:
    def __init__(self, key: str, token: str, base_url: str = "https://api.trello.com/1"):
        self.key = key
        self.token = token
        self.base_url = base_url.rstrip("/")

    @classmethod
    def from_project_root(cls, project_root: Path) -> "TrelloClient":
        env_path = project_root / ".env"
        env_values = load_env_file(env_path)
        key = env_get("TRELLO_KEY", env_values, env_path)
        token = env_get("TRELLO_TOKEN", env_values, env_path)
        return cls(key=key, token=token)

    def get(self, path: str, **params):
        url = f"{self.base_url}/{path.lstrip('/')}"
        query = {"key": self.key, "token": self.token, **params}
        response = requests.get(url, params=query, timeout=30)
        response.raise_for_status()
        return response.json()

    def download_card_attachment(self, card_id: str, attachment_id: str, filename: str):
        url = (
            f"https://trello.com/1/cards/{card_id}/attachments/{attachment_id}"
            f"/download/{filename}"
        )
        headers = {
            "Authorization": (
                f'OAuth oauth_consumer_key="{self.key}", oauth_token="{self.token}"'
            )
        }
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        return response
