#!/usr/bin/env python3
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import quote


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

    def list_project_milestones(self, project_id: str, query: dict | None = None):
        path = f"/projects/{quote(project_id, safe='')}/milestones"
        return self.get(path, query=query)

    def find_project_milestone(self, project_id: str, title: str):
        milestones = self.list_project_milestones(project_id, query={"title": title})
        if isinstance(milestones, dict):
            return milestones if milestones.get("title") == title else None

        matches = [milestone for milestone in milestones if milestone.get("title") == title]
        if not matches:
            return None
        if len(matches) > 1:
            raise RuntimeError(f"Ambiguous GitLab milestone title: {title}")
        return matches[0]

    def create_project_milestone(
        self,
        project_id: str,
        title: str,
        description: str | None = None,
        due_date: str | None = None,
        start_date: str | None = None,
    ):
        path = f"/projects/{quote(project_id, safe='')}/milestones"
        form: dict[str, str] = {"title": title}
        if description:
            form["description"] = description
        if due_date:
            form["due_date"] = due_date
        if start_date:
            form["start_date"] = start_date
        return self.post(path, form=form)

    def assign_issue_milestone(self, project_id: str, issue_iid: str, milestone_id: str | int):
        path = f"/projects/{quote(project_id, safe='')}/issues/{issue_iid}"
        return self.put(path, form={"milestone_id": str(milestone_id)})
