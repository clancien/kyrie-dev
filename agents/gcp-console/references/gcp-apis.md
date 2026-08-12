# GCP Console API Map

Use the local `.google-cloud-service-key.json` file to mint a short-lived OAuth access token, then call read-only Google Cloud REST APIs.

## What to query

| Question | API | Notes |
| --- | --- | --- |
| What project is this key tied to? | Cloud Resource Manager `projects.get` | Use the project id from the key file or `--project-id`. |
| What APIs are enabled? | Service Usage `services.list` | List enabled services for the project number, not the project id. |
| Who has access? | Cloud Resource Manager `projects.getIamPolicy` | Read-only policy inspection only. |
| Which service accounts exist? | IAM `projects.serviceAccounts.list` | Returns service account metadata only. |
| Which secrets exist? | Secret Manager `projects.secrets.list` | Returns metadata only, not secret values. |
| Which Cloud Run services exist? | Cloud Run `projects.locations.services.list` | Requires a concrete region; the v2 API does not accept `-` as the wildcard location. |

## Commands

```bash
python3 .agents/skills/gcp-console/scripts/gcp_console.py token
python3 .agents/skills/gcp-console/scripts/gcp_console.py project
python3 .agents/skills/gcp-console/scripts/gcp_console.py apis
python3 .agents/skills/gcp-console/scripts/gcp_console.py iam
python3 .agents/skills/gcp-console/scripts/gcp_console.py service-accounts
python3 .agents/skills/gcp-console/scripts/gcp_console.py secrets
python3 .agents/skills/gcp-console/scripts/gcp_console.py cloud-run --region us-central1
```

## Guardrails

- Do not use this helper to mutate Google Cloud.
- Do not print the private key contents.
- Print access tokens only when the user explicitly needs the token itself.
- Prefer one command per diagnostic question.
