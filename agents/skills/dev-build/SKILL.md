---
name: dev-build
description: Implementar una spec o story por ID o path con bmad-build y entregar estado, trazabilidad, pruebas y resultado de revisión. Usar cuando se solicite construir ese documento con este flujo.
---

# Implementar una spec o story

## Resolver la entrada

Requiere un ID o path de un documento Markdown legible. Resuelve paths desde el directorio de trabajo e IDs por nombre e identificador declarado, excluyendo `.review.md`. Si falta, no existe o es ambiguo, informa el problema y detente sin elegir por aproximación.

Distingue el contrato fuente de la spec operativa de build:

- Un `SPEC.md` nativo y todos sus `companions:` son el contrato fuente. Resuelve y lee los companions desde su carpeta; si alguno falta o no es legible, detente. Build puede generar otra spec operativa: no agregues `status` al kernel ni lo marques `done`.
- Una story/spec con estado reconocido por `bmad-build` se enruta según ese flujo. Un documento sin ese estado se recibe como intención, no como implementación aprobada.

## Ejecutar bmad-build

Localiza y lee `bmad-build` y `bmad-agent-dev`; si falta alguno, detente e informa el impedimento. Adopta el rol y ejecuta `bmad-build` con el path absoluto, respetando activación, renderizado y workflow.

Coordina desde el principal: build ya delega trabajo y revisión. Delega la coordinación si se solicita o conviene separar una ejecución extensa. Sin subagentes, sigue las alternativas y escalaciones de build, incluida revisión humana cuando corresponda.

Conserva la separación de contexto de implementadores y revisores. Libera agentes terminados y organiza tandas según capacidad, sin omitir controles. Al delegar, pasa directorio del proyecto, paths absolutos de entrada, companions y skills, decisiones y contrato de resultado. El hijo debe leerlos y seguirlos.

Antes de implementar, verifica que la spec operativa preserva requisitos, restricciones, IDs y aceptación de la fuente y companions; usa `context:` para material que el implementador deba leer. Mantén la trazabilidad y no modifiques el kernel ni su memoria como parte de la implementación.

Respeta aprobaciones, detenciones y autorización vigente. Resuelve decisiones del usuario antes del trabajo dependiente; retransmite preguntas y respuestas si delegas. No cambies configuración BMAD ni inicies otros flujos de entrega.

## Verificar y entregar

Conserva los controles de la ruta ejecutada: diff, aceptación, pruebas y revisión correspondientes. No sustituyas evidencia por el resumen del implementador ni repitas pruebas satisfactorias sin motivo. Si delegas, contrasta artefactos y cambios reales con el retorno y solicita faltantes al mismo hijo.

Devuelve en español un resultado compacto por unidad implementada:

- `done` o `blocked`, motivo del bloqueo y estado operativo real si quedó esperando aprobación o listo para continuar.
- Paths efectivos del contrato fuente y de la spec operativa creada o resumida; archivos modificados relevantes.
- Qué cambió; comandos ejecutados, directorio y resultados. Distingue comandos propuestos y verificaciones manuales de comprobaciones realizadas.
- Resultado de revisión, capas ejecutadas, pendientes/riesgos y trabajo diferido; commit si el flujo lo creó.

`done` requiere completar la ruta correspondiente y sus controles. Una entrega fallida, incompleta, pendiente de aprobación o sin revisión requerida no es `done`. No marques la fuente como completada solo porque la spec operativa lo esté.
