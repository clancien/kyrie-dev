#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_ACTIVATE="$SCRIPT_DIR/.venv/bin/activate"
ENV_FILE="$SCRIPT_DIR/.env"
CACHE_STATE="$SCRIPT_DIR/cache/session_storage_state.json"

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

if [[ -z "${BANCHILE_RUT:-}" || -z "${BANCHILE_PASSWORD:-}" ]]; then
  echo "[ERROR] Faltan variables BANCHILE_RUT / BANCHILE_PASSWORD" >&2
  echo "Define variables de entorno o crea $ENV_FILE con esas claves." >&2
  exit 1
fi

is_cache_vigente() {
  python3 - "$CACHE_STATE" << 'PY'
import json, time, sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    raise SystemExit(1)

try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)

cookies = data.get("cookies", [])
if not isinstance(cookies, list) or not cookies:
    raise SystemExit(1)

now = int(time.time())
for c in cookies:
    exp = c.get("expires", -1)
    # -1 suele representar cookie de sesión (vigente mientras backend la acepte).
    if exp == -1:
        raise SystemExit(0)
    try:
        exp_i = int(exp)
    except Exception:
        continue
    # margen de 5 minutos
    if exp_i > now + 300:
        raise SystemExit(0)

raise SystemExit(1)
PY
}

run_with_cache() {
  python3 "$SCRIPT_DIR/bancochile_server_api.py" --max-pages 2 --print-json
}

if is_cache_vigente; then
  echo "[INFO] Sesion en cache detectada. Intentando reutilizar..." >&2
  if run_with_cache; then
    echo "[OK] Ejecucion completada reutilizando cache." >&2
    exit 0
  fi
  echo "[WARN] Cache presente pero no valida en backend. Se renovara con login UI." >&2
else
  echo "[INFO] No hay cache vigente. Se requiere login UI." >&2
fi

python3 "$SCRIPT_DIR/bancochile_login_ui.py" \
  --browser chromium \
  --storage-state-out "$SCRIPT_DIR/cache/session_storage_state.json"
run_with_cache
