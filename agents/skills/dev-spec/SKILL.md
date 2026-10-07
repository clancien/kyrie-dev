---
name: dev-spec
description: Preparar una spec BMAD desde un requerimiento, aclarar decisiones pendientes y recomendar implementación completa o por stories. Usar cuando se solicite preparar una funcionalidad con este flujo; no implementa código.
---

# Preparar una spec

## Reunir el contexto

Recibe un requerimiento en texto o un documento legible e inequívoco. Si falta o la referencia no se resuelve, pide corregir la entrada antes de redactar.

Inspecciona las instrucciones y los hechos del proyecto necesarios para reunir:

- Nombre y slug en minúsculas con guiones.
- Problema, objetivo de negocio y destinatarios.
- Requerimientos, reglas de negocio y casos límite.
- Stack, integraciones, convenciones y requisitos no funcionales.
- Alcance, exclusiones y resultados observables de éxito.

Con información suficiente, pasa a redactar. Pregunta en bloques solo por decisiones pendientes; no preguntes hechos verificables en el repositorio ni inventes decisiones de producto. Resuelve ambigüedades de comportamiento antes del trabajo dependiente. Marca inferencias no confirmadas como `[SUPUESTO]`; distingue restricciones desconocidas de las que no aplican.

## Ejecutar bmad-spec

Localiza y lee `bmad-spec`. Selecciona solo las perspectivas necesarias: `bmad-agent-analyst` para requisitos, `bmad-agent-architect` para decisiones técnicas y `bmad-agent-ux-designer` para UI y sus estados. Explica la selección y lee esos skills; si falta una dependencia necesaria, informa el impedimento y detente. Varios roles dentro de un agente no son revisiones independientes.

Ejecuta directamente o delega para separar autoría y comprobación en specs extensas; respeta la modalidad solicitada. Sin subagentes, continúa directamente. Al delegar, pasa directorio del proyecto, paths absolutos de skills y fuentes, hechos y decisiones. El hijo debe leer y seguir los skills; evita duplicar investigaciones resueltas.

Ejecuta `bmad-spec` con nombre, slug, objetivo, requerimientos, restricciones y límites. Exige:

- Carpeta nativa según la configuración; no fuerces paths ni cambies la configuración BMAD.
- Kernel, IDs estables, `.memlog.md` canónica y companions conforme a BMAD. Los cambios se registran en memoria y se derivan mediante `bmad-spec`; no parches `SPEC.md` manualmente.
- Aceptación observable en Given/When/Then; si requiere un companion, referéncialo desde `SPEC.md`.
- `[SUPUESTO]` donde corresponda y "Fuera de alcance" explícito en Non-goals.

No implementes código ni crees stories. Si delegas, el hijo envía decisiones pendientes al principal y espera las respuestas del usuario antes del trabajo dependiente. Respeta la salida nativa de `bmad-spec`, incluido su JSON headless; el coordinador lee los artefactos y prepara la entrega del wrapper. Recomienda una corrida para un cambio cohesivo verificable conjuntamente, o stories para entregas independientes/dependencias por etapas; justifica y añade un plan breve en la respuesta, no en el kernel ni en `companions:`. El retorno delegado resume paths, supuestos, pendientes y recomendación, sin copiar los documentos.

## Comprobar la entrega

Lee `SPEC.md`, `.memlog.md` y los companions referenciados. Comprueba que existen, sus referencias se resuelven y preservan los requerimientos, restricciones y decisiones; que mantienen el formato e IDs BMAD; y que incluyen aceptación, supuestos y exclusiones acordados. Respeta la propiedad de companions adoptados: se referencian, no se editan como documentos propios.

Contrasta artefactos y cambios reales con el contexto y alcance, no solo con el resumen del autor. Corrige faltantes mediante `bmad-spec` o con el mismo hijo y verifica de nuevo. Si falla, comunica lo generado y las decisiones pendientes que impiden implementar; crear una spec no demuestra readiness.

