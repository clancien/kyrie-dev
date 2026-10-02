#!/usr/bin/env bash
# Update standalone Google Antigravity and Antigravity IDE on Linux x64.
# It never modifies an installation until the new archive is downloaded,
# inspected and extracted successfully.  The previous version is retained
# under ~/.local/state/antigravity-updater/backups for rollback.

set -Eeuo pipefail
IFS=$'\n\t'

readonly DOWNLOAD_PAGE='https://antigravity.google/download'
readonly APP_DIR='/home/clancien/bin/Antigravity-x64'
readonly IDE_DIR='/home/clancien/bin/Antigravity_IDE'
readonly STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/antigravity-updater"
readonly BACKUP_DIR="$STATE_DIR/backups"
readonly LOCK_FILE="$STATE_DIR/update.lock"

DRY_RUN=0
FORCE=0
ROLLBACK_TARGET=''

usage() {
  cat <<'EOF'
Uso: update-antigravity.sh [--dry-run] [--force] [--rollback NOMBRE]

  --dry-run            Muestra versiones y acciones, sin modificar archivos.
  --force              Actualiza aunque no sea posible conocer la versión local.
  --rollback NOMBRE    Restaura un respaldo creado por este script.
EOF
}

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
note() { printf '%s\n' "$*"; }

cleanup() {
  [[ -n ${WORK_DIR:-} && -d ${WORK_DIR:-} ]] && rm -rf -- "$WORK_DIR"
}
trap cleanup EXIT

require_command() { command -v "$1" >/dev/null 2>&1 || die "Falta el comando requerido: $1"; }

while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --force) FORCE=1 ;;
    --rollback)
      (($# >= 2)) || die '--rollback requiere el nombre de un respaldo.'
      ROLLBACK_TARGET=$2
      shift
      ;;
    -h|--help) usage; exit 0 ;;
    *) die "Opción desconocida: $1" ;;
  esac
  shift
done

require_command curl
require_command tar
require_command awk
require_command sort
require_command pgrep
require_command flock
require_command grep
require_command cut
require_command find
require_command dirname

mkdir -p -- "$STATE_DIR" "$BACKUP_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || die 'Ya hay otra actualización de Antigravity en curso.'

is_running() {
  # Coincidencia exacta de la ruta del ejecutable: no detiene procesos ajenos.
  pgrep -f -x "$1( .*)?" >/dev/null 2>&1
}

ensure_closed() {
  local executable
  for executable in "$APP_DIR/antigravity" "$IDE_DIR/antigravity-ide" "$IDE_DIR/bin/antigravity-ide"; do
    if [[ -x "$executable" ]] && is_running "$executable"; then
      die "Antigravity está abierto ($executable). Ciérralo por completo y vuelve a ejecutar el script."
    fi
  done
}

version_from_manifest() {
  local manifest=$1
  [[ -r "$manifest" ]] || return 1
  awk -F'"' '/"version"[[:space:]]*:/ { print $4; exit }' "$manifest"
}

version_from_asar() {
  local archive=$1
  command -v node >/dev/null 2>&1 || return 1
  node -e 'const fs=require("fs"); const b=fs.readFileSync(process.argv[1]); const n=b.readUInt32LE(12); const h=JSON.parse(b.toString("utf8",16,16+n)); const p=h.files && h.files["package.json"]; if(!p || p.offset===undefined) process.exit(2); const o=8+b.readUInt32LE(4)+Number(p.offset); const j=JSON.parse(b.toString("utf8",o,o+p.size)); if(!j.version) process.exit(3); process.stdout.write(String(j.version));' "$archive" 2>/dev/null
}

saved_version() {
  local name=$1
  [[ -r "$STATE_DIR/$name.version" ]] && <"$STATE_DIR/$name.version"
}

local_version() {
  local name=$1 directory=$2 manifest
  manifest="$directory/resources/app/package.json"
  saved_version "$name" ||
    version_from_manifest "$manifest" ||
    version_from_asar "$directory/resources/app.asar" ||
    true
}

version_is_newer() {
  local local_version=$1 remote_version=$2
  [[ -n "$local_version" ]] || return 2
  [[ "$local_version" != "$remote_version" ]] || return 1
  [[ "$(printf '%s\n%s\n' "$local_version" "$remote_version" | sort -V | tail -n1)" == "$remote_version" ]]
}

extract_url() {
  local page=$1 pattern=$2 url
  # The page may encode slashes and ampersands as JSON escapes; normalize only
  # those HTML/JSON escapes before selecting the HTTPS archive URL.
  url=$(printf '%s' "$page" | tr '\\' ' ' | sed 's#\\u0026#\&#g' |
    grep -oE "https://[^\"'[:space:]\\]+$pattern" | head -n1 || true)
  [[ -n "$url" ]] || return 1
  printf '%s\n' "$url"
}

