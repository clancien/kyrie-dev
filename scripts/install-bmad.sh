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

MODULES="core,bmm,bmad-loop,tea"

ask_module() {
  local question="$1"
  local module="$2"
  local answer

  while true; do
    if ! read -r -p "$question [s/N]: " answer; then
      return 0
    fi
    case "$answer" in
      s|S|si|Si|SI|sí|Sí|SÍ|y|Y|yes|Yes|YES)
        MODULES+=",$module"
        return 0
        ;;
      n|N|no|No|NO|"")
        return 0
        ;;
      *)
        echo "Responde s (sí) o n (no)."
        ;;
    esac
  done
}

ask_module "¿Requieres creación y modificación de agentes o flujos de trabajo propios?" bmb
ask_module "¿Requieres ideación de negocio, brainstorming y Design Thinking, como al empezar un proyecto por ejemplo?" cis

npx bmad-method install \
  --directory "$TARGET_DIRECTORY" \
  --modules "$MODULES" \
  --tools claude-code,codex \
  --user-name "$USER_NAME" \
  --communication-language Spanish \
  --document-output-language Spanish \
  --output-folder docs \
  --set core.project_name="$PROJECT_NAME" \
  --all-stable \
  --yes
