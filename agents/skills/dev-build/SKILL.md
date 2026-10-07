---
name: dev-build
description: Implementar una spec o story por ID o path con bmad-build y entregar estado, trazabilidad, pruebas y resultado de revisión. Usar cuando se solicite construir ese documento con este flujo.
---

# Implementar una spec o story

## Resolver la entrada

Requiere un ID o path de un documento Markdown legible. Resuelve paths desde el directorio de trabajo e IDs por nombre e identificador declarado, excluyendo informes e historial `.reviews/`. Si falta, no existe o es ambiguo, informa el problema y detente sin elegir por aproximación.

Distingue el contrato fuente de la spec operativa de build:

- Un `SPEC.md` nativo y todos sus `companions:` son el contrato fuente. Resuelve y lee los companions desde su carpeta; si alguno falta o no es legible, detente. Build puede generar otra spec operativa: no agregues `status` al kernel ni lo marques `done`.
- Una story/spec con estado reconocido por `bmad-build` se enruta según ese flujo. Un documento sin ese estado se recibe como intención, no como implementación aprobada.

Si la entrada se entrega desde una corrida `dev-apply-review`, lee su `run.json` y la última review: exige `ready`, `ready_for_dev: true`, política vigente, inventario completo y hashes actuales mediante `verify` del protocolo de `dev-review-spec`. Un estado detenido, legacy o contenido cambiado no demuestra readiness; informa el impedimento y la corrida a reanudar. No aplica este requisito a entradas ajenas al ciclo ni sustituye checkpoints/aprobaciones propios de build. Un informe vecino sin referencia a corrida es evidencia histórica, no aprobación automática.

## Ejecutar bmad-build

Localiza y lee `bmad-build` y `bmad-agent-dev`; si falta alguno, detente e informa el impedimento. Adopta el rol y ejecuta `bmad-build` con el path absoluto, respetando activación, renderizado y workflow.

Coordina desde el principal: build ya delega trabajo y revisión. Delega la coordinación si se solicita o conviene separar una ejecución extensa. Sin subagentes, sigue las alternativas y escalaciones de build, incluida revisión humana cuando corresponda.

Conserva la separación de contexto de implementadores y revisores. Libera agentes terminados y organiza tandas según capacidad, sin omitir controles. Al delegar, pasa directorio del proyecto, paths absolutos de entrada, companions y skills, decisiones y contrato de resultado. El hijo debe leerlos y seguirlos.

Antes de implementar, verifica que la spec operativa preserva requisitos, restricciones, IDs y aceptación de la fuente y companions; usa `context:` para material que el implementador deba leer. Mantén la trazabilidad y no modifiques el kernel ni su memoria como parte de la implementación.

Respeta aprobaciones, detenciones y autorización vigente. Resuelve decisiones del usuario antes del trabajo dependiente; retransmite preguntas y respuestas si delegas. No cambies configuración BMAD ni inicies otros flujos de entrega.

## Límites de escritura e índice de specs

Conserva las escrituras de implementación de `bmad-build` y el contrato fuente de lectura. La excepción a esos límites es la entrada de la spec suelta en el índice central y su `last_updated`. No escribas `status` en `SPEC.md`, `.memlog.md` ni companions; no modifiques `stories.yaml` ni dupliques estados por story.

Si la entrada es una story de un epic, no toques `specs:`. Para una spec suelta, identifica su kernel nativo y slug desde la fuente/trazabilidad real; no uses el nombre de la spec operativa como slug ni inventes una correspondencia.

Resuelve `{implementation_artifacts}/sprint-status.yaml` desde `implementation_artifacts` en `_bmad/config.toml` del proyecto, expandiendo `{project-root}`; no fuerces paths. Requiere archivo, mapping `specs:` y entrada `spec-<slug>` existentes. Si no puedes resolver la ruta, identificar la spec suelta o encontrar archivo/sección/entrada, avisa en la entrega y continúa; no los crees, esa creación corresponde a `dev-spec`.

Coordina la sincronización durante `bmad-build`, también si delegas: registra `operative:` en cuanto exista la spec operativa y `stories:` solo si existe `stories.yaml` de la spec nativa, ambos relativos a la raíz del proyecto. Conserva `spec:` apuntando al kernel real, también relativo a la raíz. No generes archivos para llenar campos ni incluyas rutas de archivos inexistentes.

Lee el frontmatter `status` de la spec operativa en cada transición: al empezar la implementación sincroniza `in-progress`; al pasar a revisión, `in-review → review`; al cerrar, `done`. Los estados `backlog` y `ready-for-dev` conservan su nombre. Sin frontmatter legible con estado reconocido, no inventes un estado: informa la limitación. El frontmatter es la fuente de verdad; si discrepa del YAML, corrige el índice y menciónalo en la entrega. No adelantes estado por el resumen de un delegado ni por la intención de iniciar/cerrar.

Orden: `backlog → ready-for-dev → in-progress → review → done`. No retrocedas salvo petición explícita del flujo; la reconciliación de una discrepancia con el frontmatter prevalece sobre ese orden. Si ya está igual o más avanzado que un destino propuesto y coincide con el frontmatter, no cambies el estado; registra solo rutas nuevas/corregidas cuando corresponda.

Edita únicamente la entrada en curso y `last_updated` (`MM-DD-YYYY HH:MM`, hora del proyecto) cuando haya cambios. Preserva comentarios, orden, `references:`, `development_status`, demás campos y entradas ajenas. Valida YAML antes y después, usa edición localizada o YAML que preserve formato y comprueba el diff; si no se puede parsear o editar limpiamente, no fuerces el cambio, avisa y continúa. Relee el estado operativo al entregar y sincroniza si corresponde, incluso en una ejecución bloqueada; un bloqueo no implica `done` ni autoriza retroceder.

## Verificar y entregar

Conserva los controles de la ruta ejecutada: diff, aceptación, pruebas y revisión correspondientes. No sustituyas evidencia por el resumen del implementador ni repitas pruebas satisfactorias sin motivo. Si delegas, contrasta artefactos y cambios reales con el retorno y solicita faltantes al mismo hijo.

Devuelve en español un resultado compacto por unidad implementada:

- `done` o `blocked`, motivo del bloqueo y estado operativo real si quedó esperando aprobación o listo para continuar.
- Paths efectivos del contrato fuente y de la spec operativa creada o resumida; archivos modificados relevantes.
- Qué cambió; comandos ejecutados, directorio y resultados. Distingue comandos propuestos y verificaciones manuales de comprobaciones realizadas.
- Resultado de revisión, capas ejecutadas, pendientes/riesgos y trabajo diferido; commit si el flujo lo creó.
- Cambio del índice, rutas registradas, discrepancias reconciliadas o motivo por el que no se escribió.

`done` requiere completar la ruta correspondiente y sus controles. Una entrega fallida, incompleta, pendiente de aprobación o sin revisión requerida no es `done`. No marques la fuente como completada solo porque la spec operativa lo esté.
