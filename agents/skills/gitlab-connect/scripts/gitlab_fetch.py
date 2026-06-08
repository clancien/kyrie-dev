#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = CURRENT_DIR.parent / "assets"
if str(ASSETS_DIR) not in sys.path:
    sys.path.insert(0, str(ASSETS_DIR))

from api import GitLabClient  # noqa: E402


def cmd_ping(client: GitLabClient):
    data = client.get("/user")
    print(json.dumps({
        "ok": True,
        "id": data.get("id"),
        "name": data.get("name"),
        "username": data.get("username"),
    }, ensure_ascii=False, indent=2))


def cmd_projects(client: GitLabClient, search: str | None, per_page: int):
    query = {"membership": "true", "per_page": per_page, "simple": "true"}
    if search:
        query["search"] = search
    data = client.get("/projects", query=query)
    out = [
        {
            "id": p.get("id"),
            "path_with_namespace": p.get("path_with_namespace"),
            "default_branch": p.get("default_branch"),
            "web_url": p.get("web_url"),
        }
        for p in data
    ]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_mrs(client: GitLabClient, project_id: str, state: str, per_page: int):
    query = {"state": state, "per_page": per_page, "order_by": "updated_at", "sort": "desc"}
    from urllib.parse import quote

    path = f"/projects/{quote(project_id, safe='')}/merge_requests"
    data = client.get(path, query=query)
    out = [
        {
            "iid": mr.get("iid"),
            "title": mr.get("title"),
            "state": mr.get("state"),
            "author": (mr.get("author") or {}).get("username"),
            "updated_at": mr.get("updated_at"),
            "web_url": mr.get("web_url"),
        }
        for mr in data
    ]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_issues(client: GitLabClient, project_id: str, state: str, per_page: int):
    query = {"state": state, "per_page": per_page, "order_by": "updated_at", "sort": "desc"}
    from urllib.parse import quote

    path = f"/projects/{quote(project_id, safe='')}/issues"
    data = client.get(path, query=query)
    out = [
        {
            "iid": issue.get("iid"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "author": (issue.get("author") or {}).get("username"),
            "updated_at": issue.get("updated_at"),
            "labels": issue.get("labels", []),
            "web_url": issue.get("web_url"),
        }
        for issue in data
    ]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="GitLab helper (auth via .env)")
    parser.add_argument("--project-root", default=str(Path.cwd().resolve()))
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ping", help="Validate token and show current user")

    p_projects = sub.add_parser("projects", help="List accessible projects")
    p_projects.add_argument("--search", default=None, help="Search project by name/path")
    p_projects.add_argument("--per-page", type=int, default=20)

    p_mrs = sub.add_parser("mrs", help="List merge requests for a project")
    p_mrs.add_argument("--project-id", default=os.getenv("GITLAB_PROJECT_ID", ""))
    p_mrs.add_argument("--state", choices=["opened", "closed", "locked", "merged", "all"], default="opened")
    p_mrs.add_argument("--per-page", type=int, default=20)

    p_issues = sub.add_parser("issues", help="List issues for a project")
    p_issues.add_argument("--project-id", default=os.getenv("GITLAB_PROJECT_ID", ""))
    p_issues.add_argument("--state", choices=["opened", "closed", "all"], default="opened")
    p_issues.add_argument("--per-page", type=int, default=20)

    args = parser.parse_args()

    try:
        client = GitLabClient.from_project_root(Path(args.project_root).resolve())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    if args.cmd == "ping":
        cmd_ping(client)
    elif args.cmd == "projects":
        cmd_projects(client, args.search, args.per_page)
    elif args.cmd == "mrs":
        project_id = args.project_id.strip()
        if not project_id:
            print("Missing project id. Set GITLAB_PROJECT_ID or pass --project-id", file=sys.stderr)
            sys.exit(2)
        cmd_mrs(client, project_id, args.state, args.per_page)
    elif args.cmd == "issues":
        project_id = args.project_id.strip()
        if not project_id:
            print("Missing project id. Set GITLAB_PROJECT_ID or pass --project-id", file=sys.stderr)
            sys.exit(2)
        cmd_issues(client, project_id, args.state, args.per_page)


if __name__ == "__main__":
    main()
