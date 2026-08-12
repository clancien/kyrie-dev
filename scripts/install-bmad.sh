#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install-bmad.sh [-u user_name] [-d directory] [-p project_name]

Options:
  -u, --user-name      User passed to bmad-method. Defaults to the active session user.
  -d, --directory      Target directory. Defaults to the directory where the script is invoked.
  -p, --project-name   Value for core.project_name. Defaults to the last path segment of the directory.
  -h, --help           Show this help message.
EOF
}

USER_NAME="$(whoami)"
TARGET_DIRECTORY="$(pwd)"
PROJECT_NAME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -u|--user-name)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for $1" >&2
        exit 1
      fi
      USER_NAME="$2"
      shift 2
      ;;
    -d|--directory)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for $1" >&2
        exit 1
      fi
      TARGET_DIRECTORY="$2"
      shift 2
      ;;
    -p|--project-name)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for $1" >&2
        exit 1
      fi
      PROJECT_NAME="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$PROJECT_NAME" ]]; then
  PROJECT_NAME="$(basename "$TARGET_DIRECTORY")"
fi

npx bmad-method install \
  --directory "$TARGET_DIRECTORY" \
  --modules bmm,core,tea,bmb,bmad-loop,cis,wds \
  --tools claude-code,codex \
  --user-name "$USER_NAME" \
  --communication-language Spanish \
  --document-output-language Spanish \
  --output-folder doc \
  --set core.project_name="$PROJECT_NAME" \
  --all-stable \
  --yes
