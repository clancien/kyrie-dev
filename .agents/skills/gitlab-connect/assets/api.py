#!/usr/bin/env python3
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


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


class GitLabClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    @classmethod
    def from_project_root(cls, project_root: Path) -> "GitLabClient":
        env_path = project_root / ".env"
        env_values = load_env_file(env_path)
        base_url = env_get("GITLAB_BASE_URL", env_values, env_path)
        token = env_get("GITLAB_TOKEN", env_values, env_path)
        return cls(base_url=base_url, token=token)

    def _build_url(self, path: str, query: dict | None = None) -> str:
        url = f"{self.base_url}/api/v4{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        return url

    def request(self, method: str, path: str, query: dict | None = None, form: dict | None = None):
        url = self._build_url(path, query)
        data = None
        headers = {"PRIVATE-TOKEN": self.token}
        if form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=data, method=method.upper())
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read().decode("utf-8")
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"GitLab API error {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Cannot reach GitLab: {exc}") from exc

    def get(self, path: str, query: dict | None = None):
        return self.request("GET", path, query=query)

    def post(self, path: str, form: dict | None = None):
        return self.request("POST", path, form=form)

    def put(self, path: str, form: dict | None = None):
        return self.request("PUT", path, form=form)
