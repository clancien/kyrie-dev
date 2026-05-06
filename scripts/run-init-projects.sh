#!/usr/bin/env bash
set -u

INIT_SCRIPT="/home/clancien/workspace/dev/scripts/init-project.sh"
LOG_DIR="/tmp/init-project-logs"

TARGET_DIRS=(
  "/home/clancien/workspace/abax"
  "/home/clancien/workspace/autopase"
  "/home/clancien/workspace/biodanza"
  "/home/clancien/workspace/chile911"
  "/home/clancien/workspace/circulo"
  "/home/clancien/workspace/cyber"
  "/home/clancien/workspace/docker"
  "/home/clancien/workspace/imperial"
  "/home/clancien/workspace/jef"
  "/home/clancien/workspace/kyrie"
  "/home/clancien/workspace/meridian"
  "/home/clancien/workspace/nodejs"
  "/home/clancien/workspace/novokey"
  "/home/clancien/workspace/oit"
  "/home/clancien/workspace/pacs"
  "/home/clancien/workspace/pauli"
  "/home/clancien/workspace/relacionarte"
  "/home/clancien/workspace/siap"
  "/home/clancien/workspace/siap-reportes"
  "/home/clancien/workspace/sidot"
  "/home/clancien/workspace/sis"
  "/home/clancien/workspace/sugar"
  "/home/clancien/workspace/world"
)

if [[ ! -f "$INIT_SCRIPT" ]]; then
  echo "ERROR: no existe script: $INIT_SCRIPT"
  exit 1
fi

if [[ ! -e /dev/tty ]]; then
  echo "ERROR: no hay terminal interactiva disponible (/dev/tty)."
  exit 1
fi

mkdir -p "$LOG_DIR"

ok=0
fail=0

for dir in "${TARGET_DIRS[@]}"; do
  name="$(basename "$dir")"
  log_file="$LOG_DIR/init-project.${name}.log"

  echo "=== $dir ==="

  if [[ ! -d "$dir" ]]; then
    echo "STATUS: ERROR (carpeta no existe)"
    fail=$((fail + 1))
    continue
  fi

  if (cd "$dir" && bash "$INIT_SCRIPT" </dev/tty 2>&1 | tee "$log_file"); then
    echo "STATUS: OK"
    ok=$((ok + 1))
  else
    echo "STATUS: ERROR"
    echo "LOG: $log_file"
    fail=$((fail + 1))
  fi

done

echo "---"
echo "TOTAL OK: $ok"
echo "TOTAL ERROR: $fail"
echo "LOG DIR: $LOG_DIR"

if [[ "$fail" -gt 0 ]]; then
  exit 2
fi
