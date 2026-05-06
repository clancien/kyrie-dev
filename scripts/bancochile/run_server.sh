#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_ACTIVATE="$SCRIPT_DIR/.venv/bin/activate"
ENV_FILE="$SCRIPT_DIR/.env"

if [[ ! -f "$VENV_ACTIVATE" ]]; then
  echo "[ERROR] No existe entorno virtual en $SCRIPT_DIR/.venv" >&2
  echo "Ejecuta: $SCRIPT_DIR/setup_env.sh" >&2
  exit 1
fi

source "$VENV_ACTIVATE"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

if ! python3 -c "import requests" >/dev/null 2>&1; then
  echo "[ERROR] Falta dependencia 'requests' en .venv" >&2
  echo "Ejecuta: source $VENV_ACTIVATE && pip install -r $SCRIPT_DIR/requirements.txt" >&2
  exit 1
fi

python3 "$SCRIPT_DIR/bancochile_server_api.py" --max-pages 2 --print-json
