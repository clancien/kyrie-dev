#!/usr/bin/env python3
import os
from pathlib import Path
from urllib.parse import quote

import requests


TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


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


class GmailOAuthClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @classmethod
    def from_project_root(cls, project_root: Path) -> "GmailOAuthClient":
        env_path = project_root / ".env"
        env_values = load_env_file(env_path)
        client_id = env_get("GMAIL_CLIENT_ID", env_values, env_path)
        client_secret = env_get("GMAIL_CLIENT_SECRET", env_values, env_path)
        redirect_uri = env_get("GMAIL_REDIRECT_URI", env_values, env_path, required=False) or "http://localhost:8080"
        return cls(client_id, client_secret, redirect_uri)

    def exchange_code(self, code: str) -> dict:
        response = requests.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


class GmailApiClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str, user_id: str = "me"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.user_id = user_id

    @classmethod
    def from_project_root(cls, project_root: Path) -> "GmailApiClient":
        env_path = project_root / ".env"
        env_values = load_env_file(env_path)
        client_id = env_get("GMAIL_CLIENT_ID", env_values, env_path)
        client_secret = env_get("GMAIL_CLIENT_SECRET", env_values, env_path)
        refresh_token = env_get("GMAIL_REFRESH_TOKEN", env_values, env_path)
        user_id = env_get("GMAIL_USER", env_values, env_path, required=False) or "me"
        return cls(client_id, client_secret, refresh_token, user_id)

    def get_access_token(self) -> str:
        response = requests.post(
            TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        response.raise_for_status()
        token = response.json().get("access_token", "")
        if not token:
            raise RuntimeError("Google token endpoint did not return access_token")
        return token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.get_access_token()}"}

    def list_messages(self, query: str, max_results: int) -> dict:
        url = f"{GMAIL_API_BASE}/{quote(self.user_id, safe='')}/messages"
        params: dict[str, object] = {"maxResults": max_results}
        if query:
            params["q"] = query
        response = requests.get(url, headers=self._headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_message_metadata(self, msg_id: str) -> dict:
        url = f"{GMAIL_API_BASE}/{quote(self.user_id, safe='')}/messages/{msg_id}"
        response = requests.get(url, headers=self._headers(), params={"format": "metadata"}, timeout=30)
        response.raise_for_status()
        return response.json()

    def create_draft(self, raw_message: str) -> dict:
        url = f"{GMAIL_API_BASE}/{quote(self.user_id, safe='')}/drafts"
        response = requests.post(
            url,
            headers={**self._headers(), "Content-Type": "application/json"},
            json={"message": {"raw": raw_message}},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
