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


def cmd_branches(client: GitLabClient, project_id: str, search: str | None, per_page: int):
    data = client.list_project_branches(project_id, search=search, per_page=per_page)
    out = [
        {
            "name": b.get("name"),
            "default": b.get("default"),
            "merged": b.get("merged"),
            "protected": b.get("protected"),
            "committed_date": (b.get("commit") or {}).get("committed_date"),
            "author": (b.get("commit") or {}).get("author_name"),
            "short_id": (b.get("commit") or {}).get("short_id"),
            "title": (b.get("commit") or {}).get("title"),
            "web_url": b.get("web_url"),
        }
        for b in data
    ]
    out.sort(key=lambda b: b["committed_date"] or "", reverse=True)
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


def cmd_milestones_list(client: GitLabClient, project_id: str, state: str | None, title: str | None, search: str | None, per_page: int):
    query = {"per_page": per_page}
    if state:
        query["state"] = state
    if title:
        query["title"] = title
    if search:
        query["search"] = search
    data = client.list_project_milestones(project_id, query=query)
    out = [
        {
            "id": milestone.get("id"),
            "iid": milestone.get("iid"),
            "title": milestone.get("title"),
            "state": milestone.get("state"),
            "description": milestone.get("description"),
            "due_date": milestone.get("due_date"),
            "start_date": milestone.get("start_date"),
            "web_url": milestone.get("web_url"),
        }
        for milestone in data
    ]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_milestones_create(
    client: GitLabClient,
    project_id: str,
    title: str,
    description: str | None,
    due_date: str | None,
    start_date: str | None,
):
    data = client.create_project_milestone(
        project_id,
        title,
        description=description,
        due_date=due_date,
        start_date=start_date,
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_milestones_assign(client: GitLabClient, project_id: str, issue_iid: str, milestone_id: str):
    data = client.assign_issue_milestone(project_id, issue_iid, milestone_id)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="GitLab helper (auth via .env)")
    parser.add_argument("--project-root", default=str(Path.cwd().resolve()))
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ping", help="Validate token and show current user")

    p_projects = sub.add_parser("projects", help="List accessible projects")
    p_projects.add_argument("--search", default=None, help="Search project by name/path")
    p_projects.add_argument("--per-page", type=int, default=20)

    p_branches = sub.add_parser("branches", help="List repository branches for a project")
    p_branches.add_argument("--project-id", default=os.getenv("GITLAB_PROJECT_ID", ""))
    p_branches.add_argument("--search", default=None, help="Filter by branch name substring")
    p_branches.add_argument("--per-page", type=int, default=100)

    p_mrs = sub.add_parser("mrs", help="List merge requests for a project")
    p_mrs.add_argument("--project-id", default=os.getenv("GITLAB_PROJECT_ID", ""))
    p_mrs.add_argument("--state", choices=["opened", "closed", "locked", "merged", "all"], default="opened")
    p_mrs.add_argument("--per-page", type=int, default=20)

    p_issues = sub.add_parser("issues", help="List issues for a project")
    p_issues.add_argument("--project-id", default=os.getenv("GITLAB_PROJECT_ID", ""))
    p_issues.add_argument("--state", choices=["opened", "closed", "all"], default="opened")
    p_issues.add_argument("--per-page", type=int, default=20)

    p_milestones = sub.add_parser("milestones", help="List project milestones")
    p_milestones.add_argument("--project-id", default=os.getenv("GITLAB_PROJECT_ID", ""))
    p_milestones.add_argument("--state", choices=["active", "closed"], default=None)
    p_milestones.add_argument("--title", default=None)
    p_milestones.add_argument("--search", default=None)
    p_milestones.add_argument("--per-page", type=int, default=20)

    p_milestone_create = sub.add_parser("milestone-create", help="Create a project milestone")
    p_milestone_create.add_argument("--project-id", default=os.getenv("GITLAB_PROJECT_ID", ""))
    p_milestone_create.add_argument("--title", required=True)
    p_milestone_create.add_argument("--description", default=None)
    p_milestone_create.add_argument("--due-date", default=None)
    p_milestone_create.add_argument("--start-date", default=None)

    p_milestone_assign = sub.add_parser("milestone-assign", help="Assign a milestone to an issue")
    p_milestone_assign.add_argument("--project-id", default=os.getenv("GITLAB_PROJECT_ID", ""))
    p_milestone_assign.add_argument("--issue-iid", required=True)
    p_milestone_assign.add_argument("--milestone-id", required=True)

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
    elif args.cmd == "branches":
        project_id = args.project_id.strip()
        if not project_id:
            print("Missing project id. Set GITLAB_PROJECT_ID or pass --project-id", file=sys.stderr)
            sys.exit(2)
        cmd_branches(client, project_id, args.search, args.per_page)
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
    elif args.cmd == "milestones":
        project_id = args.project_id.strip()
        if not project_id:
            print("Missing project id. Set GITLAB_PROJECT_ID or pass --project-id", file=sys.stderr)
            sys.exit(2)
        cmd_milestones_list(client, project_id, args.state, args.title, args.search, args.per_page)
    elif args.cmd == "milestone-create":
        project_id = args.project_id.strip()
        if not project_id:
            print("Missing project id. Set GITLAB_PROJECT_ID or pass --project-id", file=sys.stderr)
            sys.exit(2)
        cmd_milestones_create(client, project_id, args.title, args.description, args.due_date, args.start_date)
    elif args.cmd == "milestone-assign":
        project_id = args.project_id.strip()
        if not project_id:
            print("Missing project id. Set GITLAB_PROJECT_ID or pass --project-id", file=sys.stderr)
            sys.exit(2)
        cmd_milestones_assign(client, project_id, args.issue_iid, args.milestone_id)


if __name__ == "__main__":
    main()
