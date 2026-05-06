#!/usr/bin/env bash
set -u

DEV_ROOT="${HOME}/workspace/dev"
SRC_AGENTS="${DEV_ROOT}/.agents"
SRC_BMAD="${DEV_ROOT}/_bmad"

DST_AGENTS=".agents"
DST_BMAD="_bmad"
DST_AGENTS_MD="AGENTS.md"
GITIGNORE_FILE=".gitignore"

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

resolved_path() {
  local path="$1"
  readlink -f "$path" 2>/dev/null || true
}

check_symlink_target() {
  local dst="$1"
  local src="$2"

  if [[ ! -L "$dst" ]]; then
    return 1
  fi

  [[ "$(resolved_path "$dst")" == "$(resolved_path "$src")" ]]
}

check_gitignore_entry() {
  local entry="$1"

  [[ -f "$GITIGNORE_FILE" ]] && grep -Fxq "$entry" "$GITIGNORE_FILE"
}

status_cell() {
  local ok="$1"

  if [[ "$ok" -eq 1 ]]; then
    printf "%s" "OK"
  else
    printf "%s" "--"
  fi
}

print_separator() {
  printf "%-16s | %-14s | %-7s | %-5s | %-9s | %-12s | %-11s\n" \
    "----------------" "--------------" "-------" "-----" "---------" "------------" "-----------"
}

print_row() {
  local project="$1"
  local status="$2"
  local agents="$3"
  local bmad="$4"
  local agents_md="$5"
  local gitignore_agents="$6"
  local gitignore_bmad="$7"

  printf "%-16s | %-14s | %-7s | %-5s | %-9s | %-12s | %-11s\n" \
    "$project" "$status" "$agents" "$bmad" "$agents_md" "$gitignore_agents" "$gitignore_bmad"
}

total=0
missing_dirs=0
installed=0
partial=0
not_installed=0

agents_ok_total=0
bmad_ok_total=0
agents_md_ok_total=0
gitignore_agents_ok_total=0
gitignore_bmad_ok_total=0

print_row "Proyecto" "Estado" ".agents" "_bmad" "AGENTS.md" "git .agents" "git _bmad"
print_separator

for dir in "${TARGET_DIRS[@]}"; do
  total=$((total + 1))
  name="$(basename "$dir")"

  if [[ ! -d "$dir" ]]; then
    print_row "$name" "FALTA DIR" "--" "--" "--" "--" "--"
    missing_dirs=$((missing_dirs + 1))
    continue
  fi

  agents_ok=0
  bmad_ok=0
  agents_md_ok=0
  gitignore_agents_ok=0
  gitignore_bmad_ok=0

  if (
    cd "$dir" || exit 1

    check_symlink_target "$DST_AGENTS" "$SRC_AGENTS"
  ); then
    agents_ok=1
    agents_ok_total=$((agents_ok_total + 1))
  fi

  if (
    cd "$dir" || exit 1

    check_symlink_target "$DST_BMAD" "$SRC_BMAD"
  ); then
    bmad_ok=1
    bmad_ok_total=$((bmad_ok_total + 1))
  fi

  if [[ -f "$dir/$DST_AGENTS_MD" ]]; then
    agents_md_ok=1
    agents_md_ok_total=$((agents_md_ok_total + 1))
  fi

  if (
    cd "$dir" || exit 1

    check_gitignore_entry "$DST_AGENTS"
  ); then
    gitignore_agents_ok=1
    gitignore_agents_ok_total=$((gitignore_agents_ok_total + 1))
  fi

  if (
    cd "$dir" || exit 1

    check_gitignore_entry "$DST_BMAD"
  ); then
    gitignore_bmad_ok=1
    gitignore_bmad_ok_total=$((gitignore_bmad_ok_total + 1))
  fi

  ok_count=$((agents_ok + bmad_ok + agents_md_ok + gitignore_agents_ok + gitignore_bmad_ok))

  if [[ "$ok_count" -eq 5 ]]; then
    status="INSTALADO"
    installed=$((installed + 1))
  elif [[ "$ok_count" -eq 0 ]]; then
    status="NO INSTALADO"
    not_installed=$((not_installed + 1))
  else
    status="PARCIAL $ok_count/5"
    partial=$((partial + 1))
  fi

  print_row \
    "$name" \
    "$status" \
    "$(status_cell "$agents_ok")" \
    "$(status_cell "$bmad_ok")" \
    "$(status_cell "$agents_md_ok")" \
    "$(status_cell "$gitignore_agents_ok")" \
    "$(status_cell "$gitignore_bmad_ok")"

done

checked=$((total - missing_dirs))

echo "---"
printf "%-22s %s\n" "TOTAL CARPETAS:" "$total"
printf "%-22s %s\n" "CARPETAS REVISADAS:" "$checked"
printf "%-22s %s\n" "CARPETAS FALTANTES:" "$missing_dirs"
printf "%-22s %s\n" "INSTALADO:" "$installed"
printf "%-22s %s\n" "PARCIAL:" "$partial"
printf "%-22s %s\n" "NO INSTALADO:" "$not_installed"
echo "---"
echo "COMPONENTES OK:"
printf "%-22s %s/%s\n" "$DST_AGENTS:" "$agents_ok_total" "$checked"
printf "%-22s %s/%s\n" "$DST_BMAD:" "$bmad_ok_total" "$checked"
printf "%-22s %s/%s\n" "$DST_AGENTS_MD:" "$agents_md_ok_total" "$checked"
printf "%-22s %s/%s\n" "$GITIGNORE_FILE $DST_AGENTS:" "$gitignore_agents_ok_total" "$checked"
printf "%-22s %s/%s\n" "$GITIGNORE_FILE $DST_BMAD:" "$gitignore_bmad_ok_total" "$checked"

if [[ "$missing_dirs" -gt 0 || "$partial" -gt 0 || "$not_installed" -gt 0 ]]; then
  exit 1
fi
