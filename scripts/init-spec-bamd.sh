#!/usr/bin/env bash
# =============================================================================
#  init-speckit-bmad.sh
#  Inicializa un proyecto con SpecKit + BMad Method listos para usarse
#  de forma transparente y complementaria.
#
#  Uso:
#    chmod +x init-speckit-bmad.sh
#    ./init-speckit-bmad.sh [nombre-del-proyecto] [--ai claude|copilot|cursor]
#
#  Ejemplos:
#    ./init-speckit-bmad.sh mi-app
#    ./init-speckit-bmad.sh mi-app --ai cursor
#    ./init-speckit-bmad.sh .         ← inicializa en el directorio actual
# =============================================================================

set -euo pipefail

# ─────────────────────────────────────────────
#  Colores para output
# ─────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

log()    { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()     { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()   { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()  { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
header() { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════${NC}"; \
           echo -e "${BOLD}${CYAN}  $*${NC}"; \
           echo -e "${BOLD}${CYAN}══════════════════════════════════════${NC}"; }

# ─────────────────────────────────────────────
#  Parsear argumentos
# ─────────────────────────────────────────────
PROJECT_NAME="${1:-.}"
AI_INTEGRATION="claude"   # default: Claude Code

shift || true   # consumir $1 (puede no existir)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ai)
      AI_INTEGRATION="${2:-claude}"
      shift 2
      ;;
    --help|-h)
      echo "Uso: $0 [nombre-proyecto] [--ai claude|copilot|cursor|gemini]"
      exit 0
      ;;
    *)
      warn "Argumento desconocido: $1 (ignorado)"
      shift
      ;;
  esac
done

# ─────────────────────────────────────────────
#  1. Verificar prerequisitos
# ─────────────────────────────────────────────
header "Verificando prerequisitos"

check_cmd() {
  if command -v "$1" &>/dev/null; then
    ok "$1 encontrado → $(command -v "$1")"
  else
    error "$1 no está instalado. $2"
  fi
}

check_cmd "git"  "Instala git: https://git-scm.com"
check_cmd "node" "Instala Node.js 20+: https://nodejs.org"
check_cmd "npx"  "Viene incluido con Node.js"

# Verificar versión de Node >= 20
NODE_VER=$(node -e "process.exit(parseInt(process.versions.node) < 20 ? 1 : 0)" 2>&1 || true)
NODE_MAJOR=$(node -e "console.log(parseInt(process.versions.node))")
if [[ "$NODE_MAJOR" -lt 20 ]]; then
  error "Node.js 20+ es requerido. Versión actual: $(node --version)"
fi
ok "Node.js versión: $(node --version)"

# Verificar uv (para SpecKit) — instalarlo si no existe
if ! command -v uv &>/dev/null && ! command -v uvx &>/dev/null; then
  warn "uv no encontrado. Instalando..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Cargar uv en el PATH de la sesión actual
  export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
  if ! command -v uv &>/dev/null; then
    error "No se pudo instalar uv. Instálalo manualmente: https://docs.astral.sh/uv/getting-started/installation/"
  fi
fi
ok "uv/uvx disponible"

# ─────────────────────────────────────────────
#  2. Crear o entrar al directorio del proyecto
# ─────────────────────────────────────────────
header "Preparando directorio del proyecto"

if [[ "$PROJECT_NAME" == "." ]]; then
  PROJECT_DIR="$(pwd)"
  PROJECT_NAME="$(basename "$PROJECT_DIR")"
  log "Inicializando en el directorio actual: $PROJECT_DIR"
else
  PROJECT_DIR="$(pwd)/$PROJECT_NAME"
  if [[ -d "$PROJECT_DIR" ]]; then
    warn "El directorio '$PROJECT_NAME' ya existe. Se inicializará dentro de él."
  else
    mkdir -p "$PROJECT_DIR"
    ok "Directorio creado: $PROJECT_DIR"
  fi
  cd "$PROJECT_DIR"
fi

# Init git si no existe
if [[ ! -d ".git" ]]; then
  git init -q
  ok "Repositorio git inicializado"
else
  ok "Repositorio git ya existe"
fi

# ─────────────────────────────────────────────
#  3. Instalar SpecKit
# ─────────────────────────────────────────────
header "Instalando SpecKit (Spec-Driven Development)"

log "Ejecutando: uvx specify init --here --integration $AI_INTEGRATION --force"

uvx --from "git+https://github.com/github/spec-kit.git" \
    specify init --here \
    --integration "$AI_INTEGRATION" \
    --force

ok "SpecKit instalado correctamente"

# ─────────────────────────────────────────────
#  4. Instalar BMad Method
# ─────────────────────────────────────────────
header "Instalando BMad Method"

log "Ejecutando: npx bmad-method install (no-interactivo)"

# Mapear integración de SpecKit a herramienta de BMad
case "$AI_INTEGRATION" in
  claude)        BMAD_TOOL="claude-code" ;;
  copilot)       BMAD_TOOL="copilot" ;;
  cursor)        BMAD_TOOL="cursor" ;;
  gemini)        BMAD_TOOL="gemini" ;;
  *)             BMAD_TOOL="claude-code" ;;
