# Epic 1: Agente Orquestador de Desarrollo (Ollama + Codex CLI sobre LangGraph)

**Fuente:** Conversación de planificación técnica — decisión de arquitectura del [YYYY-MM-DD]  
**Nivel de proyecto:** 3 (multi-componente, requiere arquitectura previa)  
**Owner:** Scrum Master Agent (bmad sm)

## Objetivo del Epic

Construir un agente autónomo local, orquestado con LangGraph, capaz de desarrollar una aplicación completa combinando dos motores de IA con roles diferenciados:

- **Ollama** (modelo local) planifica, revisa diffs y genera documentación.
- **Codex CLI** ejecuta tareas en un worktree aislado, corre verificaciones y produce cambios candidatos.

El sistema debe resistir reinicios, mantener trazabilidad verificable desde la tarea hasta el SHA fusionado, detener acciones irreversibles para decisión humana explícita y completar el objetivo sólo cuando el backlog esté conciliado.

## Alcance

**Incluye:** StateGraph, planificación/revisión con Ollama, ejecución de Codex CLI aislada, ramas o worktrees por tarea, checkpoints persistentes, logs JSONL, CLI de operación, notificación por consola y webhook configurable, merge y deploy gobernados, y un dashboard HTML local para el operador.

**No incluye:** LangGraph Platform, una SPA o framework frontend, más de un repositorio simultáneo, ni un proveedor de notificaciones concreto. El webhook es un adaptador configurable; stdout sigue disponible para operación local.

## Arquitectura y contrato operativo

```
crear run/thread_id
  → planner → executor → reviewer → human_checkpoint(merge)
       ↑          │          │              │
       └──────────┘          └─ rechazo ────┤
                  fallo recuperable          ↓
                              checkpoint de atención
                                               ↓ aprobación validada
                                      merge seguro → checkpoint(deploy)
                                                       ↓ aprobación
                                              deploy/verificación → conciliación → END
```

**Estado compartido (`AgentState`).** Debe ser JSON-serializable y contener, como mínimo: `run_id`, `thread_id`, `objetivo`, `estado_ejecucion`, `backlog`, `tarea_actual`, `task_id`, `estado_tarea`, `attempt`, `branch_or_worktree`, `base_sha`, `candidate_sha`, `ultimo_diff`, `test_summary`, `review`, `checkpoint`, `historial`, `last_event_id`, `reintentos` y `completado`.

Los valores de ciclo de vida serán cerrados: `planned`, `running`, `failed`, `awaiting_review`, `awaiting_human`, `approved`, `merged`, `cancelled`, `blocked` y `completed`. Cada nodo sólo podrá emitir una transición válida y deberá registrar un evento antes de causar un efecto externo.

**Eventos y evidencia.** `log.jsonl` es append-only y cada evento incluye `timestamp`, `run_id`, `thread_id`, `task_id`, `attempt`, `node`, transición, nivel, duración, `checkpoint_id` cuando aplique y referencias a artefactos. Prompts, diffs, stdout y stderr deben pasar por redacción de secretos antes de persistirse o notificarse.

**CLI de operación.** El sistema expone `status --thread <id>`, `logs --thread <id> [--follow]`, `checkpoints --pending` y `approve|reject|edit|cancel --checkpoint <id>`. `status` muestra el flujo actual, tarea/SHA/rama, último evento, límites restantes, checkpoint pendiente, errores accionables y el comando de reanudación.

**Dashboard local.** Un servidor Flask integrado ofrece HTML server-rendered con plantillas y CSS locales. Lee snapshots SQLite y `log.jsonl`; para resolver checkpoints llama a la misma capa de servicio que la CLI, por lo que no escribe SQLite ni eventos directamente. Un único operador accede tras superar una allowlist CIDR y autenticarse con usuario y hash de contraseña configurados por variables de entorno.

---

## Story 1.1 — Setup del proyecto, estado durable y esqueleto del grafo

