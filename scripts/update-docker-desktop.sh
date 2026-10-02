#!/usr/bin/env bash
# Actualiza Docker Desktop para Ubuntu x86-64 desde el paquete DEB oficial.
# Docker Engine (docker-ce) se actualiza por separado mediante APT.

set -euo pipefail

readonly PACKAGE_URL='https://desktop.docker.com/linux/main/amd64/docker-desktop-amd64.deb'
readonly PACKAGE_NAME='docker-desktop'
readonly EXPECTED_ARCH='amd64'
readonly STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/docker-desktop-updater"

DRY_RUN=0
FORCE=0
WORK_DIR=''

usage() {
  cat <<'EOF'
Uso: update-docker-desktop.sh [--dry-run] [--force]

  --dry-run  Consulta las versiones sin descargar ni instalar el paquete completo.
  --force    Reinstala la versión publicada aunque ya esté instalada.
  -h, --help Muestra esta ayuda.
EOF
}

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
note() { printf '%s\n' "$*"; }
require_command() { command -v "$1" >/dev/null 2>&1 || die "Falta el comando requerido: $1"; }
cleanup() { [[ -z "$WORK_DIR" ]] || rm -rf -- "$WORK_DIR"; }
trap cleanup EXIT

while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --force) FORCE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Opción desconocida: $1" ;;
  esac
  shift
done

require_command curl
require_command dpkg
require_command dpkg-deb
require_command dpkg-query
require_command flock
require_command mktemp
require_command apt

[[ "$(dpkg --print-architecture)" == "$EXPECTED_ARCH" ]] || die 'Este script requiere Ubuntu/Debian amd64.'
[[ "$(id -u)" -ne 0 ]] || die 'Ejecuta el script como usuario normal; usará sudo solo para instalar.'

mkdir -p -- "$STATE_DIR"
exec 9>"$STATE_DIR/update.lock"
flock -n 9 || die 'Ya hay otra actualización de Docker Desktop en curso.'
WORK_DIR=$(mktemp -d /tmp/docker-desktop-update.XXXXXXXX)

package_field() {
  dpkg-deb -f "$1" "$2" 2>/dev/null || die "No se pudo leer el campo $2 del paquete descargado."
}

verify_package() {
  local file=$1 expected_version=$2 name arch version
  name=$(package_field "$file" Package)
  arch=$(package_field "$file" Architecture)
  version=$(package_field "$file" Version)
  [[ "$name" == "$PACKAGE_NAME" && "$arch" == "$EXPECTED_ARCH" ]] || die 'La descarga no es un paquete Docker Desktop amd64 válido.'
  [[ -z "$expected_version" || "$version" == "$expected_version" ]] || die "La versión descargada cambió durante la actualización ($version). Vuelve a ejecutar el script."
  printf '%s\n' "$version"
}

installed_version=$(dpkg-query -W -f='${Version}' "$PACKAGE_NAME" 2>/dev/null || true)
[[ -n "$installed_version" ]] || die 'Docker Desktop no está instalado.'

# En los DEB oficiales, control.tar está al principio. El rango permite leer
# la versión remota sin descargar los cientos de MB de data.tar.
metadata="$WORK_DIR/metadata.deb"
note 'Consultando la versión publicada por Docker...'
curl --fail --silent --show-error --location --retry 3 \
  --proto '=https' --proto-redir '=https' --tlsv1.2 \
  --range 0-1048575 --max-filesize 1048576 \
  --output "$metadata" "$PACKAGE_URL" || die 'No se pudo consultar el paquete oficial.'
remote_version=$(verify_package "$metadata" '')
printf 'Docker Desktop: instalada=%s, disponible=%s\n' "$installed_version" "$remote_version"

if dpkg --compare-versions "$remote_version" lt "$installed_version"; then
  die 'La versión publicada es anterior a la instalada; se cancela para evitar una degradación.'
fi
if dpkg --compare-versions "$remote_version" eq "$installed_version" && (( ! FORCE )); then
  note 'Docker Desktop ya está actualizado.'
  exit 0
fi
if (( DRY_RUN )); then
  note "Se descargaría e instalaría $remote_version desde $PACKAGE_URL"
  exit 0
fi

require_command sudo
if command -v systemctl >/dev/null 2>&1 && systemctl --user --quiet is-active docker-desktop.service; then
  die 'Docker Desktop está abierto. Ciérralo y vuelve a ejecutar el script.'
fi

package="$WORK_DIR/docker-desktop-amd64.deb"
note "Descargando Docker Desktop $remote_version..."
curl --fail --show-error --location --retry 3 \
  --proto '=https' --proto-redir '=https' --tlsv1.2 \
  --output "$package" "$PACKAGE_URL" || die 'No se pudo descargar el paquete oficial.'
verify_package "$package" "$remote_version" >/dev/null
dpkg-deb --info "$package" >/dev/null || die 'El paquete descargado está dañado.'

# APT necesita leer el archivo como usuario _apt; el DEB es una descarga pública.
chmod 755 "$WORK_DIR"
chmod 644 "$package"
note 'Instalando con APT...'
if (( FORCE )); then
  sudo apt install --reinstall "$package"
else
  sudo apt install "$package"
fi

final_version=$(dpkg-query -W -f='${Version}' "$PACKAGE_NAME")
[[ "$final_version" == "$remote_version" ]] || die "APT terminó, pero la versión instalada es $final_version (se esperaba $remote_version)."
note "Docker Desktop actualizado a $final_version."
