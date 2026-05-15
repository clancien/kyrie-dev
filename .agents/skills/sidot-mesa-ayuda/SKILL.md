---
name: sidot-mesa-ayuda
description: "Gestionar solicitudes de reinicio de clave SIDOT en GitLab siguiendo el protocolo oficial de Mesa de Ayuda. Usar cuando se necesite triage, validación, respuesta y cierre de issues/work items de acceso SIDOT. Este skill debe apoyarse en el skill gitlab-connect para listar y actualizar work items, y en el skill sidot-connect para consultar/validar datos del usuario en la plataforma SIDOT."
---

# SIDOT Mesa Ayuda

## Objetivo

Ejecutar el flujo de Mesa de Ayuda SIDOT para solicitudes de clave, desde la revisión del work item hasta su cierre, usando respuestas estandarizadas y validaciones obligatorias.

## Flujo Operativo

1. Obtener y registrar trabajo pendiente:
- Usar el skill `gitlab-connect` para listar work items/issues asignados (priorizar estado `opened`).
- Filtrar **obligatoriamente** por `GITLAB_PROJECT_ID` definido en `.env`.
- Guardar metadata relevante (IID, título, autor, URL, etiquetas) en `doc/.sidot/git-tickets.json`.
- Identificar el item objetivo y leer título, descripción, comentarios y datos del solicitante.

2. Validar datos mínimos del solicitante:
- Nombre completo, RUT, Institución, Correo de uso exclusivo.
- El correo del solicitante debe obtenerse siempre desde el campo GitLab `service_desk_reply_to` de `GET /projects/<GITLAB_PROJECT_ID>/issues/<issue_iid>`. No usar la descripción del issue ni el autor `support-bot` como fuente del correo.
- Si faltan datos críticos, responder con plantilla de información incompleta y cerrar.
- Actualizar `doc/.sidot/git-tickets.json` con los datos extraídos del solicitante.

3. Verificar elegibilidad en SIDOT:
- Usar el skill `sidot-connect` para buscar al usuario.
- **Obligatorio**: Validar existencia y estado (habilitado) antes de proceder.
- Guardar `usuarioId`, `login`, estado y link directo del usuario SIDOT sin parámetro `state` (`sidot_user.url`, formato `/pref/usuario/edit/<usuarioId>`) en `doc/.sidot/git-tickets.json` para el ticket correspondiente.
- Si no existe o está deshabilitado, responder con plantilla de rechazo por alcance y cerrar. **Antes de modificar GitLab**, pedir confirmación explícita al usuario indicando el issue, comentario/etiqueta/estado a aplicar y esperar aprobación.

4. Iniciar tramitación:
- **Antes de modificar GitLab**, pedir confirmación explícita al usuario indicando el issue, comentario/etiqueta/estado a aplicar y esperar aprobación.
- Publicar plantilla de "en proceso".
- Cambiar etiquetas/estado del work item a en curso.
- Enviar solicitud de validación al equipo administrador SIDOT. Para esto generar un link en formato "mailto:" y entregarlo por pantalla al usuario.

5. Aplicar reinicio de clave:
- Leer `usuarioId` y `login` desde `doc/.sidot/git-tickets.json` para asegurar consistencia.
- Generar clave temporal robusta de 20 caracteres con símbolos.
- **Antes de modificar SIDOT**, pedir confirmación explícita al usuario indicando `usuarioId`, `login` y acción de reinicio de clave, sin exponer la clave temporal.
- Aplicar cambio de clave en SIDOT.
- **Obligatorio**: Verificar que el login con la nueva clave funciona antes de informar al usuario.

6. Informar y cerrar:
- **Antes de modificar GitLab**, pedir confirmación explícita al usuario indicando el comentario de entrega y el cierre/etiquetas a aplicar.
- Publicar plantilla de entrega de clave temporal.
- Marcar item como cerrado y actualizar estado en `doc/.sidot/git-tickets.json`.

## Reglas

- **Confirmación obligatoria antes de modificar datos**: Antes de cualquier acción que modifique datos en GitLab o SIDOT, pedir confirmación explícita al usuario y esperar respuesta afirmativa. Esto aplica a publicar notas, cambiar etiquetas, cerrar/reabrir issues, cambiar estado de work items, reiniciar claves, guardar formularios SIDOT o cualquier `POST`/`PUT`/`PATCH`/`DELETE` con efecto persistente. No asumir confirmación por contexto, urgencia, automatización o ejecución previa.
- **Lecturas sin confirmación**: Consultas `GET`, búsquedas, validaciones y generación de `mailto:` no requieren confirmación si no persisten cambios en GitLab o SIDOT.
- **Persistencia de Datos**: Mantener `doc/.sidot/git-tickets.json` actualizado con el mapeo `issue_iid -> {usuario_sidot_id, login, nombre, rut, estado}`.
- **Validación Previa**: No intentar modificar una clave sin haber validado primero la existencia y estado activo del usuario en SIDOT.
- **Verificación Post-Acción**: Tras un cambio de clave, realizar una prueba de login (vía script o manual) para confirmar que la nueva clave es válida.
- No inventar datos del solicitante ni del usuario SIDOT.
- No exponer tokens, credenciales ni datos sensibles en logs.
- Mantener trazabilidad: registrar qué validaciones se realizaron.
- Usar plantillas de `assets/` y adaptarlas al caso concreto.
- En la solicitud de validación a administradores MINSAL, incluir siempre el `Link usuario SIDOT` tomado desde `sidot_user.url`.
- En comentarios al solicitante, reemplazar `Estimad@` por saludo personalizado según nombre+sexo.
- Si hay ambigüedad de identidad (RUT/correo no coinciden), pausar cierre y solicitar aclaración.
- El alcance de consulta en GitLab debe restringirse **siempre** al proyecto `GITLAB_PROJECT_ID`.