esac

npx bmad-method@latest install \
  --directory "$(pwd)" \
  --modules bmm \
  --tools "$BMAD_TOOL" \
  --yes

ok "BMad Method instalado correctamente"

# ─────────────────────────────────────────────
#  5. Crear estructura de carpetas compartida
# ─────────────────────────────────────────────
header "Creando estructura de artefactos compartidos"

# Carpetas donde ambos frameworks leerán/escribirán
mkdir -p docs/specs
mkdir -p docs/stories
mkdir -p docs/architecture
mkdir -p _bmad-output

ok "Estructura de carpetas creada"

# ─────────────────────────────────────────────
#  6. Crear constitution.md base
# ─────────────────────────────────────────────
CONST_FILE=".specify/memory/constitution.md"

# Solo crear si SpecKit no lo generó ya con contenido
if [[ ! -s "$CONST_FILE" ]]; then
  cat > "$CONST_FILE" << 'EOF'
# Constitución del Proyecto

## Principios Generales
- El código debe ser legible y mantenible antes que ingenioso.
- Cada feature comienza con una especificación antes de implementarse.
- Los artefactos generados por SpecKit y BMad son complementarios y comparten esta carpeta `docs/`.

## Estándares de Calidad
- Cobertura mínima de tests: 80%
- Los PRs deben incluir referencia a la spec o story correspondiente.
- Sin deuda técnica introducida intencionalmente sin documentarla.

## Flujo de Trabajo
- **SpecKit** para fase de especificación y clarificación de requisitos.
- **BMad** para fase de planificación multi-agente e implementación de stories.
- Los `tasks.md` generados por SpecKit son la entrada para el Scrum Master de BMad.

## Artefactos Compartidos
- `docs/specs/`       → especificaciones generadas por SpecKit
- `docs/stories/`     → stories generadas por BMad Scrum Master
- `docs/architecture/ ` → documentos de arquitectura (BMad Architect)
- `_bmad-output/`     → artefactos de salida de BMad
EOF
  ok "constitution.md creado en $CONST_FILE"
else
  ok "constitution.md ya existe, se conserva el contenido actual"
fi

# ─────────────────────────────────────────────
#  7. Crear WORKFLOW.md como guía de uso
# ─────────────────────────────────────────────
cat > WORKFLOW.md << 'EOF'
# Guía de Flujo de Trabajo: SpecKit + BMad

Este proyecto usa **SpecKit** y **BMad** de forma complementaria.
Ambos frameworks comparten la carpeta `docs/` como fuente de verdad.

---

## ¿Cuándo usar cada uno?

| Situación                                  | Framework     | Comando                  |
|--------------------------------------------|---------------|--------------------------|
| Feature nueva, sin contexto                | **SpecKit**   | `/speckit.specify`       |
| Clarificar requisitos ambiguos             | **SpecKit**   | `/speckit.clarify`       |
| Generar plan técnico desde spec            | **SpecKit**   | `/speckit.plan`          |
| Generar lista de tareas                    | **SpecKit**   | `/speckit.tasks`         |
| Convertir tareas en stories con contexto   | **BMad**      | `bmad-help` → Scrum Master |
| Planificación multi-agente compleja        | **BMad**      | `bmad-help`              |
| Implementación guiada por agente           | **BMad**      | BMad Developer agent     |
| Verificar cobertura de spec                | **SpecKit**   | `/speckit.analyze`       |

