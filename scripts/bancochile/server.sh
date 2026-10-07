#!/usr/bin/env bash
# Control independiente del panel: Python local o Docker Compose.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER="$SCRIPT_DIR/bancochile_web_server.py"
PYTHON="$SCRIPT_DIR/.venv/bin/python"
UNIT="bancochile-panel.service"
RUNTIME="$SCRIPT_DIR/cache/web-server"
PID_FILE="$RUNTIME/server.pid"
LOG_FILE="$RUNTIME/server.log"

usage() {
  echo "Uso: $0 up [local|docker] | down [local|docker|all] | restart [local|docker] | status | logs [local|docker]"
  echo "Por defecto: up/restart/logs local; down detiene ambos. Panel: http://localhost:8030"
}

systemd_available() {
  command -v systemctl >/dev/null && command -v systemd-run >/dev/null && systemctl --user show-environment >/dev/null 2>&1
}

unit_active() {
  systemd_available && systemctl --user is-active --quiet "$UNIT"
}

pid_active() {
  [[ -f "$PID_FILE" ]] || return 1
  local server_pid
  read -r server_pid < "$PID_FILE"
  [[ "$server_pid" =~ ^[0-9]+$ && -r "/proc/$server_pid/cmdline" ]] || return 1
  # Evita detener otro proceso si Linux reutilizó el PID.
  tr '\0' '\n' < "/proc/$server_pid/cmdline" | grep -Fxq -- "$SERVER"
}

compose() {
  docker compose --project-directory "$SCRIPT_DIR" -f "$SCRIPT_DIR/docker-compose.yml" "$@"
}

docker_available() {
  command -v docker >/dev/null && docker info >/dev/null 2>&1 && docker compose version >/dev/null 2>&1
}

stop_local() {
  if unit_active; then
    systemctl --user stop "$UNIT"
  fi
  if pid_active; then
    local server_pid
    read -r server_pid < "$PID_FILE"
    kill "$server_pid"
    for _ in {1..50}; do
      pid_active || break
      sleep 0.1
    done
    if pid_active; then
      echo "[ERROR] El proceso local aún no terminó." >&2
      return 1
    fi
  fi
  echo "[OK] Servidor local detenido."
}

stop_docker() {
  if docker_available; then
    compose down
    echo "[OK] Docker detenido; datos y sesión conservados."
  elif command -v docker >/dev/null; then
    echo "[ERROR] Docker está instalado pero no está disponible; no se pudo ejecutar down." >&2
    return 1
  else
    echo "[INFO] Docker no está instalado."
  fi
}

wait_local() {
  "$PYTHON" - <<'PY'
import time
from urllib.request import urlopen
for _ in range(50):
    try:
        with urlopen('http://localhost:8030/api/update', timeout=0.5) as response:
            if response.status == 200:
                break
    except Exception:
        time.sleep(0.2)
else:
    raise SystemExit('El servidor no respondió. Consulta server.sh logs local.')
PY
}

start_local() {
  if unit_active || pid_active; then
    echo "[OK] El servidor local ya está activo: http://localhost:8030"
    return
  fi
  if [[ ! -x "$PYTHON" ]]; then
    echo "[ERROR] Falta el entorno Python. Ejecuta: bash $SCRIPT_DIR/setup_env.sh" >&2
    return 1
  fi
  "$PYTHON" -c 'import requests, dotenv, playwright' || return 1
  # Detener el contenedor del panel antes de ocupar el mismo puerto.
  if docker_available; then compose stop web; fi
  if systemd_available; then
    systemctl --user reset-failed "$UNIT" >/dev/null 2>&1 || true
    local env_args=()
    [[ -z "${DISPLAY:-}" ]] || env_args+=("--setenv=DISPLAY=$DISPLAY")
    [[ -z "${XAUTHORITY:-}" ]] || env_args+=("--setenv=XAUTHORITY=$XAUTHORITY")
    systemd-run --user --unit="$UNIT" --property=Restart=on-failure \
      --working-directory="$SCRIPT_DIR" "${env_args[@]}" "$PYTHON" "$SERVER" --port 8030
  else
    nohup "$PYTHON" "$SERVER" --port 8030 >> "$LOG_FILE" 2>&1 < /dev/null 9>&- &
    echo "$!" > "$PID_FILE"
  fi
  wait_local
  echo "[OK] Panel iniciado: http://localhost:8030"
}

start_docker() {
  if ! docker_available; then
    echo "[ERROR] Docker Compose no está disponible." >&2
    return 1
  fi
  # Construir primero: un fallo de espacio no interrumpe el servidor local.
  compose build
  local restore_local=false
  if unit_active || pid_active; then restore_local=true; fi
  stop_local
  if ! compose up -d --no-build; then
    echo "[ERROR] Docker no pudo iniciar el panel." >&2
    if "$restore_local"; then start_local; fi
    return 1
  fi
  echo "[OK] Panel Docker iniciado: http://localhost:8030"
}

action="${1:-help}"
mode="${2:-local}"
if [[ $# -gt 2 ]]; then usage >&2; exit 2; fi
case "$action" in
  help|-h|--help) usage; exit 0 ;;
  up|restart|logs) [[ "$mode" == local || "$mode" == docker ]] || { usage >&2; exit 2; } ;;
  down) mode="${2:-all}"; [[ "$mode" == local || "$mode" == docker || "$mode" == all ]] || { usage >&2; exit 2; } ;;
  status) [[ $# -le 1 ]] || { usage >&2; exit 2; } ;;
  *) usage >&2; exit 2 ;;
esac

mkdir -p "$RUNTIME"
command -v flock >/dev/null || { echo "[ERROR] Falta flock (util-linux)." >&2; exit 1; }
exec 9> "$RUNTIME/control.lock"
flock -n 9 || { echo "[ERROR] Ya hay un comando de control en ejecución." >&2; exit 1; }

case "$action" in
  up) if [[ "$mode" == docker ]]; then start_docker; else start_local; fi ;;
  down)
    [[ "$mode" == docker ]] || stop_local
    [[ "$mode" == local ]] || stop_docker
    ;;
  restart)
    if [[ "$mode" == docker ]]; then start_docker; compose restart web; else stop_local; start_local; fi
    ;;
  status)
    if unit_active || pid_active; then echo "Local: activo"; else echo "Local: detenido"; fi
    if docker_available; then compose ps --all; else echo "Docker: no disponible"; fi
    ;;
  logs)
    if [[ "$mode" == docker ]]; then compose logs --tail=100 web
    elif systemd_available; then journalctl --user -u "$UNIT" -n 100 --no-pager
    elif [[ -f "$LOG_FILE" ]]; then tail -100 "$LOG_FILE"
    else echo "Sin registros locales."; fi
    ;;
esac
