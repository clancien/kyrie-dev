---
name: gcp-console
description: Consult Google Cloud project metadata, enabled APIs, IAM policy, service accounts, Secret Manager, and Cloud Run using the local `.google-cloud-service-key.json` service account key. Use when you need to inspect or diagnose GCP configuration from this repo without making changes.
---

# GCP Console

## Use This Skill

- Use this skill when you need to inspect Google Cloud from this repository with the local service account key at `.google-cloud-service-key.json`.
- Use it for read-only diagnosis of project metadata, enabled APIs, IAM policy, service accounts, Secret Manager secrets, and Cloud Run services.

## Workflow

1. Resolve the key file with `scripts/gcp_console.py`. The helper searches from the current directory upward until it finds `.google-cloud-service-key.json`.
2. Run `token` first if you need to confirm the key can mint an OAuth token.
3. Use the narrowest read-only command that answers the question.

## Commands

- `project`: show project metadata and derive the project number.
- `token`: print the OAuth token response for the service account key.
- `apis`: list enabled Google Cloud APIs for the project.
- `iam`: fetch the project IAM policy.
- `service-accounts`: list service accounts in the project.
- `secrets`: list Secret Manager secret metadata.
- `cloud-run --region <region>`: list Cloud Run services in one region.

## Guardrails

- Do not mutate Google Cloud from this skill.
- Do not enable or disable APIs, change IAM, create secrets, create keys, or deploy workloads.
- Do not print private key material.
- Print access tokens only when the user explicitly needs the token value.
- Prefer the project id inside `.google-cloud-service-key.json`; override it only when intentionally inspecting a different project.

## References

- See [references/gcp-apis.md](references/gcp-apis.md) for the API map and read-only scope.
- See [scripts/gcp_console.py](scripts/gcp_console.py) for the executable helper.