---

## Flujo combinado típico

```
1. /speckit.specify   → docs/specs/feature-x.md
2. /speckit.clarify   → (itera hasta resolver ambigüedades)
3. /speckit.plan      → docs/specs/plan-feature-x.md
4. /speckit.tasks     → docs/specs/tasks-feature-x.md
5. BMad Scrum Master  → docs/stories/story-001.md  (con contexto completo)
6. BMad Developer     → implementación del código
7. /speckit.analyze   → verificación de cobertura
```

---

## Comandos rápidos

```bash
# SpecKit — dentro de tu agente IA (Claude Code, Copilot, etc.)
/speckit.constitution   # Definir principios (solo una vez)
/speckit.specify        # Escribir especificación de feature
/speckit.clarify        # Resolver ambigüedades
/speckit.plan           # Plan técnico
/speckit.tasks          # Lista de tareas
/speckit.implement      # Implementar
/speckit.analyze        # Análisis de cobertura

# BMad — desde tu agente IA
bmad-help                         # Guía inteligente de próximo paso
bmad-help I just finished the spec, what's next?
```

---

## Estructura de artefactos

```
docs/
├── specs/          ← SpecKit: specs, planes y tasks
├── stories/        ← BMad: stories con contexto completo
└── architecture/   ← BMad: documentos de arquitectura

_bmad-output/       ← Salida de BMad (PRDs, diagramas, etc.)
.specify/           ← Configuración interna de SpecKit
_bmad/              ← Configuración interna de BMad
```
EOF

ok "WORKFLOW.md creado"

# ─────────────────────────────────────────────
#  8. .gitignore
# ─────────────────────────────────────────────
if [[ ! -f ".gitignore" ]]; then
  cat > .gitignore << 'EOF'
# Node
node_modules/
.npm

# Python / uv
__pycache__/
*.pyc
.venv/
.uv/

# Sistema
.DS_Store
Thumbs.db

# Credenciales
.env
.env.local
*.key

# BMad cache (local, no versionar)
~/.bmad/
EOF
  ok ".gitignore creado"
else
  ok ".gitignore ya existe, se conserva"
fi

# ─────────────────────────────────────────────
#  9. Commit inicial
# ─────────────────────────────────────────────
header "Commit inicial"

git add -A
git commit -q -m "chore: inicializar proyecto con SpecKit + BMad

- SpecKit (specify init --integration $AI_INTEGRATION)
- BMad Method (npx bmad-method install --modules bmm --tools $BMAD_TOOL)
- Estructura compartida en docs/ para artefactos de ambos frameworks
- WORKFLOW.md con guía de uso combinado
- constitution.md con principios del proyecto" \
  --allow-empty 2>/dev/null || warn "Commit omitido (sin cambios)"

ok "Commit inicial creado"

# ─────────────────────────────────────────────
#  Resumen final
# ─────────────────────────────────────────────
header "¡Proyecto listo!"

echo ""
echo -e "  ${BOLD}Proyecto:${NC}       $PROJECT_NAME"
echo -e "  ${BOLD}Directorio:${NC}     $(pwd)"
echo -e "  ${BOLD}Integración IA:${NC} $AI_INTEGRATION (SpecKit) / $BMAD_TOOL (BMad)"
echo ""
echo -e "  ${BOLD}Próximos pasos:${NC}"
echo -e "  ${CYAN}1.${NC} Abre el proyecto en tu agente IA (Claude Code, Cursor, etc.)"
echo -e "  ${CYAN}2.${NC} Ejecuta ${BOLD}/speckit.constitution${NC} para definir los principios del proyecto"
echo -e "  ${CYAN}3.${NC} Usa ${BOLD}/speckit.specify${NC} para describir tu primera feature"
echo -e "  ${CYAN}4.${NC} Consulta ${BOLD}WORKFLOW.md${NC} para el flujo combinado SpecKit + BMad"
echo ""
echo -e "  ${GREEN}Lee WORKFLOW.md para la guía completa de uso combinado.${NC}"
echo ""