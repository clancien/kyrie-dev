Actúa como ORQUESTADOR AUTÓNOMO de sprint en /home/clancien/workspace/PROYECT_NAME.

Parámetro único:
EPIC_OBJETIVO="8"

Objetivo:
Lee `doc/implementation-artifacts/sprint-status.yaml` y completa las tareas pendientes de la Epic seleccionada (`## Epic ${EPIC_OBJETIVO}`),  usando los prompts de `doc/implementation-artifacts/sprint-prompt.md`.
Ignora cualquier pendiente fuera de esa Epic.
Completa las tareas en subagents sin contexto previo, para cuidar el uso de la ventana de contexto.
Actualiza sprint-prompt.md a medida que ejecutaste los prompts.

Reglas duras:
1) No te detengas hasta que en la Epic objetivo no quede ningún `- []`.
2) No ejecutes tareas de otras Epics.
3) Flujo por historia pendiente dentro de la Epic:
   A) `$bmad-create-story` crea historia
   B) `$bmad-create-story` valida historia
   C) `$bmad-dev-story` implementa historia
   D) `$bmad-code-review` revisa cambio
   E) aplicar fixes si hay hallazgos críticos
   F) marcar `[x]` en `sprint-prompt.md`
4) Si una tarea falla, crear subtarea de corrección y reintentar hasta cerrar.
5) No correr suite completa de tests salvo pedido explícito; validar sintaxis puntual cuando aplique.

Subagentes (usar prompt corto):
- Implementación: "Implementa solo la historia <ID> de Epic <EPIC_OBJETIVO>. Sin refactor fuera de alcance."
- Review: "Revisa solo el diff de <ID>. Reporta bugs/regresiones/riesgos accionables."
- Validación: "Confirma que <ID> quedó en [x] dentro de la Epic <EPIC_OBJETIVO>."

Criterio de salida:
- Releer `doc/implementation-artifacts/sprint-prompt.md`.
- Si en `## Epic ${EPIC_OBJETIVO}` no existe `- []`, finalizar con resumen.
- Si existe al menos un `- []`, continuar automáticamente.
