# Manual de uso de bmad

### 1. Preparación y Alineación (Fase 0)

**`bmad-bmb-setup`**: Instalar el módulo base de BMad en el repositorio para tener la estructura de `/doc` y `_bmad` lista.
**`bmad-document-project`** (**CRÍTICO**): Este es el paso más importante. El skill escaneará el proyecto existente para generar el `project-context.md`. Sin esto, el agente no conocerá las dependencias actuales, la arquitectura de rutas o los componentes personalizados que podrían romperse.

### 2. Definición del Objetivo (Análisis)
**`bmad-create-prd`**: Crea un documento de requerimientos donde se especifique la versión de salida y la versión destino (ej. Laravel 10 -> 11). Aquí se documentan las motivaciones técnicas y las dependencias críticas que deben actualizarse (PHP, Composer, NPM).

**`bmad-validate-prd`**: Útil ahora porque acabamos de editar el PRD y cambió la secuencia de épicas. Validaría consistencia, huecos, trazabilidad, numeración, riesgos y si el PRD ya está suficientemente claro para alimentar arquitectura.

**`bmad-technical-research`**: Investiga tanta veces sea necesario para obtener información relevante.

**`bmad-agent-tech-writer`**: con acción Validate Document: revisar claridad/documentación del PRD o inventario, no es gate BMad principal.

### 3. Diseño de la Arquitectura y Estrategia de implementación
**`bmad-create-architecture`**: La arquitectura va a tomar decisiones técnicas desde ese PRD; si el PRD todavía tiene inconsistencias, las amplifica.

**`bmad-create-epics-and-stories`**: Crea los epics y indica de historias.
- aplicar [A] Advanced Elicitation + [P] Party Mode para todas las historias, para afinar su definción

**`bmad-check-implementation-readiness`**: Gate final antes de implementar: revisa PRD + arquitectura + épicas/stories.
- si requiere trabajo aun despues de este paso, se puede usar **`bmad-correct-course`** para corregirlo.

**`bmad-sprint-planning`**: Genera el `sprint-status.yaml` para trackear el progreso.
**`bmad-sprint-status`**: Para validar el sprint-status


### 4. Ejecución de las historias
**`bmad-create-story`** crea la siguiente historia: 1-1-capturar-linea-base-ejecutable-del-entorno
**`bmad-create-story`** valida la historia creada
**`bmad-dev-story`** implementa la historia validada
**`bmad-code-review`** revisa el cambio
**`bmad-qa-generate-e2e-tests`**: Si el proyecto no tenía tests, este es el momento de generar pruebas de humo en las rutas críticas para asegurar que el salto de versión no rompió el flujo principal.


