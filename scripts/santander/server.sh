#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export SANTANDER_UID="$(id -u)" SANTANDER_GID="$(id -g)"
MODE="${2:-local}"; PORT="${SANTANDER_PORT:-8031}"
[[ "$PORT" != 8030 ]] || { echo '8030 reservado para Banco de Chile'; exit 1; }
COMPOSE=(docker compose -p santander-panel -f "$ROOT/docker-compose.yml")
mkdir -p "$ROOT/.cache"; chmod 700 "$ROOT/.cache"
exec 9>"$ROOT/.cache/control.lock"
flock -n 9 || { echo "Control Santander ocupado"; exit 1; }
PID="$ROOT/.cache/server.pid"; LOG="$ROOT/.cache/server.log"
live(){ [[ -f "$PID" ]] && kill -0 "$(cat "$PID")" 2>/dev/null && [[ "$(tr '\0' ' ' 2>/dev/null < "/proc/$(cat "$PID")/cmdline")" == *"$ROOT/santander_web_server.py"* ]]; }
stop_local(){ if live; then kill "$(cat "$PID")"; for attempt in {1..30}; do live || break; sleep .1; done; if live; then echo "Santander no terminó; revise proceso propio"; exit 1; fi; fi; rm -f "$PID"; }
case "${1:---help}" in
 up|restart)
   if [[ "$MODE" == docker ]]; then
     "${COMPOSE[@]}" build
     stop_local
     if [[ "$1" == restart ]]; then "${COMPOSE[@]}" up -d --force-recreate; else "${COMPOSE[@]}" up -d; fi
   elif [[ "$MODE" == local ]]; then
     if live && [[ "$1" == up ]]; then echo 'Santander ya está activo'; exit; fi
     [[ -x "$ROOT/.venv/bin/python" ]] || { echo 'Ejecute setup_env.sh antes de iniciar'; exit 1; }
     "$ROOT/.venv/bin/python" -c 'import requests, dotenv, playwright'
     "${COMPOSE[@]}" stop >/dev/null 2>&1 || true
     if ! live; then "$ROOT/.venv/bin/python" -c 'import socket,sys; s=socket.socket(); s.bind(("127.0.0.1",int(sys.argv[1])))' "$PORT" || { echo 'Puerto ocupado'; exit 1; }; fi
     stop_local
     "${COMPOSE[@]}" stop >/dev/null 2>&1 || true
     setsid nohup "$ROOT/.venv/bin/python" "$ROOT/santander_web_server.py" --port "$PORT" >"$LOG" 2>&1 9>&- & echo "$!" > "$PID"; chmod 600 "$PID" "$LOG"
     for attempt in {1..30}; do
       if "$ROOT/.venv/bin/python" -c 'import urllib.request,sys; urllib.request.urlopen("http://127.0.0.1:"+sys.argv[1]+"/api/status",timeout=1)' "$PORT" >/dev/null 2>&1; then echo "Santander disponible en http://localhost:$PORT"; exit 0; fi
       live || { echo 'No se pudo iniciar Santander; revise logs'; exit 1; }
       sleep .2
     done
     echo 'Santander no respondió al iniciar'; exit 1
   else echo 'Modo: local o docker'; exit 1; fi;;
 down) if [[ -z "${2:-}" ]]; then stop_local; "${COMPOSE[@]}" down; elif [[ "$MODE" == docker ]]; then "${COMPOSE[@]}" down; else stop_local; fi;;
 status) if [[ -z "${2:-}" ]]; then if live; then echo 'Santander local activo'; else echo 'Santander local detenido'; fi; "${COMPOSE[@]}" ps; elif [[ "$MODE" == docker ]]; then "${COMPOSE[@]}" ps; elif live; then echo 'Santander activo'; else echo 'Santander detenido'; fi;;
 logs) if [[ "$MODE" == docker ]]; then "${COMPOSE[@]}" logs --tail=100; else tail -n 100 "$LOG"; fi;;
 *) echo 'Uso: server.sh {up|down|restart|status|logs} [local|docker] (SANTANDER_PORT=8031)';;
esac