**Status:** Draft

### Story
Como **desarrollador que va a operar el agente**, quiero **un proyecto Python inicializado con un `AgentState` durable y un grafo mínimo compilable**, para que **los nodos posteriores compartan un contrato seguro sin refactors estructurales**.

### Acceptance Criteria
1. **Given** una instalación limpia, **when** se instalan las dependencias, **then** `requirements.txt` fija `langgraph`, `langgraph-checkpoint-sqlite`, `requests` y la librería de validación de esquema elegida.
2. **Given** una ejecución nueva, **when** se crea `AgentState`, **then** contiene los identificadores, estados, SHAs, evidencia, checkpoint y referencias de eventos definidos por el contrato operativo, sin handles u otros objetos no serializables.
3. **Given** una actualización de estado, **when** un nodo intenta una transición no permitida, **then** se rechaza, se registra un evento de error y no se muta el estado durable.
4. **Given** `python main.py --objetivo "..."`, **when** se ejecuta el grafo placeholder, **then** crea `run_id` y `thread_id`, registra el evento inicial y termina limpiamente.

### Tasks/Subtasks
- [ ] Crear `/nodes`, `state.py`, `main.py`, `config.py` y el módulo de eventos (AC: 1, 2, 4).
- [ ] Definir tipos/enums serializables, validación de transición y estructuras de tarea, revisión, test y checkpoint en `state.py` (AC: 2, 3).
- [ ] Compilar `StateGraph(AgentState)` con `planner` placeholder, `START` y `END` (AC: 4).
- [ ] Añadir `requirements.txt` y README con instalación y ejecución local (AC: 1, 4).

### Testing
- Test unitario de serialización y de cada transición aceptada/rechazada.
- Test de humo que compila el grafo y crea una ejecución identificable.

---

## Story 1.2 — Nodo Planificador (Ollama) y conciliación de objetivo

**Status:** Draft

### Story
Como **agente orquestador**, quiero **que Ollama produzca la siguiente tarea estructurada o solicite cierre sujeto a conciliación**, para que **el objetivo avance sin repetir trabajo ni terminar prematuramente**.

### Acceptance Criteria
1. **Given** un objetivo y estado válido, **when** `planner` llama a Ollama, **then** envía el objetivo, backlog, historial relevante y límites operativos a la URL/modelo configurables.
2. **Given** una respuesta válida, **when** se acepta una tarea, **then** contiene `task_id` único, `titulo`, `descripcion`, `criterio_de_exito`, alcance permitido y dependencias, y queda en `planned`.
3. **Given** JSON inválido o un esquema inválido, **when** se procesa la respuesta, **then** se hacen como máximo dos intentos de corrección con backoff y después se registra un fallo explícito recuperable.
4. **Given** contenido de modelo, repositorio o diff no confiable, **when** se arma un prompt, **then** se delimita como datos y no puede alterar las políticas, comandos permitidos ni instrucciones del orquestador.
5. **Given** una señal `DONE`, **when** se enruta el grafo, **then** una conciliación confirma que no existen tareas pendientes, fallidas, bloqueadas o cambios sin fusionar; de lo contrario `END` queda prohibido y se abre atención humana o replanificación.

### Tasks/Subtasks
- [ ] Implementar cliente y configuración de Ollama en `nodes/planner.py` y `config.py` (AC: 1, 3).
- [ ] Validar la salida con esquema estricto, generar `task_id` y persistir la transición (AC: 2, 3).
- [ ] Delimitar entradas no confiables y registrar motivos de rechazo de salida (AC: 4).
- [ ] Implementar nodo/arista de conciliación previa a `END` (AC: 5).

### Testing
- Mocks para tarea válida, JSON malformado y una instrucción inyectada en contenido no confiable.
- `DONE` con tarea pendiente/fallida debe impedir un cierre exitoso.

---

