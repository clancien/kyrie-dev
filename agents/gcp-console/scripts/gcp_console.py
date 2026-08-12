#!/usr/bin/env python3
"""Read-only Google Cloud console inspector for local service account keys."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_KEY_NAME = ".google-cloud-service-key.json"
DEFAULT_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"


class GcpConsoleError(RuntimeError):
    pass


@dataclass(frozen=True)
class ServiceAccountKey:
    project_id: str
    client_email: str
    private_key: str
    token_uri: str
    private_key_id: str | None = None


def find_key_file(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.exists():
            raise GcpConsoleError(f"Key file not found: {path}")
        return path

    current = Path.cwd().resolve()
    for directory in (current, *current.parents):
        candidate = directory / DEFAULT_KEY_NAME
        if candidate.exists():
            return candidate

    raise GcpConsoleError(
        f"Could not find {DEFAULT_KEY_NAME} from {current}. Use --key-file to override."
    )


def load_service_account_key(path: Path) -> ServiceAccountKey:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GcpConsoleError(f"Invalid JSON in key file {path}: {exc}") from exc

    required = ["project_id", "client_email", "private_key"]
    missing = [field for field in required if not raw.get(field)]
    if missing:
        raise GcpConsoleError(
            f"Key file {path} is missing required field(s): {', '.join(missing)}"
        )

    token_uri = raw.get("token_uri") or DEFAULT_TOKEN_URI

    return ServiceAccountKey(
        project_id=str(raw["project_id"]),
        client_email=str(raw["client_email"]),
        private_key=str(raw["private_key"]),
        token_uri=str(token_uri),
        private_key_id=raw.get("private_key_id"),
    )


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def sign_rs256(message: bytes, private_key_pem: str) -> bytes:
    openssl = shutil.which("openssl")
    if not openssl:
        raise GcpConsoleError("openssl is required to sign service-account JWTs")

    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = Path(tmpdir) / "private_key.pem"
        message_path = Path(tmpdir) / "jwt_input.bin"
        signature_path = Path(tmpdir) / "jwt_signature.bin"
        key_path.write_text(private_key_pem, encoding="utf-8")
        message_path.write_bytes(message)

        cmd = [
            openssl,
            "dgst",
            "-sha256",
            "-sign",
            str(key_path),
            "-out",
            str(signature_path),
            str(message_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise GcpConsoleError(
                f"openssl signing failed: {result.stderr.strip() or result.stdout.strip()}"
            )
        return signature_path.read_bytes()


def build_jwt_assertion(key: ServiceAccountKey, scope: str = DEFAULT_SCOPE) -> str:
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    if key.private_key_id:
        header["kid"] = key.private_key_id

    claims = {
        "iss": key.client_email,
        "scope": scope,
        "aud": key.token_uri,
        "iat": now,
        "exp": now + 3600,
    }

    encoded_header = b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    encoded_claims = b64url(json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_claims}".encode("ascii")
    signature = sign_rs256(signing_input, key.private_key)
    return f"{encoded_header}.{encoded_claims}.{b64url(signature)}"


def http_request(url: str, method: str = "GET", headers: dict[str, str] | None = None, body: bytes | None = None) -> dict[str, Any]:
    request = Request(url, method=method, headers=headers or {}, data=body)
    try:
        with urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
            if not payload:
                return {}
            return json.loads(payload)
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise GcpConsoleError(
            f"HTTP {exc.code} for {method} {url}: {body_text or exc.reason}"
        ) from exc
    except URLError as exc:
        raise GcpConsoleError(f"Network error for {method} {url}: {exc.reason}") from exc


def get_access_token(key: ServiceAccountKey, scope: str = DEFAULT_SCOPE) -> dict[str, Any]:
    assertion = build_jwt_assertion(key, scope=scope)
    form = urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    return http_request(key.token_uri, method="POST", headers=headers, body=form)


def authorized_request(access_token: str, url: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    payload = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode("utf-8")
    return http_request(url, method=method, headers=headers, body=payload)


def project_resource_name(project_id: str) -> str:
    return f"projects/{project_id}"


def load_project(access_token: str, project_id: str) -> dict[str, Any]:
    return authorized_request(
        access_token,
        f"https://cloudresourcemanager.googleapis.com/v3/{project_resource_name(project_id)}",
    )


def get_project_number(project: dict[str, Any]) -> str:
    project_number = project.get("projectNumber")
    if not project_number:
        raise GcpConsoleError("Project metadata does not include projectNumber")
    return str(project_number)


def list_paginated(
    access_token: str,
    url: str,
    item_keys: tuple[str, ...],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        request_url = url
        if page_token:
            separator = "&" if "?" in request_url else "?"
            request_url = f"{request_url}{separator}pageToken={page_token}"

        response = authorized_request(access_token, request_url)
        batch: list[dict[str, Any]] = []
        for key in item_keys:
            value = response.get(key)
            if isinstance(value, list):
                batch = value
                break
        items.extend(batch)
        page_token = response.get("nextPageToken")
        if not page_token:
            return items


def enabled_apis(access_token: str, project_number: str) -> list[dict[str, Any]]:
    url = (
        "https://serviceusage.googleapis.com/v1/"
        f"projects/{project_number}/services?filter=state:ENABLED&pageSize=200"
    )
    return list_paginated(access_token, url, ("services",))


def list_service_accounts(access_token: str, project_id: str) -> list[dict[str, Any]]:
    url = (
        "https://iam.googleapis.com/v1/"
        f"{project_resource_name(project_id)}/serviceAccounts?pageSize=200"
    )
    return list_paginated(access_token, url, ("accounts", "serviceAccounts"))


def list_secrets(access_token: str, project_id: str) -> list[dict[str, Any]]:
    url = (
        "https://secretmanager.googleapis.com/v1/"
        f"{project_resource_name(project_id)}/secrets?pageSize=200"
    )
    return list_paginated(access_token, url, ("secrets",))


def list_cloud_run_services(access_token: str, project_id: str, region: str) -> list[dict[str, Any]]:
    url = (
        "https://run.googleapis.com/v2/"
        f"projects/{project_id}/locations/{region}/services?pageSize=100"
    )
    return list_paginated(access_token, url, ("services",))


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def build_output(query: str, project_id: str, payload: Any, **extra: Any) -> dict[str, Any]:
    output = {
        "query": query,
        "project_id": project_id,
        "payload": payload,
    }
    output.update(extra)
    return output


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gcp_console.py",
        description="Read-only Google Cloud inspector using a local service account key.",
    )
    parser.add_argument(
        "--key-file",
        help=f"Path to the service account JSON key. Defaults to {DEFAULT_KEY_NAME} discovered from the current directory upward.",
    )
    parser.add_argument(
        "--project-id",
        help="Override the project id from the service account key.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("token", help="Print an OAuth token response.")
    subparsers.add_parser("project", help="Fetch project metadata.")
    subparsers.add_parser("apis", help="List enabled APIs for the project.")
    subparsers.add_parser("iam", help="Fetch the project IAM policy.")
    subparsers.add_parser("service-accounts", help="List project service accounts.")
    subparsers.add_parser("secrets", help="List project Secret Manager secrets.")

    cloud_run = subparsers.add_parser("cloud-run", help="List Cloud Run services in a region.")
    cloud_run.add_argument(
        "--region",
        default=os.environ.get("GOOGLE_CLOUD_RUN_REGION"),
        help="Cloud Run region. If omitted, uses GOOGLE_CLOUD_RUN_REGION.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        key_path = find_key_file(args.key_file)
        key = load_service_account_key(key_path)
        project_id = args.project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or key.project_id
        if not project_id:
            raise GcpConsoleError("Missing project id. Provide --project-id or set GOOGLE_CLOUD_PROJECT.")

        if args.command == "token":
            print_json(
                build_output(
                    "token",
                    project_id,
                    get_access_token(key),
                    key_file=str(key_path),
                    token_uri=key.token_uri,
                )
            )
            return 0

        access_token = get_access_token(key).get("access_token")
        if not access_token:
            raise GcpConsoleError("Token endpoint response did not include access_token")

        if args.command == "project":
            project = load_project(access_token, project_id)
            print_json(
                build_output(
                    "project",
                    project_id,
                    project,
                    project_number=get_project_number(project),
                )
            )
            return 0

        project = load_project(access_token, project_id)
        project_number = get_project_number(project)

        if args.command == "apis":
            items = enabled_apis(access_token, project_number)
            print_json(
                build_output(
                    "apis",
                    project_id,
                    items,
                    project_number=project_number,
                    count=len(items),
                )
            )
            return 0

        if args.command == "iam":
            policy = authorized_request(
                access_token,
                f"https://cloudresourcemanager.googleapis.com/v3/{project_resource_name(project_id)}:getIamPolicy",
                method="POST",
                body={},
            )
            print_json(build_output("iam", project_id, policy, project_number=project_number))
            return 0

        if args.command == "service-accounts":
            items = list_service_accounts(access_token, project_id)
            print_json(
                build_output(
                    "service-accounts",
                    project_id,
                    items,
                    project_number=project_number,
                    count=len(items),
                )
            )
            return 0

        if args.command == "secrets":
            items = list_secrets(access_token, project_id)
            print_json(
                build_output(
                    "secrets",
                    project_id,
                    items,
                    project_number=project_number,
                    count=len(items),
                )
            )
            return 0

        if args.command == "cloud-run":
            if not args.region:
                raise GcpConsoleError(
                    "cloud-run requires --region or GOOGLE_CLOUD_RUN_REGION."
                )
            items = list_cloud_run_services(access_token, project_id, args.region)
            print_json(
                build_output(
                    "cloud-run",
                    project_id,
                    items,
                    project_number=project_number,
                    region=args.region,
                    count=len(items),
                )
            )
            return 0

        raise GcpConsoleError(f"Unknown command: {args.command}")

    except GcpConsoleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