## Recursos

- **Índice de Tickets**: `doc/.sidot/git-tickets.json`
- Plantillas de comentario y correo: `assets/templates.md`
- Plantilla de checklist operativo: `assets/checklist.md`
- Plantilla de resumen de resolución: `assets/resumen-cierre.md`
- Automatización de reset/cierre: `assets/reset_password_from_issue.py`

## Comandos de Referencia

Usar como base operativa los comandos definidos en:

- Skill `gitlab-connect`: listar proyectos, work items/issues y comentar/cerrar.
- Skill `sidot-connect`: búsqueda y validación del usuario SIDOT, y actualización de clave.

Condición obligatoria para este skill:

- Toda consulta de work items/issues debe ejecutarse con filtro de proyecto `GITLAB_PROJECT_ID`.


## Ejecución asistida (automatizada)

Comando recomendado para resolver un issue de clave de punta a punta:

```bash
python3 .agents/skills/sidot-mesa-ayuda/assets/reset_password_from_issue.py \
  --project-root "$PWD" \
  --issue-iid 102
```

La automatización debe solicitar confirmación interactiva antes de cada modificación persistente en GitLab o SIDOT. Si la ejecución no tiene terminal interactiva, debe detenerse antes de modificar datos.

Opcional:

- `--sidot-user-query "Cmiranda"` para forzar la búsqueda del usuario SIDOT.
- Si no se informa `--sidot-user-query`, el script intenta inferir la búsqueda desde `Usuario`, `usuario sidot`, `login`, `service_desk_reply_to` o `Nombre completo` del issue.
- `--solicitante-nombre "Juan Carlos Pérez"` para fijar saludo.
- `--sexo M|F` para fijar tratamiento (`Estimado`/`Estimada`) cuando la inferencia no sea clara.
- `--skip-start-note` para no publicar nuevamente la plantilla "en proceso" cuando el issue ya fue tramitado y solo falta aplicar el reinicio aprobado.
- `--skip-close` para publicar clave temporal sin cerrar inmediatamente el issue.

Notas de implementación:

- Para reiniciar clave en `/pref/usuario/save`, enviar estos campos del formulario de edición: `__csrftoken`, `usuarioId`, `state`, `contrasenaNew`, `contrasenaRepeat`, `hospitalesProcuramientoIds` y `hospitalesTrasplantesIds`.
- Enviar `hospitalesProcuramientoIds` y `hospitalesTrasplantesIds` como campos repetidos cuando tengan más de un valor. Si el `select multiple` viene vacío en el HTML inicial, tomar los valores desde `struts.hiddenHospitalesProcuramientoIds[data-values]` y `struts.hiddenHospitalesTrasplantesIds[data-values]`.
- No enviar el formulario completo de usuario para un reinicio de clave: otros `select` dependientes se completan por JavaScript y el POST completo puede volver al formulario sin persistir la nueva clave.
- Al cerrar, la automatización agrega `Estado: Cerrado`, remueve `Estado: En proceso` y ejecuta `state_event=close`.
- Si la búsqueda de usuario SIDOT devuelve más de una cuenta editable, la automatización se detiene por ambigüedad.

## Integración API Skills

- Conectividad GitLab: usar cliente de `gitlab-connect` (`assets/api.py`).
- Conectividad SIDOT: usar cliente de `sidot-connect` (`assets/api.py`).
- Evitar duplicar lógica HTTP directa del servicio en este skill.

Métodos usados por este skill:
- GitLab:
  - `GitLabClient.get("/projects/<id>/issues/<iid>")`
  - `GitLabClient.post("/projects/<id>/issues/<iid>/notes", form={"body": ...})`
  - `GitLabClient.put("/projects/<id>/issues/<iid>", form={"add_labels": ..., "remove_labels": ..., "state_event": "close"})`
- SIDOT:
  - `SidotClient.login()`
  - `SidotClient.get("/pref/usuario/?busqueda.query=...")`
  - `SidotClient.session.post("/pref/usuario/save", data={...})` para persistir cambio de clave con cookies de sesión y payload mínimo.