## Story 1.3 — Nodo Ejecutor (Codex CLI) aislado y recuperable

**Status:** Draft

### Story
Como **agente orquestador**, quiero **ejecutar cada tarea con Codex CLI en un worktree aislado y con evidencia determinista**, para que **los cambios sean revisables sin modificar `main` ni exceder los permisos concedidos**.

### Acceptance Criteria
1. **Given** una tarea `planned`, **when** comienza la ejecución, **then** se crea o valida un worktree/rama dedicado, limpio y basado en un `base_sha` registrado; `main` no se modifica.
2. **Given** el worktree, **when** se invoca `codex exec`, **then** el proceso se limita al directorio de la tarea, sin secretos por defecto, sin red salvo allowlist configurable y sin permisos fuera del repositorio.
3. **Given** que Codex finaliza, **when** se recopila evidencia, **then** se persisten código de salida, timeout, stdout/stderr redactados, comando y resultado de tests, `candidate_sha` y diff exacto `base_sha..candidate_sha`.
4. **Given** error o timeout, **when** se clasifica el resultado, **then** nunca se llama a `reviewer`: un fallo recuperable vuelve al planificador con evidencia y uno no recuperable o repetido abre checkpoint `requiere_atencion`.
5. **Given** una tarea terminada, **when** se conserva o limpia su worktree/rama, **then** la decisión y ubicación quedan auditadas y no se pierde el candidato necesario para revisión o recuperación.

### Tasks/Subtasks
- [ ] Implementar creación, validación y política de retención/limpieza del worktree (AC: 1, 5).
- [ ] Invocar Codex por `subprocess` con timeout y configuración de sandbox/allowlist (AC: 2, 4).
- [ ] Capturar la evidencia contra `base_sha`, no mediante `HEAD~1` (AC: 3).
- [ ] Implementar rutas de éxito, replanificación y escalamiento sin ejecutar review sobre fallo (AC: 4).

### Testing
- Integración con tarea trivial que prueba rama, SHA y diff correctos.
- Timeout y worktree sucio: sin review, con evento y ruta de recuperación correcta.

---

## Story 1.4 — Nodo Revisor y reintentos trazables

**Status:** Draft

### Story
Como **agente orquestador**, quiero **revisar exactamente el artefacto candidato y escalar rechazos repetidos**, para que **ningún cambio incompleto llegue a una aprobación humana como si fuera válido**.

### Acceptance Criteria
1. **Given** una ejecución exitosa, **when** `reviewer` llama a Ollama, **then** recibe `base_sha..candidate_sha`, criterio de éxito y resultados de tests, y devuelve `aprobado`, `motivo`, evidencia e ítems pendientes estructurados.
2. **Given** una aprobación, **when** se guarda, **then** queda vinculada a `task_id`, intento y `candidate_sha`; cualquier cambio posterior invalida la revisión y vuelve a `awaiting_review`.
3. **Given** un rechazo, **when** se enruta, **then** se registra causa e intento, se añade al historial del planificador y se vuelve a planificar sin perder la evidencia anterior.
4. **Given** que se supera el umbral configurable de reintentos, **when** se evalúa la arista, **then** se crea un checkpoint durable `requiere_atencion` en vez de iterar indefinidamente.

### Tasks/Subtasks
- [ ] Implementar `nodes/reviewer.py` y su esquema de veredicto (AC: 1).
- [ ] Definir `route_after_review`, invalidación por SHA y registro de intentos (AC: 2, 3).
- [ ] Escalar con motivo/evidencia enlazados al checkpoint (AC: 4).

### Testing
- Aprobación, rechazo y modificación de SHA posterior a aprobación.
- El cuarto rechazo abre checkpoint y no llama de nuevo al planner.

---

## Story 1.5 — Persistencia, idempotencia e inspección de ejecuciones

**Status:** Draft