## Límites de escritura e índice de specs

Las escrituras de producto se limitan a memoria, kernel y companions propios mediante `bmad-spec`. La excepción es el índice central siguiente; no escribas `status` en `SPEC.md`, `.memlog.md` ni companions, ni modifiques `stories.yaml`.

Solo después de comprobar con éxito la spec creada/actualizada, resuelve `{implementation_artifacts}/sprint-status.yaml` desde `implementation_artifacts` en `_bmad/config.toml` del proyecto, expandiendo `{project-root}`. No fuerces paths ni cambies configuración; si no puedes resolverla, avisa en la entrega y continúa.

Usa `specs:` como mapping y la clave `spec-<slug>` de la carpeta nativa. Crea o actualiza su entrada con `status: backlog` y `spec:` apuntando al kernel real (habitualmente `docs/specs/<slug>/SPEC.md`), relativo a la raíz del proyecto. Si la entrada ya está más avanzada que `backlog`, déjala igual. El orden es `backlog → ready-for-dev → in-progress → review → done`: a igual estado no reescribas una entrada ya correcta; no retrocedas salvo petición explícita del flujo.

Solo este skill puede crear el archivo o la sección `specs:` ausentes. Para un archivo nuevo, copia el encabezado y la estructura básica del sprint-status/template BMAD de referencia, adaptando los datos al proyecto: `generated`, `last_updated`, `project`, `project_key`, `tracking_system`, `story_location`, `references`, `specs` y `development_status: {}`. No copies epics, stories ni entradas del proyecto de referencia. Si falta solo `specs:`, añade ese mapping sin reconstruir el archivo.

En un archivo existente, edita únicamente la entrada en curso y `last_updated` (`MM-DD-YYYY HH:MM`, hora del proyecto) cuando haya cambios. Preserva comentarios, orden, `references:`, `development_status`, campos existentes y entradas ajenas; usa edición localizada o YAML que preserve formato, nunca una serialización que pierda comentarios. Valida el YAML antes y después y comprueba el diff. Si no se puede parsear o editar limpiamente, no fuerces el cambio: avisa y continúa.

`operative:` y `stories:` son rutas relativas a la raíz, solo cuando existen; este flujo no genera esos archivos. Si existe spec operativa, su frontmatter `status` es la fuente de verdad (`in-review` se traduce a `review`); una discrepancia se corrige en el índice y se menciona en la entrega, sin reiniciar el estado operativo a `backlog`. La reconciliación con el frontmatter prevalece sobre el orden de avance; no deduzcas estado del kernel ni dupliques estados por story.

## Entregar y continuar

Responde en español con el enlace real a `SPEC.md`, supuestos, pendientes y plan. Lista el cambio del índice, su estado conservado o el motivo por el que no se escribió. Entrega prompts con paths verificados, entre comillas si contienen espacios:

```text
/dev-review-spec <PATH-DE-LA-SPEC>
/dev-apply-review <PATH-DE-LA-SPEC>
```

Son pasos para continuar, no ejecuciones de este flujo; `dev-apply-review` requiere el informe previo y ejecuta automáticamente el loop acotado de aplicación y revisiones completas hasta readiness o una parada explícita. No es necesario repetir manualmente review/apply. Major pendientes impiden readiness; minor opcionales pueden acompañar `LISTO CON OBSERVACIONES`.

- Una corrida: `/dev-build <PATH-DE-LA-SPEC>`.
- Por stories: `/bmad-create-epics-and-stories <PATH-DE-LA-SPEC>` y `/dev-build <PATH-DE-CADA-STORY>`, una vez por story en orden de dependencias. Si aún no existen, conserva el placeholder y explica que las rutas se obtienen al crearlas; no inventes nombres.

Aclara que build puede generar una spec operativa distinta tomando `SPEC.md` y sus companions como contrato fuente.