validate_archive() {
  local archive=$1 entry
  tar -tzf "$archive" >/dev/null || die "El archivo descargado no es un tar.gz válido: $archive"
  while IFS= read -r entry; do
    [[ "$entry" != /* && "$entry" != *'../'* && "$entry" != '..' ]] || die 'El archivo descargado contiene rutas inseguras.'
  done < <(tar -tzf "$archive")
}

find_extracted_root() {
  local directory=$1 binary_name=$2 binary_path
  binary_path=$(find "$directory" -type f -name "$binary_name" -print -quit)
  [[ -n "$binary_path" ]] || return 1
  dirname "$binary_path"
}

restore_sandbox_permissions() {
  local directory sandbox
  directory=$1
  sandbox="$directory/chrome-sandbox"
  [[ -e "$sandbox" ]] || return 0
  # Electron needs this helper to remain owned by root with setuid enabled on
  # systems where the current installation uses the setuid sandbox.
  if [[ -e "$APP_DIR/chrome-sandbox" || -e "$IDE_DIR/chrome-sandbox" ]]; then
    sudo chown root:root -- "$sandbox"
    sudo chmod 4755 -- "$sandbox"
  fi
}

install_one() {
  local name=$1 target=$2 remote_version=$3 url=$4 current stage extracted_root backup stamp
  [[ -d "$target" ]] || die "No existe la instalación de $name: $target"
  current=$(local_version "$name" "$target")
  printf '%s: instalada=%s, disponible=%s\n' "$name" "${current:-desconocida}" "$remote_version"

  if version_is_newer "$current" "$remote_version"; then
    :
  else
    case $? in
      1) note "$name ya está actualizado."; return 0 ;;
      2)
        (( FORCE )) || { note "$name: no se pudo determinar la versión local; usa --force para actualizarlo."; return 0; }
        ;;
      *) die "No se pudo comparar las versiones de $name." ;;
    esac
  fi

  (( DRY_RUN )) && { note "$name: se descargaría e instalaría desde $url"; return 0; }
  ensure_closed
  archive="$WORK_DIR/$name.tar.gz"
  stage="$WORK_DIR/$name"
  note "Descargando $name desde Google..."
  curl --fail --location --proto '=https' --tlsv1.2 --retry 3 --output "$archive" "$url"
  validate_archive "$archive"
  mkdir -p -- "$stage"
  tar -xzf "$archive" -C "$stage" --no-same-owner --no-same-permissions
  case "$name" in
    antigravity) extracted_root=$(find_extracted_root "$stage" antigravity) || die 'El archivo oficial no contiene el ejecutable antigravity.' ;;
    ide) extracted_root=$(find_extracted_root "$stage" antigravity-ide) || die 'El archivo oficial no contiene el ejecutable antigravity-ide.' ;;
  esac

  # Move is atomic because both paths live under /home/clancien/bin. A failed
  # permission repair is followed by an automatic rollback.
  stamp=$(date '+%Y%m%d-%H%M%S')
  backup="$BACKUP_DIR/${name}-${stamp}"
  mv -- "$target" "$backup"
  if ! mv -- "$extracted_root" "$target"; then
    mv -- "$backup" "$target"
    die "No se pudo instalar $name; se restauró la versión anterior."
  fi
  if ! restore_sandbox_permissions "$target"; then
    rm -rf -- "$target"
    mv -- "$backup" "$target"
    die "No se pudieron configurar los permisos del sandbox; se restauró la versión anterior."
  fi
  printf '%s\n' "$remote_version" >"$STATE_DIR/$name.version"
  note "$name actualizado a $remote_version. Respaldo: $backup"
}

rollback() {
  local backup="$BACKUP_DIR/$ROLLBACK_TARGET" target
  [[ -d "$backup" ]] || die "No existe el respaldo: $backup"
  ensure_closed
  case "$ROLLBACK_TARGET" in
    antigravity-*) target=$APP_DIR ;;
    ide-*) target=$IDE_DIR ;;
    *) die 'El nombre de respaldo no corresponde a una instalación conocida.' ;;
  esac
  (( DRY_RUN )) && { note "Se restauraría $backup en $target"; return; }
  local displaced="$BACKUP_DIR/pre-rollback-$(date '+%Y%m%d-%H%M%S')"
  mv -- "$target" "$displaced"
  mv -- "$backup" "$target"
  restore_sandbox_permissions "$target"
  note "Rollback aplicado. La versión reemplazada quedó en: $displaced"
}

if [[ -n "$ROLLBACK_TARGET" ]]; then
  rollback
  exit 0
fi

ensure_closed
WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/antigravity-update.XXXXXX")
# Google currently serves this page with gzip content encoding even when curl
# does not advertise it.  --compressed both requests and decodes that response.
page=$(curl --fail --location --compressed --proto '=https' --tlsv1.2 --retry 3 "$DOWNLOAD_PAGE")

app_url=$(extract_url "$page" '/linux-x64/Antigravity\.tar\.gz') || die 'No se encontró la descarga Linux x64 de Antigravity en la página oficial.'
ide_url=$(extract_url "$page" '/linux-x64/Antigravity(%20| )IDE\.tar\.gz') || die 'No se encontró la descarga Linux x64 de Antigravity IDE en la página oficial.'
app_remote=$(printf '%s\n' "$app_url" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+-[0-9]+' | head -n1 | cut -d- -f1 || true)
ide_remote=$(printf '%s\n' "$ide_url" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+-[0-9]+' | head -n1 | cut -d- -f1 || true)
[[ -n "$app_remote" && -n "$ide_remote" ]] || die 'No se pudieron identificar las versiones oficiales en la página de descarga.'

install_one antigravity "$APP_DIR" "$app_remote" "$app_url"
install_one ide "$IDE_DIR" "$ide_remote" "$ide_url"