### Story
Como **operador que deja el agente ejecutándose durante horas**, quiero **reanudación durable e idempotente con una vista de ejecución**, para que **un reinicio no repita efectos externos ni oculte un bloqueo**.

### Acceptance Criteria
1. **Given** una ejecución, **when** un nodo completa una transición, **then** `SqliteSaver` persiste el estado y un evento append-only asociado al mismo `thread_id`.
2. **Given** un reinicio antes, durante o después de crear worktree, ejecutar Codex, interrumpir o fusionar, **when** se usa `--resume <thread_id>`, **then** cada `operation_id` realiza su efecto como máximo una vez.
3. **Given** dos procesos sobre la misma ejecución, **when** intentan operar el mismo `thread_id`, **then** un lock impide concurrencia y una SQLite bloqueada/corrupta falla de forma segura con diagnóstico.
4. **Given** una ejecución persistida, **when** el operador usa `status --thread <id>`, **then** ve objetivo, nodo/tarea, estado, último evento, límites, errores, checkpoint pendiente y comando de reanudación; `list-runs` enumera ejecuciones resumidas.

### Tasks/Subtasks
- [ ] Configurar `SqliteSaver`, `thread_id`, `operation_id` y lock por ejecución (AC: 1–3).
- [ ] Implementar `--resume`, `list-runs` y `status --thread` desde snapshots y eventos (AC: 2, 4).
- [ ] Manejar bloqueo/corrupción de SQLite preservando diagnóstico y sin continuar efectos (AC: 3).

### Testing
- Integración de reinicio en los cuatro puntos críticos sin duplicar un efecto.
- Dos procesos y base SQLite bloqueada/corrupta dejan estado seguro y diagnosticable.

---

## Story 1.6 — Checkpoint humano durable y notificado

**Status:** Draft

### Story
Como **responsable del repositorio**, quiero **recibir y resolver checkpoints identificables antes de acciones sensibles**, para que **la ejecución permanezca pausada, informada y recuperable hasta una decisión explícita**.

### Acceptance Criteria
1. **Given** merge, deploy o atención requerida, **when** se crea un checkpoint, **then** `interrupt()` persiste una solicitud JSON-serializable con `checkpoint_id`, razón, severidad, tarea/rama/SHA, diff resumido, tests, revisión y acciones permitidas.
2. **Given** un checkpoint pendiente, **when** se notifica, **then** se muestra en consola y se entrega por webhook configurable con `run_id`, `checkpoint_id`, acción requerida y comando `status`; los envíos se reintentan con backoff y se deduplican por `checkpoint_id`.
3. **Given** que el operador no responde, **when** vence la política de espera/reaviso, **then** el estado sigue en `awaiting_human`, es recuperable y nunca se autoaprueba.
4. **Given** una decisión, **when** el operador usa `approve`, `reject`, `edit` o `cancel`, **then** se valida el payload y se reanuda con el mismo `thread_id` mediante `Command(resume=...)`; editar/rechazar/cancelar invalida la aprobación previa y conserva comentario/auditoría.
5. **Given** una aprobación de merge, **when** se intenta proceder, **then** se vuelven a validar rama, SHA aprobado, worktree limpio, tests obligatorios, base actualizada y ausencia de conflictos; se registra aprobador, timestamp, comentario y resultado.

### Tasks/Subtasks
- [ ] Implementar `nodes/human_checkpoint.py`, solicitud durable y adaptación a `interrupt()` (AC: 1, 4).
- [ ] Crear adaptadores stdout/webhook y política de configuración, reintento y deduplicación (AC: 2, 3).
- [ ] Implementar comandos de decisión y registro de auditoría (AC: 4).
- [ ] Validar precondiciones de merge antes de delegar en Story 1.8 (AC: 5).

### Testing
- Operador ausente: aviso/reaviso sin duplicados y sin autoaprobación.
- Decisiones válidas/inválidas y SHA/worktree obsoleto bloquean el avance.

---

## Story 1.7 — Observabilidad y límites operacionales

