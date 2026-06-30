#!/bin/bash

# --- COLORES ---
ROJO='\033[0;31m'
VERDE='\033[0;32m'
AZUL='\033[0;34m'
NC='\033[0m' # Sin color

# --- VARIABLES DE CONFIGURACIÓN ---
BMAD_USER_NAME="${USER:-}"
if [ -z "$BMAD_USER_NAME" ]; then
    BMAD_USER_NAME="$(id -un 2>/dev/null || whoami)"
fi
BMAD_OUTPUT_DIR="doc"
BMAD_PLANNING_ARTIFACTS="doc/planning-artifacts"
BMAD_IMPLEMENTATION_ARTIFACTS="doc/implementation-artifacts"
BMAD_TEST_ARTIFACTS="doc/test-artifacts"
BMAD_DESIGN_ARTIFACTS="doc/design-artifacts"
BMAD_LANG="Spanish"
BMAD_MODULES="bmm,bmb,tea,cis,wds"
BMAD_TOOLS="codex,claude-code"

# --- VALIDACIÓN DE ARGUMENTOS ---

# 1. Verificar si se proporcionó un argumento
if [ -z "$1" ]; then
    echo -e "${ROJO}Error: No se ha especificado ninguna carpeta.${NC}"
    echo -e "Uso: $0 /ruta/a/la/carpeta"
    exit 1
fi

# Asignar el primer argumento a una variable limpia
CARPETA_OBJETIVO="$1"

# 2. Verificar si la ruta existe y si es realmente un directorio
if [ ! -d "$CARPETA_OBJETIVO" ]; then
    echo -e "${ROJO}Error: La ruta '$CARPETA_OBJETIVO' no existe o no es una carpeta válida.${NC}"
    exit 1
fi

# Obtener la ruta absoluta de la carpeta (por si se pasó una ruta relativa como "." o "../")
RUTA_ABSOLUTA=$(cd "$CARPETA_OBJETIVO" && pwd)
BMM_PROJECT_NAME="$(basename "$RUTA_ABSOLUTA")"

# 3. Validar que no exista una instalación previa
if [ -d "$RUTA_ABSOLUTA/.agents" ] || [ -d "$RUTA_ABSOLUTA/_bmad" ]; then
    echo -e "${ROJO}Alerta: Ya existe una instalación previa en '$RUTA_ABSOLUTA' (.agents o _bmad).${NC}"
    echo -e "${ROJO}Cancelo la ejecución para evitar sobreescribir configuración existente.${NC}"
    exit 1
fi

# Instalar bmad-method en la carpeta especificada
echo "Instalando bmad-method en: $RUTA_ABSOLUTA"

npx bmad-method install \
  --directory "$RUTA_ABSOLUTA" \
  --yes \
  --modules "$BMAD_MODULES" \
  --tools "$BMAD_TOOLS" \
  --set core.user_name="$BMAD_USER_NAME" \
  --set bmm.project_name="$BMM_PROJECT_NAME" \
  --set core.communication_language="$BMAD_LANG" \
  --set core.document_output_language="$BMAD_LANG" \
  --set bmm.project_knowledge="$BMAD_OUTPUT_DIR" \
  --set bmm.planning_artifacts="$BMAD_PLANNING_ARTIFACTS" \
  --set bmm.implementation_artifacts="$BMAD_IMPLEMENTATION_ARTIFACTS" \
  --set tea.test_artifacts="$BMAD_TEST_ARTIFACTS" \
  --set wds.project_knowledge="$BMAD_OUTPUT_DIR" \
  --set wds.design_artifacts="$BMAD_DESIGN_ARTIFACTS"
INSTALL_EXIT_CODE=$?

if [ $INSTALL_EXIT_CODE -eq 0 ]; then
    echo -e "${VERDE}✓ bmad-method instalado correctamente.${NC}"
else
    echo -e "${ROJO}Error: Falló la instalación de bmad-method (exit code: $INSTALL_EXIT_CODE).${NC}"
    exit $INSTALL_EXIT_CODE
fi
