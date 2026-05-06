#!/usr/bin/env bash
set -euo pipefail

DEV_ROOT="${HOME}/workspace/dev"
SRC_AGENTS="${DEV_ROOT}/.agents"
SRC_BMAD="${DEV_ROOT}/_bmad"
SRC_AGENTS_MD="${DEV_ROOT}/doc/setup/AGENTS.md"

DST_AGENTS=".agents"
DST_BMAD="_bmad"
DST_AGENTS_MD="AGENTS.md"
GITIGNORE_FILE=".gitignore"

confirm() {
  local prompt="$1"
  local default_no="${2:-1}"
  local ans

  if [[ "$default_no" -eq 1 ]]; then
    read -r -p "${prompt} [y/N]: " ans || true
  else
    read -r -p "${prompt} [Y/n]: " ans || true
  fi

  ans="${ans:-}"
  case "${ans}" in
    y|Y|yes|YES) return 0 ;;
    n|N|no|NO) return 1 ;;
    "")
      if [[ "$default_no" -eq 1 ]]; then
        return 1
      fi
      return 0
      ;;
    *)
      echo "Respuesta no valida: '${ans}'. Se toma como 'No'."
      return 1
      ;;
  esac
}

require_source() {
  local src="$1"
  if [[ ! -e "$src" ]]; then
    echo "ERROR: no existe origen requerido: $src"
    exit 1
  fi
}

ensure_symlink() {
  local src="$1"
  local dst="$2"

  require_source "$src"

  if [[ -L "$dst" ]]; then
    local current
    current="$(readlink "$dst")"
    local resolved_current
    resolved_current="$(readlink -f "$dst" || true)"
    local resolved_src
    resolved_src="$(readlink -f "$src" || true)"

    if [[ "$resolved_current" == "$resolved_src" ]]; then
      echo "OK: $dst ya apunta a $src"
      return 0
    fi

    echo "AVISO: $dst es symlink pero apunta a: $current"
    if confirm "Reemplazar symlink para que apunte a $src?" 1; then
      rm "$dst"
      ln -s "$src" "$dst"
      echo "Actualizado: $dst -> $src"
    else
      echo "Omitido: $dst"
    fi
    return 0
  fi

  if [[ -e "$dst" ]]; then
    echo "AVISO: $dst existe y no es symlink."
    if confirm "Eliminar '$dst' y crear symlink a $src?" 1; then
      rm -rf "$dst"
      ln -s "$src" "$dst"
      echo "Creado: $dst -> $src"
    else
      echo "Omitido: $dst"
    fi
    return 0
  fi

  ln -s "$src" "$dst"
  echo "Creado: $dst -> $src"
}

copy_agents_md() {
  require_source "$SRC_AGENTS_MD"

  backup_agents_md() {
    local backup_file
    backup_file="${DST_AGENTS_MD}.bak.$(date +%Y%m%d-%H%M%S)"
    cp "$DST_AGENTS_MD" "$backup_file"
    echo "Backup creado: $backup_file"
  }

  if [[ -e "$DST_AGENTS_MD" ]]; then
    if cmp -s "$SRC_AGENTS_MD" "$DST_AGENTS_MD"; then
      echo "OK: $DST_AGENTS_MD ya esta actualizado."
      return 0
    fi

    echo "AVISO: $DST_AGENTS_MD ya existe y difiere de origen."
    if confirm "Sobrescribir $DST_AGENTS_MD con $SRC_AGENTS_MD?" 1; then
      backup_agents_md
      cp "$SRC_AGENTS_MD" "$DST_AGENTS_MD"
      echo "Actualizado: $DST_AGENTS_MD"
    else
      echo "Omitido: $DST_AGENTS_MD"
    fi
    return 0
  fi

  cp "$SRC_AGENTS_MD" "$DST_AGENTS_MD"
  echo "Copiado: $DST_AGENTS_MD"
}

ensure_gitignore_entry() {
  local entry="$1"
  local file="$2"

  if [[ ! -e "$file" ]]; then
    printf "%s\n" "$entry" > "$file"
    echo "Creado: $file con entrada '$entry'"
    return 0
  fi

  if grep -Fxq "$entry" "$file"; then
    echo "OK: $entry ya existe en $file"
    return 0
  fi

  echo "AVISO: falta '$entry' en $file."
  if confirm "Agregar '$entry' a $file?" 1; then
    printf "\n%s\n" "$entry" >> "$file"
    echo "Agregado: $entry a $file"
  else
    echo "Omitido: agregar $entry a $file"
  fi
}

run_codex_agents_init() {
  if ! command -v codex >/dev/null 2>&1; then
    echo "AVISO: 'codex' no esta instalado o no esta en PATH. Se omite inicializacion de AGENTS.md."
    return 0
  fi

  if [[ ! -f "$DST_AGENTS_MD" ]]; then
    echo "AVISO: no existe $DST_AGENTS_MD. Se omite inicializacion con codex."
    return 0
  fi

  if confirm "Ejecutar codex para completar datos faltantes en $DST_AGENTS_MD?" 1; then
    codex exec --ignore-user-config --ignore-rules --dangerously-bypass-approvals-and-sandbox "/init completa los datos faltantes en el AGENTS.md"


  else
    echo "Omitido: inicializacion de AGENTS.md con codex"
  fi
}

run_codex_agents_backup_review() {
  if ! command -v codex >/dev/null 2>&1; then
    echo "AVISO: 'codex' no esta instalado o no esta en PATH. Se omite revision de backups de AGENTS.md."
    return 0
  fi

  if [[ ! -f "$DST_AGENTS_MD" ]]; then
    echo "AVISO: no existe $DST_AGENTS_MD. Se omite revision de backups con codex."
    return 0
  fi

  if ! compgen -G "${DST_AGENTS_MD}.bak.*" >/dev/null; then
    echo "OK: no hay backups ${DST_AGENTS_MD}.bak.* para comparar."
    return 0
  fi

  if confirm "Ejecutar codex para comparar backups de $DST_AGENTS_MD con el archivo actual?" 1; then
    codex exec --ignore-user-config --ignore-rules --dangerously-bypass-approvals-and-sandbox "Compara AGENTS.md.bak.* y AGENTS.md y dime si ves cosas importantes que incorporar en AGENTS.md."
  else
    echo "Omitido: revision de backups de AGENTS.md con codex"
  fi
}

echo "Inicializando proyecto en: $(pwd)"
echo "Fuente compartida: $DEV_ROOT"

ensure_symlink "$SRC_AGENTS" "$DST_AGENTS"
ensure_symlink "$SRC_BMAD" "$DST_BMAD"
copy_agents_md
ensure_gitignore_entry ".agents" "$GITIGNORE_FILE"
ensure_gitignore_entry "_bmad" "$GITIGNORE_FILE"
run_codex_agents_init
run_codex_agents_backup_review

echo "Listo."