**Status:** Draft

### Story
Como **operador sin supervisión constante**, quiero **seguir la ejecución, sus evidencias y sus límites desde CLI**, para que **pueda intervenir antes de un bloqueo, error o consumo indefinido**.

### Acceptance Criteria
1. **Given** cada transición o efecto externo, **when** ocurre, **then** se agrega un evento JSONL correlacionado y redactado de secretos; prompts, diffs y salidas nunca exponen valores sensibles.
2. **Given** un operador, **when** ejecuta `status`, `logs --follow` o `checkpoints --pending`, **then** puede visualizar el recorrido `planner → executor → reviewer → awaiting_human → merge → deploy → completed` y su evidencia disponible.
3. **Given** que se alcanza el máximo configurable de iteraciones (100) o tiempo (8 h), **when** se detecta el límite, **then** se emite `limit_reached`, se conserva checkpoint y se bloquea/escala; no se produce un `END` indistinguible de éxito.
4. **Given** el cierre de una ejecución, **when** se genera el resumen final, **then** informa motivo de término, tareas completadas/pendientes/fallidas, checkpoint pendiente, ramas/SHA sin fusionar, fallos accionables y ubicación de evidencia.

### Tasks/Subtasks
- [ ] Implementar escritor JSONL append-only, correlación y redacción centralizada (AC: 1).
- [ ] Implementar `logs --follow` y `checkpoints --pending`; integrar su salida con `status` (AC: 2).
- [ ] Centralizar límites y rutas a `blocked`/checkpoint (AC: 3).
- [ ] Construir resumen final desde estado y eventos, incluso ante excepción no capturada (AC: 4).

### Testing
- Un secreto inyectado en stdout, diff o prompt no aparece en log ni notificación.
- Límite bajo, error no capturado y cierre normal generan estados/resúmenes distinguibles.

---

## Story 1.8 — Merge y deploy gobernados

**Status:** Draft

### Story
Como **responsable de entrega**, quiero **fusionar y desplegar sólo artefactos aprobados en checkpoints separados**, para que **cada acción irreversible sea verificable, autorizada y recuperable**.

### Acceptance Criteria
1. **Given** una aprobación de merge aún válida, **when** se ejecuta el merge, **then** se fusiona sólo el `candidate_sha` aprobado tras las validaciones de Story 1.6, se verifica el resultado post-merge y se registra el SHA fusionado.
2. **Given** conflicto, test post-merge fallido o incertidumbre de estado, **when** falla el merge, **then** no se despliega, el estado queda bloqueado/recuperable y se abre checkpoint de atención con evidencia.
3. **Given** un deploy configurado y merge verificado, **when** se propone el deploy, **then** se crea un checkpoint humano independiente que identifica entorno, artefacto/SHA, plan y resultado esperado.
4. **Given** que falta aprobación específica de deploy, tests o merge verificado, **when** se intenta desplegar, **then** la operación se rechaza y se registra el motivo.
5. **Given** una aprobación de deploy, **when** finaliza la operación, **then** se persisten resultado, evidencia y procedimiento de rollback o fallo seguro antes de permitir la conciliación final.

### Tasks/Subtasks
- [ ] Implementar merge seguro, verificación post-merge y evento auditable (AC: 1, 2).
- [ ] Implementar checkpoint de deploy independiente y validación de precondiciones (AC: 3, 4).
- [ ] Registrar resultado de deploy y rollback/fallo seguro para conciliación (AC: 5).

### Testing
- Aprobación con SHA obsoleto, conflicto y test post-merge fallido no despliegan.
- Deploy configurado sin aprobación se bloquea; con aprobación registra evidencia y resultado.

---

## Story 1.9 — Dashboard HTML seguro para operación humana

**Status:** Draft

### Story
Como **operador autorizado**, quiero **visualizar el estado e historial de las ejecuciones y responder checkpoints desde un dashboard HTML ligero**, para que **pueda supervisar y decidir acciones sensibles sin depender de una terminal abierta**.

### Acceptance Criteria
1. **Given** el agente local está configurado, **when** se inicia el dashboard, **then** Flask sirve HTML server-rendered con plantillas/CSS locales, cabecera, navegación, tablas y formularios clásicos, sin SPA, JavaScript obligatorio ni servicios externos.
2. **Given** una solicitud al dashboard, **when** la IP cliente no pertenece a la allowlist CIDR configurable, **then** se deniega antes de mostrar login; por defecto sólo se permite loopback y las cabeceras de proxy sólo se aceptan si se configuró un proxy confiable.
3. **Given** una IP permitida, **when** el operador inicia sesión, **then** se autentica un único usuario comparando de forma segura el hash de contraseña y usuario de variables de entorno; contraseñas, hash, sesiones y encabezados de autorización nunca se registran.
4. **Given** una sesión autenticada, **when** navega el dashboard, **then** puede ver listado de ejecuciones, detalle de run (flujo, tarea, rama/SHA, límites, resumen y eventos), historial JSONL filtrable/paginado y bandeja de checkpoints pendientes, siempre con datos redactados.
5. **Given** un checkpoint pendiente, **when** abre su detalle, **then** ve razón, severidad, diff resumido, tests, revisión y evidencia, junto a formularios explícitos para `approve`, `reject`, `edit` y `cancel`; comentario es obligatorio salvo en `approve`.
6. **Given** una acción de checkpoint, **when** el formulario POST contiene sesión válida y token CSRF, **then** reutiliza la misma validación, auditoría, `checkpoint_id`, `thread_id` y `Command(resume=...)` que la CLI; no puede resolver un checkpoint dos veces ni escribir SQLite/`log.jsonl` directamente.
7. **Given** una sesión del dashboard, **when** permanece inactiva o el operador cierra sesión, **then** expira o se invalida; la cookie usa `HttpOnly`, `SameSite=Lax` y `Secure` cuando HTTPS está activo.
8. **Given** una vista de ejecución o checkpoint abierta, **when** el estado cambia, **then** el HTML sigue siendo funcional sin JavaScript y puede actualizarse mediante polling ligero como mejora progresiva.

### Tasks/Subtasks
- [ ] Añadir Flask a `requirements.txt` y crear el módulo web, plantillas y CSS locales (AC: 1, 8).
- [ ] Implementar configuración de host/puerto, allowlist CIDR, proxy confiable, usuario y hash de contraseña por variables de entorno (AC: 2, 3).
- [ ] Crear middleware de restricción IP, autenticación, sesión segura y protección CSRF para todas las acciones mutables (AC: 2, 3, 7).
- [ ] Implementar rutas de listado, detalle, historial filtrable/paginado y checkpoints usando la capa de lectura de SQLite/JSONL redactada (AC: 4, 5).
- [ ] Implementar formularios POST de decisión delegados a la misma capa de servicio de la CLI, con auditoría e idempotencia existentes (AC: 5, 6).

### Testing
- IP fuera de allowlist, credenciales inválidas, sesión expirada o POST sin CSRF no acceden ni ejecutan decisiones.
- Dashboard autenticado muestra ejecución, eventos, checkpoint y datos redactados; filtros y paginación funcionan.
- Una decisión HTML genera la misma transición/evento que la CLI y no se puede aplicar dos veces.
- Las vistas son utilizables sin JavaScript y el polling no es requisito para ver un estado correcto.

---

## Orden de implementación sugerido

`1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7 → 1.8 → 1.9`

Las Stories 1.2 y 1.3 pueden desarrollarse en paralelo sólo después de que 1.1 haya fijado el contrato de estado. La Story 1.9 depende de las capas de persistencia, observabilidad y checkpoints de 1.5–1.7 para que dashboard y CLI mantengan una única fuente de verdad.
