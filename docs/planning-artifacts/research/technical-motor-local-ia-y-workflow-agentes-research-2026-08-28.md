---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - doc/ai-stack/README.md
  - doc/ai-stack/modelos-open-source.md
  - doc/ai-stack/arquitectura-recomendada.md
  - doc/awf:agentic-work-flow/epics.md
workflowType: 'research'
lastStep: 6
research_type: 'technical'
research_topic: 'motor local de IA y workflow durable de agentes para desarrollo y automatización'
research_goals: 'definir una arquitectura local concreta, hardware comprable, modelos y serving, orquestación durable, benchmark reproducible y plan de implementación por fases'
user_name: 'Clancien'
date: '2026-08-28'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-08-28
**Author:** Clancien
**Research Type:** technical

---

## Research Overview

Esta investigación define una arquitectura soberana para inferencia local y desarrollo asistido por agentes, contrastando la documentación existente con fuentes primarias vigentes al 28 de agosto de 2026. Evalúa modelos, licencias, runtimes, orquestadores, persistencia, aislamiento, observabilidad, hardware, energía y operación. Las cifras de VRAM son estimaciones de planificación y siempre se subordinan a pruebas del checkpoint, cuantización, contexto, batch y concurrencia exactos.

La decisión recomendada es construir la plataforma antes de fijar la compra: vLLM sobre Linux como serving productivo, Ollama/llama.cpp para laboratorio, LangGraph + PostgreSQL como orquestación durable inicial, runners rootless por worktree y aprobación humana ligada al SHA. La primera hipótesis de compra es una RTX 5090/32 GB para modelos 20–35B; la R9700 es una opción de menor coste/consumo condicionada a ROCm y la RTX PRO 6000/96 GB sólo se justifica si el benchmark demuestra valor material de 120B. Véase `Research Synthesis` para la decisión ejecutiva completa.

---

<!-- Content will be appended sequentially through research workflow steps -->

## Technical Research Scope Confirmation

**Research Topic:** motor local de IA y workflow durable de agentes para desarrollo y automatización

**Research Goals:** definir una arquitectura local concreta, hardware comprable, modelos y serving, orquestación durable, benchmark reproducible y plan de implementación por fases.

**Technical Research Scope:**

- Architecture Analysis - patrones de diseño, frameworks y arquitectura del sistema.
- Implementation Approaches - metodología de desarrollo, aislamiento, seguridad e idempotencia.
- Technology Stack - lenguajes, modelos, runtimes, frameworks, datos y observabilidad.
- Integration Patterns - API, protocolos, interoperabilidad, tools y checkpoints humanos.
- Performance Considerations - VRAM, KV cache, contexto, batch, concurrencia, latencia, energía y escalamiento.

**Research Methodology:**

- Datos web actuales con verificación rigurosa, priorizando documentación, repositorios y fichas oficiales.
- Validación cruzada de afirmaciones críticas y separación entre hechos publicados, estimaciones e inferencias.
- Clasificación explícita de licencias: open source permisivo; open-weight con licencia propia; software gratuito propietario.
- Contraste con `doc/ai-stack/` y `doc/awf:agentic-work-flow/epics.md`.

**Scope Confirmed:** 2026-08-28

## Technology Stack Analysis

### Programming Languages

**Python 3.11–3.13** debe ser el lenguaje principal del control plane: LangGraph se distribuye para Python 3.10+ y su API de grafos ofrece persistencia, streaming e intervención humana sin imponer un proveedor de modelos. Python también concentra los SDK de inferencia, evaluación, embeddings y clientes OpenAI-compatible. **Go no se necesita en el producto propio**, aunque Temporal Server está escrito mayoritariamente en Go; se consume como servicio. **Shell/Git** quedan limitados a adaptadores auditados para crear worktrees y ejecutar verificaciones, no a lógica de estado. [LangGraph package](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/pyproject.toml), [Temporal Server](https://github.com/temporalio/temporal).

El criterio no es popularidad general sino superficie operativa mínima: un solo servicio Python tipado para la API y el grafo, procesos externos encapsulados para Git/tests y servicios existentes para inferencia y datos. **Confianza: alta.**

### Development Frameworks and Libraries

- **LangGraph (MIT)** es la base del workflow: guarda snapshots por thread, reanuda desde el último paso válido y soporta interrupciones humanas. Su documentación exige encapsular efectos no deterministas en tareas y aun así diseñarlos idempotentes; por tanto, un checkpoint no reemplaza `operation_id`, claves únicas ni validación del SHA. [Persistencia](https://docs.langchain.com/oss/python/langgraph/persistence), [Functional API e idempotencia](https://docs.langchain.com/oss/python/langgraph/functional-api), [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), [licencia](https://github.com/langchain-ai/langgraph/blob/main/LICENSE).
- **Temporal Server (MIT)** se reserva para una fase de mayor escala o workflows que deban sobrevivir fallas de procesos/hosts durante días y coordinar retries durables. No se añade a v1 porque duplicaría parte de la semántica de ejecución de LangGraph y aumentaría la carga operativa. [Repositorio y licencia](https://github.com/temporalio/temporal).
- **vLLM (Apache 2.0)** es el servidor de producción: API OpenAI-compatible, batching/concurrencia, serving distribuido, tool parsers, structured outputs, cuantización, embeddings y métricas. Su matriz actual enumera parsers para Qwen3-Coder, Granite, DeepSeek, gpt-oss y OLMo 3; esto reduce adaptadores propios, pero cada checkpoint debe validarse con su template/parser exacto. [Tool calling](https://docs.vllm.ai/en/latest/features/tool_calling/), [structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/), [licencia](https://github.com/vllm-project/vllm/blob/main/LICENSE).
- **Ollama (MIT)** y **llama.cpp (MIT)** cubren laboratorio, GGUF y pruebas en hardware heterogéneo. llama.cpp aporta un servidor liviano, inferencia CPU/GPU y gramáticas/JSON-schema; su propia documentación advierte que la compatibilidad OpenAI es práctica, no una garantía total. [Ollama license](https://github.com/ollama/ollama/blob/main/LICENSE), [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md), [llama.cpp license](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE).

### Database and Storage Technologies

**PostgreSQL** debe ser la fuente de verdad de producción para runs, threads, checkpoints, aprobaciones, locks, presupuestos e identificadores idempotentes. Su WAL da recuperación ante crash y permite backup continuo/PITR. **SQLite** permanece sólo para un prototipo de operador único o tests; no debe compartir escritura entre varios workers. [PostgreSQL WAL](https://www.postgresql.org/docs/current/runtime-config-wal.html), [reliability](https://www.postgresql.org/docs/16/wal-reliability.html).

**pgvector** permite almacenar embeddings con metadatos y permisos junto al estado relacional, con búsqueda exacta o aproximada HNSW/IVFFlat y recuperación por WAL. Para la escala inicial evita operar una base vectorial separada; la calidad RAG se mide contra búsqueda exacta antes de activar aproximación. [pgvector](https://github.com/pgvector/pgvector), [licencia PostgreSQL](https://github.com/pgvector/pgvector/blob/master/LICENSE).

La evidencia grande —diffs, stdout/stderr redactados, reportes y manifests— no se guarda como blobs indiscriminados en el estado del grafo. Se conserva en un **artifact store local append-only** sobre un volumen cifrado, con SHA-256, tamaño, MIME, política de retención y referencia desde PostgreSQL. Un segundo medio local o NAS recibe backups cifrados y se prueba restauración; RAID no sustituye backup. **Confianza: alta; la retención exacta requiere definición humana.**

### Development Tools and Platforms

La cadena mínima es Git + worktrees por tarea, contenedores rootless (Podman o Docker con endurecimiento), runners de tests/linters/SAST del repositorio, y un adaptador de modelo que hable OpenAI-compatible. Cada ejecutor recibe filesystem, comandos, red, CPU/RAM, tiempo y cantidad de procesos limitados; `git push`, merge y deploy quedan fuera de su allowlist.

La observabilidad usa **OpenTelemetry Collector** como punto de redacción/exportación, métricas Prometheus y dashboards Grafana; vLLM ya expone superficies de métricas y ejemplos de Prometheus/Grafana. OpenTelemetry se define como framework vendor-neutral para traces, métricas y logs, lo que evita depender de LangSmith o de telemetría cloud. [OpenTelemetry](https://opentelemetry.io/docs/), [Collector](https://opentelemetry.io/docs/collector/), [vLLM observability index](https://docs.vllm.ai/en/latest/examples/online_serving/).

### Local Infrastructure and Deployment

La plataforma objetivo es **Linux bare metal** con servicios en contenedores o unidades systemd: GPU dedicada a vLLM, API de control no privilegiada, PostgreSQL en volumen separado, workers rootless por tarea y reverse proxy privado con TLS/RBAC. Ollama/llama.cpp se ejecutan como servicios alternativos de laboratorio, no simultáneamente si compiten por la misma VRAM.

No se propone Kubernetes para una sola workstation. Docker Compose/Podman Compose más systemd ofrecen despliegues reproducibles con mucha menos superficie. Kubernetes, Temporal y un segundo nodo GPU sólo se justifican por métricas de concurrencia, alta disponibilidad o necesidad de mantenimiento sin interrupción.

La nube se excluye del camino por defecto: ninguna llamada de inferencia, traza, prompt, diff o embedding debe salir de la red privada salvo que una política humana autorice explícitamente un proveedor y un conjunto de datos redactado. Esto incluye desactivar o revisar telemetría de cada componente y bloquear egress en workers.

### Licensing Classification of the Stack

| Categoría | Componentes | Consecuencia |
|---|---|---|
| **Open source permisivo** | vLLM (Apache 2.0); LangGraph, Temporal, Ollama, llama.cpp, CrewAI (MIT); PostgreSQL/pgvector (licencia PostgreSQL); OpenTelemetry (Apache 2.0) | Preferidos; registrar versión, licencia y SBOM por release. |
| **Open-weight con términos propios** | Determinados modelos, por ejemplo Nemotron o familias con licencias comunitarias | Pesos disponibles no equivalen a software/modelo open source; revisión legal por checkpoint exacto. |
| **Gratis pero propietario** | **LM Studio Desktop** | Útil como GUI individual, no como dependencia de producción. Sus términos conceden uso personal/interno y describen código/estructura como secretos comerciales. [Términos](https://lmstudio.ai/app-terms). |

La licencia del runtime no hereda automáticamente a los pesos: cada manifest de modelo debe registrar `model_id`, revisión/commit, hash, licencia, política de uso, cuantización y origen.

### Technology Adoption and Decision Trends

La pila converge en cuatro contratos estables: **OpenAI-compatible API** entre orquestador e inferencia; **JSON Schema** para planes/tool calls/veredictos; **checkpoint + operation ledger** para reanudación; y **OpenTelemetry** para correlación. Esta separación permite cambiar modelo, cuantización o runtime sin reescribir el workflow.

El patrón recomendado es deliberadamente incremental: LangGraph + PostgreSQL primero; Temporal sólo al aparecer una necesidad medida de coordinación distribuida; vLLM para producción y Ollama/llama.cpp para experimentación; pgvector mientras la escala RAG sea moderada. **Confianza global de esta selección: alta.** Las brechas que todavía requieren benchmark son soporte exacto por checkpoint/cuanto, calidad de tool calling, rendimiento ROCm frente a CUDA y capacidad real bajo contexto/concurrencia objetivo.

## Integration Patterns Analysis

### API Design Patterns

**REST/JSON sobre HTTPS privado** es el contrato externo adecuado. La API de control debe exponer recursos estables (`jobs`, `runs`, `artifacts`, `approvals`, `models`) y comandos explícitos (`start`, `cancel`, `approve`, `reject`, `resume`), con `Idempotency-Key`, control de versión y respuesta que incluya `job_id`, `thread_id`, estado y correlación. GraphQL no aporta una ventaja material para el primer dashboard server-rendered; gRPC sólo se justifica más adelante entre workers de alto volumen.

El adaptador de inferencia consume un subconjunto fijado y probado de **OpenAI Chat Completions/Responses/Embeddings**. vLLM implementa estas familias pero documenta diferencias —por ejemplo, ignora `user`, no soporta `suffix` y el comportamiento de tools paralelas depende del modelo—, por lo que “OpenAI-compatible” no significa identidad semántica. Se requieren contract tests para streaming, `usage`, reasoning, `response_format`, cancelación y tools. [vLLM OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/).

Los modelos no ejecutan funciones directamente: proponen un `tool_call`; el orquestador valida nombre, JSON Schema, política, presupuesto y autorización, y recién entonces crea una operación. vLLM puede garantizar JSON parseable bajo determinadas configuraciones, pero su documentación diferencia validez estructural de calidad de la elección. [vLLM tool calling](https://docs.vllm.ai/en/stable/features/tool_calling/).

Los webhooks de notificación son **at-least-once**: payload firmado, `event_id`/`checkpoint_id`, reintento con backoff y deduplicación del receptor. Nunca transportan prompts, secretos o diffs completos; sólo referencias y resúmenes redactados.

### Communication Protocols

- **HTTPS/HTTP/1.1 o HTTP/2**: API de control, gateway de modelos y webhook. SSE/streaming HTTP se usa para tokens y eventos de ejecución; WebSocket no es requisito inicial.
- **PostgreSQL protocol**: persistencia transaccional y locks/leases. Los workers no escriben artefactos ni estados saltándose la capa de servicio.
- **Proceso local/subprocess**: Git, tests, linters y herramientas se invocan mediante un runner que recibe un spec declarativo; no se pasa shell arbitrario generado por el modelo.
- **Temporal Signals/Updates**: sólo en una fase futura. Signals sirven para escrituras asíncronas; Updates para decisiones que requieren validación y respuesta. [Temporal message passing](https://docs.temporal.io/encyclopedia/workflow-message-passing).

No se necesita RabbitMQ/Kafka en v1. PostgreSQL más una cola/lease transaccional cubre el volumen esperado y conserva una única autoridad. Un broker se incorpora sólo si las métricas muestran múltiples clases de workers, backlog elevado o desacople entre hosts.

### Data Formats and Standards

Todo estado durable, plan, tool call, revisión y checkpoint usa **JSON versionado y validado con JSON Schema/Pydantic**, sin objetos Python opacos. Los artefactos pesados se referencian por URI local y SHA-256. La respuesta del modelo nunca se convierte directamente en comando.

Contrato mínimo de una operación externa:

```json
{
  "operation_id": "uuid",
  "idempotency_key": "job/phase/input_digest",
  "job_id": "uuid",
  "thread_id": "uuid",
  "phase": "test",
  "base_sha": "git-sha",
  "input_digest": "sha256",
  "tool": "pytest",
  "argv": ["pytest", "-q"],
  "cwd_ref": "worktree-id",
  "timeout_seconds": 900,
  "budget": {"cpu": 4, "memory_mb": 8192, "pids": 256},
  "policy_version": "v1"
}
```

El resultado registra imagen de contenedor por digest, timestamps, exit code, stdout/stderr redactados y hasheados, artefactos, tokens, energía si se mide, `candidate_sha` y decisión. JSONL append-only es una copia portátil de auditoría, no la autoridad de concurrencia.

### System Interoperability Approaches

Se usa un **gateway/adaptor pattern** para que LangGraph no conozca detalles de vLLM, Ollama o llama.cpp. Un `ModelEndpoint` resuelve alias versionados (`coder-primary`, `reviewer`, `router`, `embedder`) a endpoint, modelo, revisión, cuantización, template, parser y límites. El mismo principio aplica a `Runner`, `ArtifactStore`, `CheckpointStore` y `Notifier`.

El reverse proxy es frontera obligatoria de red: mTLS o token de servicio, allowlist, rate limits, tamaños máximos y endpoints permitidos. Esto es especialmente importante porque vLLM advierte que `--api-key` sólo protege determinados prefijos y deja otros endpoints de inferencia sin autenticar. [Limitación de autenticación de vLLM](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/).

No se recomienda service mesh ni ESB para una workstation. La interoperabilidad se logra con contratos HTTP/JSON, esquemas versionados, eventos correlacionados y adaptadores pequeños. **Confianza: alta.**

### Workflow and Service Integration Patterns

El workflow se divide por fronteras de efecto:

1. `plan` produce una tarea validada, sin tocar el repositorio.
2. `prepare_worktree` adquiere lease y crea/verifica una ruta determinista.
3. `execute_change` y `run_tests` llaman al runner aislado mediante operaciones idempotentes.
4. `collect_evidence` fija `base_sha`, `candidate_sha`, diff y hashes.
5. `review` evalúa exactamente esa evidencia y no puede mutarla.
6. `request_approval` sólo persiste el checkpoint y ejecuta `interrupt()`.
7. `validate_approval` comprueba usuario, decisión, diff hash y vigencia del SHA.
8. `merge_local` vuelve a validar precondiciones y fusiona localmente; **no existe tool de push**.
9. `request_deploy_approval` es un checkpoint independiente, si el deploy está configurado.

LangGraph documenta que al reanudar un interrupt el nodo comienza de nuevo; por eso ningún efecto no idempotente se coloca antes del `interrupt()` en ese nodo. Los efectos se aíslan en tareas/nodos con deduplicación propia. [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), [idempotencia](https://docs.langchain.com/oss/python/langgraph/functional-api).

Cada operación tiene restricción única `(job_id, phase, input_digest)`. Antes de reintentar se consulta el ledger y se comprueba el estado real de Git/filesystem. “Exactly once” no se asume: se implementa **at-least-once + efecto idempotente + reconciliación**.

### Event-Driven Integration

PostgreSQL conserva el estado autoritativo y un **outbox transaccional** publica eventos de dominio (`job.started`, `operation.finished`, `approval.requested`, `budget.exhausted`). Un worker entrega esos eventos a JSONL, webhook y OpenTelemetry; la clave única `event_id + sink` evita duplicados. Así, un commit de estado no puede quedar sin su evento debido a una caída entre escrituras.

No se adopta event sourcing completo: reconstruir todo el estado sólo desde logs complicaría migraciones y consultas. Se conserva snapshot autoritativo más audit log append-only y artefactos content-addressed.

Si se incorpora Temporal, Git/red/shell/LLM se ejecutan como **Activities**, que la documentación recomienda idempotentes y cuyos reintentos empiezan desde el estado inicial salvo heartbeats. Aprobaciones se reciben como Update/Signal. Temporal posee entonces los retries exteriores; LangGraph no debe reintentar el mismo efecto en paralelo. [Temporal Activities](https://docs.temporal.io/activities).

### Integration Security Patterns

- **Identidad:** sesión segura para operador; identidad de servicio separada para API, workers y serving. RBAC mínimo: viewer, operator, approver, administrator.
- **Autenticación/transporte:** TLS privado; mTLS o tokens rotables entre servicios. Secretos en archivos/secret store montados sólo donde corresponda, nunca en prompts ni variables heredadas al runner.
- **Aislamiento:** contenedor rootless por operación, `cap-drop=all`, filesystem de sistema read-only, sólo worktree montado RW, sin socket del motor, sin dispositivos salvo los imprescindibles, cgroups para CPU/RAM/PIDs/IO y red `none` por defecto. Podman documenta namespaces separados, límites cgroup y el riesgo de agregar capabilities. [Podman run](https://docs.podman.io/en/latest/markdown/podman-run.1.html).
- **Egress:** allowlist por tarea; descargas de modelos/dependencias se realizan en un proceso controlado, verificado por hash y separado de la ejecución agéntica.
- **Datos:** cifrado de volúmenes y backups; redacción central antes de persistir/exportar; pruebas canario con secretos sintéticos; retención y borrado gobernados.
- **Supply chain:** modelos y contenedores fijados por digest/revisión; SBOM y escaneo; `trust_remote_code` deshabilitado salvo excepción revisada.
- **Aprobación:** la autorización queda ligada a `approval_id`, actor, timestamp, `candidate_sha`, `diff_hash`, tests y policy version; cualquier cambio la invalida.

### Compatibility and Failure Contracts

Cada integración declara timeout, política de retry, idempotency key y clasificación de error: transitorio, corregible por modelo, requiere humano o terminal. Los circuit breakers impiden tormentas contra un modelo saturado; la cola aplica backpressure y presupuesto global monotónico en PostgreSQL.

Antes de actualizar LangGraph se prueban threads suspendidos: su documentación señala que una ejecución reanudada usa el grafo más reciente, de modo que reordenar tareas o interrupts anteriores al punto de pausa puede romper compatibilidad. Se necesita `workflow_schema_version`, migración o drenaje de runs antes de deploy. [LangGraph backward compatibility](https://docs.langchain.com/oss/python/langgraph/backward-compatibility).

Temporal sigue teniendo límites de historial —51.200 eventos o 50 MB, con aviso desde 10.240/10 MB—, por lo que no elimina la necesidad de artefactos externos ni de rotar ejecuciones extensas mediante Continue-As-New. [Temporal limits](https://docs.temporal.io/workflow-execution/limits).

**Calidad de evidencia:** alta para semántica de APIs, reanudación e idempotencia; media para dimensionamiento de colas/brokers, que depende de la concurrencia todavía no definida.

## Architectural Patterns and Design

### System Architecture Patterns

La arquitectura inicial es un **monolito modular para el control plane** con servicios de infraestructura y runners separados. API, políticas, presupuestos, registro de jobs y definición LangGraph viven en un único producto Python desplegable, pero dependen de puertos explícitos para inferencia, persistencia, artefactos, ejecución y notificación. Evita transacciones distribuidas y despliegues múltiples antes de conocer la carga, sin sacrificar fronteras que permitan extraer workers posteriormente.

```text
Operador: CLI / dashboard local
          │ HTTPS privado + sesión/RBAC
          ▼
┌───────────────────────────────────────────────────────┐
│ API de control / Policy & Budget Engine              │
│ jobs · modelos · artefactos · aprobaciones · auditoría│
├───────────────────────────────────────────────────────┤
│ LangGraph                                             │
│ plan → prepare → execute → test → evidence → review  │
│                         → human gate → merge local    │
└──────────┬─────────────────┬───────────────────┬──────┘
           │                 │                   │
           ▼                 ▼                   ▼
    PostgreSQL         Artifact Store       Model Gateway
    checkpoints        diffs/logs/SHA        aliases/policy
    ledger/outbox      backups cifrados       │
    leases/approval                         ┌───┴──────────┐
           │                               │              │
           ▼                               ▼              ▼
  Runner rootless por tarea          vLLM producción  Ollama/llama.cpp
  worktree RW · host RO · red none       GPU local      laboratorio
  Git/tests/linters · nunca push
```

LangGraph es el motor de estado explícito; PostgreSQL es la autoridad operacional; el ledger protege efectos externos; el artifact store conserva evidencia content-addressed. Los checkpoints por thread y pending writes soportan recuperación, pero no sustituyen la verificación idempotente de Git/filesystem. [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

### Design Principles and Best Practices

- **Control plane / data plane:** el control plane decide y audita; runners e inferencia ejecutan dentro de límites. Ningún output de modelo concede permisos.
- **Hexagonal/ports and adapters:** `ModelEndpoint`, `Runner`, `ArtifactStore`, `CheckpointStore`, `ApprovalService` y `Notifier` permiten sustituir runtimes sin contaminar el dominio.
- **Least authority:** planner/router/reviewer no reciben shell; executor no recibe push/merge/deploy; approver no altera evidencia histórica.
- **Evidence before transition:** una transición sólo referencia artefactos persistidos y hasheados; una revisión sólo vale para un `candidate_sha`/`diff_hash` exactos.
- **Small durable nodes:** efectos, checkpoints y decisiones se separan para reducir repetición después de fallos. LangGraph confirma que los límites de nodo son los límites de checkpoint. [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph).
- **Version everything:** graph schema, prompts, policies, tools, model revision, tokenizer/template/parser, runtime/container, cuantización y dataset de benchmark.
- **Fail closed:** estado desconocido, evidencia incompleta, base cambiada, secreto detectado o presupuesto agotado conducen a `blocked`/checkpoint, nunca a éxito implícito.

### Scalability and Performance Patterns

El orden de escalamiento es:

1. **Optimizar una GPU:** modelo/cuanto adecuados, continuous batching, límite de contexto, prefix caching y colas por prioridad.
2. **Separar cargas:** una instancia generativa principal y una instancia pequeña de embeddings/routing en GPU secundaria o CPU si evita desalojos.
3. **Replicar:** data parallel para más solicitudes cuando el modelo cabe por GPU.
4. **Particionar:** tensor/pipeline/expert parallel sólo cuando el modelo no cabe o el benchmark prueba una ganancia neta.
5. **Separar nodo GPU:** 10/25 GbE y scheduler externo únicamente tras medir saturación.

vLLM soporta estrategias TP/PP/DP/EP y despliegue single/multi-node, pero el paralelismo exige comunicación; dos GPU de consumo no equivalen automáticamente a una GPU con VRAM unificada. [vLLM parallelism and scaling](https://docs.vllm.ai/en/latest/serving/parallelism_scaling/), [data-parallel deployment](https://docs.vllm.ai/en/latest/serving/data_parallel_deployment/).

El contexto se trata como presupuesto, no como capacidad gratuita: pesos + runtime/CUDA graphs + KV cache por secuencia + batch/concurrencia + 15–25 % de margen. RAG y resúmenes incrementales se prefieren a enviar el repositorio completo. Backpressure en la API limita solicitudes concurrentes antes de causar OOM/preemption.

### Integration and Communication Patterns

El gateway local resuelve alias de rol a una instancia/modelo exacto y aplica timeout, máximo de tokens, parser y schema. La API de control emite eventos vía outbox; dashboard y CLI consumen la misma capa de servicio. Los workers reclaman operaciones mediante lease, heartbeat y fencing token para evitar que un worker recuperado y uno nuevo modifiquen el mismo worktree.

Temporal puede envolver fases exteriores en el futuro:

```text
Temporal Workflow (opcional)
  ├─ Activity: ejecutar/reanudar fase LangGraph
  ├─ Activity: preparar/verificar worktree
  ├─ Activity: ejecutar comando aislado
  ├─ Update/Signal: decisión humana
  └─ Activity: merge local validado
```

No se permite que Temporal y LangGraph reintenten el mismo efecto. Temporal poseería retries de Activities; LangGraph conserva la lógica cognitiva y checkpoints internos.

### Security Architecture Patterns

Se aplica **zero trust local**: pertenecer a loopback/LAN no concede confianza. NIST SP 800-207 explícitamente desplaza la confianza desde ubicación de red hacia usuario, dispositivo y recurso. [NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final).

Fronteras:

- **Operador → API:** autenticación, RBAC, CSRF para dashboard, auditoría de decisiones.
- **API → serving:** identidad de servicio y reverse proxy; sólo endpoints requeridos.
- **Orquestador → runner:** spec firmado/validado, imagen por digest y capacidades mínimas.
- **Runner → repositorio:** worktree único RW; repositorio base/host RO; credenciales Git ausentes.
- **Runner → red:** bloqueada; excepciones temporales por allowlist y motivo auditable.
- **Observabilidad:** redacción antes del collector; labels sin código, prompts, paths sensibles ni datos personales.

Threats prioritarios: prompt injection desde repositorio, exfiltración por tools/egress, command injection, escape de contenedor, dependencia/modelo malicioso, aprobación obsoleta, logs con secretos, agotamiento de recursos y confusión entre evidencia de runs.

### Data Architecture Patterns

PostgreSQL contiene datos pequeños y autoritativos: `jobs`, `threads`, `operations`, `attempts`, `leases`, `budgets`, `approvals`, `events/outbox`, `artifacts`, `model_manifests` y schemas de LangGraph. Las restricciones únicas y transacciones implementan deduplicación y transición válida.

El artifact store usa rutas/objetos por hash para prompts redactados, diffs, logs, reportes y bundles Git. Checkpoints sólo guardan referencias. pgvector mantiene embeddings y metadatos de documentos; el índice se reconstruye desde fuentes y no se mezcla con evidencia regulada.

El backup es una unidad de recuperación consistente:

- base backup + WAL/PITR de PostgreSQL;
- artefactos y manifests con checksums;
- Git bundles de commits locales que aún no tienen remoto;
- claves/configuración mediante backup cifrado separado;
- prueba de restauración periódica con RPO/RTO aún por definir.

### Deployment and Operations Architecture

Primera instalación: Linux LTS, servicios fijados por versión en systemd y Compose/Podman, volúmenes cifrados separados, GPU reservada al serving, reverse proxy privado y firewall deny-by-default. Kubernetes no se justifica en una workstation.

Topología lógica inicial:

| Unidad | Despliegue | Reinicio/estado |
|---|---|---|
| API + LangGraph workers | servicio Python no privilegiado | stateless salvo checkpoints/leases en PostgreSQL |
| PostgreSQL | servicio/contenedor dedicado | WAL, health check, backup consistente |
| vLLM | contenedor GPU fijado por digest | un modelo principal por instancia; warmup antes de ready |
| Ollama/llama.cpp | servicio de laboratorio detenido por defecto | no competir por VRAM con producción |
| Runner | contenedor efímero rootless | reconstruible; worktree/evidencia externos |
| OTel/Prometheus/Grafana | servicios internos | retención y cardinalidad limitadas |
| Reverse proxy | única entrada de red | TLS, auth, allowlist, rate/size limits |

Las actualizaciones de LangGraph requieren compatibilidad con runs suspendidos: el runtime aplica el grafo nuevo a threads existentes, por lo que se versiona el workflow y se drenan/migran ejecuciones antes de cambios incompatibles. [LangGraph backward compatibility](https://docs.langchain.com/oss/python/langgraph/backward-compatibility).

### Architectural Decisions and Trade-offs

| Decisión | Alternativa descartada ahora | Motivo / condición de revisión |
|---|---|---|
| Monolito modular | microservicios | Menor complejidad transaccional; extraer sólo por carga/ownership. |
| LangGraph + PostgreSQL | Temporal desde v1 | Suficiente para un host; revisar ante SLA multi-host o esperas de semanas. |
| vLLM producción | Ollama único | Mejor scheduling, concurrencia, métricas y paralelismo. |
| PostgreSQL + pgvector | DB vectorial separada | Menos servicios; revisar al superar recall/latencia/escala medidos. |
| Podman/rootless | shell directo | Reduce blast radius; VM/microVM si el adversario incluye código altamente hostil. |
| Vertical primero | multi-GPU inmediato | Evita coste de interconnect y operación sin benchmark. |
| Servicios OSS locales | LangSmith/AMP/LM Studio como núcleo | Privacidad, auditabilidad y licencia; pueden usarse sólo como herramientas opcionales. |

**Confianza arquitectónica: alta** para la topología y fronteras; **media** para la ruta de escalamiento, que depende de concurrencia, SLA, energía, ruido y presupuesto aún no definidos.

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategy

La adopción debe ser incremental y reversible: primero un benchmark en hardware prestado/alquilado o con política de devolución; luego serving local; después un flujo de sólo lectura; finalmente escritura aislada y checkpoints humanos. La autonomía aumenta únicamente cuando cada fase genera evidencia aceptada.

No se migra la documentación actual a un framework nuevo: `doc/awf:agentic-work-flow/epics.md` sigue siendo el contrato funcional y se ajusta donde contradiga estas decisiones (PostgreSQL en producción, separación de efectos/interrupts y model gateway). El prototipo SQLite se conserva para pruebas de un operador, no como arquitectura productiva.

### Hardware Profiles and Real Constraints

| Perfil VRAM | Modelos realistas | Límite operacional |
|---|---|---|
| **24 GB** | gpt-oss-20b MXFP4; Qwen3-Coder-30B-A3B Q4 con contexto/concurrencia recortados; auxiliares 3–8B | Un agente generativo; escaso margen de KV; laboratorio, no compra nueva preferida si 32 GB es accesible. |
| **32 GB** | Qwen3-Coder-30B-A3B Q4/FP8 según checkpoint; gpt-oss-20b; Gemma 4 26B-A4B Q4; Granite 4.2 30B Q4; Nemotron Nano NVFP4 | Punto de entrada productivo; 1–3 solicitudes moderadas, no todos los modelos simultáneos; contexto real a medir. |
| **48–64 GB** | Qwen3-Coder-Next Q4; OLMo 3 32B con mejor precisión; 30B densos con mayor KV | Perfil válido en una GPU profesional o dos GPU sólo tras benchmark. La memoria de dos GPU no se comporta como un pool transparente. |
| **80–96 GB** | gpt-oss-120b MXFP4; Mistral Small 4 NVFP4; Qwen3-Coder-Next con holgura | Alta capacidad mononodo; 120B/119B dejan margen finito para KV/batch; no garantiza 256K a alta concurrencia. |

Comparación de las GPU solicitadas:

| GPU | VRAM / ECC | Potencia | Ecosistema | Precio de referencia verificable | Decisión |
|---|---:|---:|---|---:|---|
| **RTX 5090** | 32 GB GDDR7 / no ECC | 575 W; sistema recomendado 1000 W | CUDA, menor riesgo en vLLM; sin NVLink | MSRP USD 1.999; precios AIB observados muy superiores | **Recomendada condicionada** para 20–35B y 1–3 agentes. |
| **RTX PRO 6000 Blackwell Workstation** | 96 GB GDDR7 ECC | hasta 600 W | CUDA profesional, gran capacidad en una GPU | NVIDIA Marketplace ~USD 13.250 sólo GPU | **Alto rendimiento** si 120B y SLA justifican coste. |
| **Radeon AI PRO R9700** | 32 GB GDDR6; ECC Linux | 300 W; PSU mínima 750 W | ROCm 7; vLLM incluye gfx1201/Radeon 9000; matriz menos uniforme por modelo/cuanto | MSRP USD 1.299 | **Entrada/value** sólo tras PoC exacta vLLM+ROCm. |

Fuentes: [RTX 5090 specs](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/), [precio oficial de lanzamiento](https://nvidianews.nvidia.com/news/nvidia-blackwell-geforce-rtx-50-series-opens-new-world-of-ai-computer-graphics), [RTX PRO 6000](https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000/), [NVIDIA Marketplace](https://marketplace.nvidia.com/en-us/enterprise/laptops-workstations/), [R9700](https://www.amd.com/en/products/graphics/workstations/radeon-ai-pro/ai-9000-series/amd-radeon-ai-pro-r9700.html), [ROCm matrix](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/native_linux/native_linux_compatibility.html), [vLLM GPU support](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/index.html).

### Three Conditional Purchase Configurations

Precios son rangos de planificación en USD a agosto de 2026, **no cotizaciones para Chile**; excluyen IVA, importación, instalación eléctrica, UPS y soporte del integrador.

| Componente | Entrada | Recomendada | Alto rendimiento |
|---|---|---|---|
| GPU | Radeon AI PRO R9700 32 GB | RTX 5090 32 GB | RTX PRO 6000 Blackwell 96 GB ECC |
| CPU/plataforma | Ryzen 9 9950X/AM5, 16C | Threadripper 9960X/TRX50, 24C | Threadripper PRO 9965WX/WRX90, 24C |
| RAM | 128 GB DDR5 ECC UDIMM si placa/CPU lo validan | 256 GB DDR5 ECC RDIMM, 4 canales | 256–512 GB DDR5 ECC RDIMM, 8 canales |
| NVMe | 2 TB SO/DB + 4 TB modelos/worktrees | 2 TB SO/DB PLP + 8 TB modelos/artefactos | 2 TB SO/DB PLP + 2×7.68/8 TB modelos/artefactos |
| Red | 2.5 GbE; 10 GbE opcional | 10 GbE | 10/25 GbE |
| PSU | 1000 W 80+ Gold/Platinum | 1600 W ATX 3.x Platinum | 1600 W o PSU certificada por integrador |
| Chasis/refrigeración | torre airflow, GPU 300 W | torre grande, 5090 verificada, CPU/GPU continuos | chasis workstation certificado; double-flow-through sin obstrucción |
| UPS | online/line-interactive dimensionada, shutdown limpio | 2 kVA aproximado a validar | 2–3 kVA y circuito dedicado a validar |
| Estimación sistema | **USD 3.800–5.000** | **USD 6.000–8.000** | **USD 21.000–27.000** |

La plataforma AM5 es económica pero limita expansión PCIe y ancho de memoria. TRX50 ofrece 80 carriles PCIe 5.0 y cuatro canales; WRX90/Threadripper PRO ofrece hasta 128 carriles PCIe 5.0, ocho canales y ECC, apropiado si se prevén GPU/NVMe/NIC adicionales. [Threadripper 9000](https://www.amd.com/en/blogs/2025/designed-to-create-built-to-inspire-amd-introduces-new.html), [Threadripper PRO 9965WX](https://www.amd.com/en/products/processors/workstations/ryzen-threadripper/9000-wx-series/amd-ryzen-threadripper-pro-9965wx.html).

Requisitos comunes:

- no compartir térmicamente una GPU de 575–600 W con slots/NVMe sin validar airflow;
- conectores 12V-2x6 sin adaptadores doblados ni PSU marginal;
- medir ruido a 1 m en idle/carga sostenida y temperatura ambiente de verano;
- separar volumen de modelos (reconstruible) de DB/evidencia (crítico);
- preferir NVMe enterprise con power-loss protection para PostgreSQL si el presupuesto lo permite;
- backup cifrado 3-2-1 adaptado: copia local rápida, copia en NAS/medio separado y una copia desconectada/offsite autorizada sin datos en cloud por defecto;
- probar restore de PostgreSQL, artifacts y Git bundles, no sólo existencia del backup.

### Reproducible Benchmark Protocol

**Manifest fijo por corrida:** hardware/BIOS/power limit; kernel/OS; driver CUDA/ROCm; runtime/contenedor digest; modelo revision/hash/licencia; tokenizer/chat template/tool parser; cuantización; flags vLLM; contexto máximo; `gpu_memory_utilization`; seed; dataset commit; temperatura ambiente.

**Matriz mínima:**

- modelos shortlist por perfil;
- prompts 2K, 8K, 32K y contexto objetivo adicional sólo si cabe;
- outputs 256, 1K y 4K tokens;
- concurrencia 1, 2, 4 y 8 hasta incumplir SLO/OOM;
- cold start y warm state; prefix cache controlada/reiniciada;
- tres repeticiones más warm-up; reportar mediana, p95/p99 e intervalos/dispersión.

vLLM proporciona `bench serve`, TTFT, TPOT, ITL, E2E y throughput; advierte que repetir prompts puede reutilizar prefix cache e inflar resultados. Se reinicia/reseteará cache o variará seed según el escenario. [vLLM benchmark CLI](https://docs.vllm.ai/en/latest/benchmarking/cli/).

**Suite de tareas reales, congelada y sin datos sensibles:**

1. corregir bugs con tests rojos en Java/Spring, Java legacy, Laravel y Node/Express representativos;
2. implementar una feature pequeña multiarchivo desde criterio de aceptación;
3. refactor seguro con tests de regresión;
4. explicar arquitectura y ubicar código relevante en repositorio mediano/grande;
5. revisar un diff con defectos conocidos, secretos sintéticos y vulnerabilidades sembradas;
6. producir plan JSON válido y conciliar backlog;
7. tool calls: Git status/diff, búsqueda, edición, tests y consulta RAG, incluyendo argumentos adversariales;
8. reanudar tras kill/reboot simulado en cuatro puntos críticos sin duplicar efectos.

**Métricas:**

| Dimensión | Métrica |
|---|---|
| Rendimiento | output/total tokens/s; req/s; TTFT p50/p95/p99; TPOT/ITL; E2E; queue time; cold-load time |
| Capacidad | VRAM pesos/runtime/KV; max concurrencia que cumple SLO; preemptions/OOM; RAM/IO/PCIe |
| Calidad código | tareas resueltas; tests pasados; regresiones; diff mínimo; intervención humana; intentos |
| Agents/tools | JSON/schema válido; tool seleccionada; argumentos correctos; tools innecesarias/prohibidas; recuperación de error |
| Review | defectos verdaderos detectados; falsos positivos; severidad; evidencia por línea/SHA |
| Durabilidad | efectos duplicados = 0; recuperación exitosa; tiempo de resume; consistencia DB/artifacts |
| Seguridad | secretos filtrados = 0; push/egress no autorizados = 0; prompt injections obedecidas = 0 |
| Energía | W idle/promedio/pico; Wh/tarea exitosa; tokens/Wh; throttling; temperatura; dBA |

Para NVIDIA, DCGM expone potencia, energía total, VRAM, temperatura, PCIe y errores; para AMD se usa ROCm SMI más un medidor de pared calibrado. El coste energético se calcula con energía total del sistema, no sólo GPU. [DCGM metrics](https://docs.nvidia.com/datacenter/dcgm/latest/reference/dcgm-exporter-metrics.html), [ROCm SMI](https://rocm.docs.amd.com/_/downloads/rocm_smi_lib/en/latest/pdf/).

**Scoring recomendado:** calidad/gates 50 %, rendimiento/SLO 20 %, estabilidad/operación 15 %, energía/ruido 10 %, licencia/mantenibilidad 5 %. Seguridad, licencia y no duplicación son gates binarios, no puntos compensables.

### Implementation Roadmap

| Fase | Entregable | Gate |
|---|---|---|
| **0. Benchmark** | dataset versionado, runner, resultados de modelos/runtimes en hardware comparable | shortlist y perfil VRAM justificados; ninguna compra por pesos teóricos |
| **1. Inferencia** | vLLM privado autenticado por proxy, manifests y métricas; Ollama/llama.cpp laboratorio | contract tests, SLO provisional y sin egress/logs sensibles |
| **2. Orquestador** | LangGraph + PostgreSQL; read-only → worktree → tests → review → approval | reanudación/idempotencia y SHA evidence demostrados |
| **3. Seguridad/operación** | runners rootless, policy engine, redacción, alertas, backup/restore, dashboard | threat tests, restore drill, runbook e incident response aprobados |
| **4. Escalamiento** | tuning y decisión segunda GPU/96 GB/nodo | saturación sostenida y TCO justifican inversión; no escalar por intuición |

### Acceptance Criteria Before Hardware Purchase

No emitir orden de compra hasta documentar:

1. presupuesto máximo **puesto en Chile**, impuestos/garantía incluidos;
2. usuarios y agentes concurrentes objetivo y patrón horario;
3. SLO: TTFT p95, completion E2E p95, disponibilidad y cola tolerada;
4. tamaño de contexto habitual/p95 y output esperado;
5. circuito eléctrico, potencia máxima, UPS, climatización, dBA y ubicación;
6. RPO/RTO y retención de evidencia;
7. modelo principal/quant exacto supera suite real con tasa objetivo definida por humano;
8. configuración candidata cumple SLO con ≥20 % de VRAM operacional o margen probado equivalente;
9. vLLM/tool parser/structured output estables durante prueba sostenida de 8–24 h;
10. tres cotizaciones comparables y garantía/soporte local; TCO de 3 años con energía;
11. para R9700: PoC exacta sobre ROCm/OS soportados; para multi-GPU: benchmark de interconnect; para PRO 6000: necesidad demostrada de >64 GB.

### Acceptance Criteria Before Enabling Automation

- `main` y remoto no cambian durante ejecución; `git push` no existe en tools/credenciales/egress.
- toda tarea usa worktree y contenedor dedicados, límites cgroup y red deny-by-default;
- schema/model output inválido falla cerrado;
- kill/reboot en cada punto crítico no duplica worktree, comando, commit, merge, webhook ni deploy;
- revisión/aprobación ligadas a SHA/diff hash; cambio posterior las invalida;
- merge y deploy requieren checkpoints separados y actor autenticado;
- límites monotónicos de tokens, llamadas, tiempo, comandos y reintentos detienen el grafo claramente;
- secretos sintéticos no aparecen en prompts persistidos, logs, diff summaries, métricas ni webhook;
- backup/restore recrea run, checkpoints, evidencia y commits locales;
- suite de seguridad/prompt injection y pruebas de aislamiento pasa;
- operación piloto read-only y luego write-isolated durante periodo definido sin incidentes críticos;
- rollback, cancelación, limpieza/retención y respuesta a incidente tienen runbook probado.

### Team, Skills and Operating Model

Roles mínimos, aunque una persona pueda cubrir varios: owner técnico/arquitectura; ML inference engineer; platform/SRE; security reviewer; dueños de repositorios/aprobadores. Capacidades: Linux/GPU drivers, vLLM, evaluación LLM, Python/LangGraph, PostgreSQL/WAL, Git internals/worktrees, contenedores/cgroups, observabilidad, threat modeling y respuesta a incidentes.

Separación humana: quien ajusta prompts/modelos no define unilateralmente los criterios de aceptación; el revisor de seguridad valida egress/runner; el dueño del repositorio conserva merge/deploy.

### Cost and Resource Management

Registrar por job tokens, segundos GPU, Wh, intentos y resultado. El coste local por tarea incluye amortización de sistema, energía, refrigeración, operación y tiempo humano; no debe compararse con cloud sólo por precio de tokens. Apagar/descargar modelos de laboratorio cuando no se usan, aplicar power cap si mejora tokens/Wh sin romper SLO y evitar mantener simultáneamente modelos grandes que fuerzan swapping.

La RTX 5090 puede ser la mejor relación rendimiento/ecosistema, pero no lo es si el límite acústico/eléctrico excluye 575 W. La R9700 puede dominar coste/VRAM/energía, pero el coste de ingeniería ROCm puede superar el ahorro. La PRO 6000 compra capacidad, ECC y simplicidad monogpu; sólo se justifica si el benchmark de 120B produce valor superior medible.

### Risks and Decisions Requiring Human Validation

| Riesgo/supuesto | Mitigación | Decisión humana pendiente |
|---|---|---|
| Calidad local insuficiente para repos reales | benchmark ciego y baseline actual | tasa mínima de éxito/calidad aceptable |
| VRAM agotada por KV/concurrencia | sweep de contexto/batch y margen | contexto/SLO/concurrencia objetivo |
| Precios/stock/importación volátiles | tres cotizaciones y garantía local | presupuesto puesto en Chile |
| 5090: 575 W, ruido, no ECC/NVLink | power cap, chasis/PSU/circuito validados | energía y dBA máximos |
| R9700: kernels/cuants ROCm variables | PoC exacta y lock de versiones | tolerancia a mantenimiento AMD |
| PRO 6000: CAPEX alto | comparar valor de 120B contra 30B | si 96 GB es requisito o aspiración |
| Agente ejecuta código hostil | rootless, egress off, seccomp/cap drop; considerar VM | nivel de aislamiento requerido |
| Prompt injection/exfiltración | datos no confiables delimitados, policy fuera del prompt | repos/datos admitidos |
| Pérdida de commits locales/evidencia | bundles + PITR + restore drills | RPO/RTO/retención |
| Dos motores durables duplican efectos | un dueño de retry por frontera | umbral para introducir Temporal |
| Licencia/política cambia por checkpoint | manifest, revisión legal y pin | licencias organizacionalmente aceptables |

**Conclusión de implementación:** construir primero el harness de evaluación y la vertical mínima en hardware disponible. La configuración recomendada es una hipótesis informada, no autorización de compra, mientras falten presupuesto, concurrencia, SLA y restricciones de energía/ruido.

# Research Synthesis: Motor local de IA y workflow durable de agentes

## Executive Summary

La recomendación es **adoptar una arquitectura local modular y no comprar aún una configuración definitiva**. El stack objetivo es vLLM (Apache 2.0) para serving de producción, Ollama/llama.cpp (MIT) para laboratorio y GGUF, LangGraph (MIT) con `AsyncPostgresSaver` para el grafo durable, PostgreSQL + pgvector para estado y recuperación, artefactos content-addressed para evidencia, y runners rootless aislados por worktree. Temporal (MIT) queda como capa exterior futura sólo si aparecen tareas multi-host de días/semanas o un SLA que exceda la recuperación de aplicación.

Para el modelo principal, el shortlist inicial es **Qwen3-Coder-30B-A3B** para edición agéntica y **gpt-oss-20b** para planificación/revisión, con Granite 4.2 o Qwen pequeño para routing y Qwen3-Embedding/Granite Embedding para RAG. En 48–64 GB entra Qwen3-Coder-Next; en 80–96 GB se habilitan gpt-oss-120b y Mistral Small 4 NVFP4. DeepSeek-V3.2/V4 quedan como referencias de calidad o cargas multi-GPU, no como objetivos para una workstation de hasta 96 GB.

La hipótesis de hardware con menor riesgo de implementación es **RTX 5090 32 GB + Threadripper/TRX50 + 256 GB ECC + NVMe separados**, estimada en USD 6.000–8.000 antes de IVA/importación. No es una orden de compra: faltan presupuesto puesto en Chile, cantidad de usuarios/agentes concurrentes, TTFT/E2E objetivo, contexto p95, disponibilidad, potencia/circuito, ruido y RPO/RTO. La alternativa R9700 reduce CAPEX y TBP; la PRO 6000 compra 96 GB ECC y simplicidad monogpu a un coste varias veces mayor.

**Decisión recomendada:** financiar primero la fase de benchmark y reservar la compra a la configuración mínima que cumpla el SLO con ≥20 % de margen operacional observado. Ningún resultado de pesos teóricos, benchmark público o tokens/s aislado reemplaza la tasa de tareas reales completadas, calidad de tools, tests, reanudación, seguridad y Wh por tarea exitosa.

### Key Decisions

- Producción: **vLLM + NVIDIA/CUDA** como camino de menor riesgo; AMD/ROCm sólo tras PoC exacta.
- Workflow: **LangGraph + PostgreSQL + ledger idempotente**; Temporal diferido.
- Ejecución: worktree dedicado + contenedor rootless + egress deny-by-default; no se proporciona `git push`.
- Estado/evidencia: checkpoints pequeños en PostgreSQL; artefactos redactados y hasheados fuera del estado.
- Control humano: revisión y aprobación ligadas a `candidate_sha` y `diff_hash`; merge y deploy son gates separados.
- Compra: RTX 5090 como hipótesis recomendada; R9700 entrada; RTX PRO 6000 alto rendimiento condicionado.

## Table of Contents

1. [Decision and Conditions](#1-decision-and-conditions)
2. [Model Comparison](#2-model-comparison)
3. [Runtime and Framework Comparison](#3-runtime-and-framework-comparison)
4. [Target Architecture](#4-target-architecture)
5. [Hardware Purchase Profiles](#5-hardware-purchase-profiles)
6. [Implementation Roadmap](#6-implementation-roadmap)
7. [Benchmark and Acceptance Gates](#7-benchmark-and-acceptance-gates)
8. [Risks and Human Decisions](#8-risks-and-human-decisions)
9. [Licensing Classification](#9-licensing-classification)
10. [Methodology, Confidence and Sources](#10-methodology-confidence-and-sources)

## 1. Decision and Conditions

### Recommended target

| Capa | Selección | Estado de decisión |
|---|---|---|
| Serving productivo | vLLM detrás de reverse proxy | Recomendado |
| Serving laboratorio | Ollama; llama.cpp para control/portabilidad GGUF | Recomendado |
| Orquestación | LangGraph StateGraph/Functional tasks | Recomendado |
| Durabilidad | PostgreSQL + checkpointer + operation ledger/outbox | Recomendado |
| Durabilidad distribuida | Temporal self-hosted | Diferido, con trigger medible |
| RAG | embeddings locales + PostgreSQL/pgvector | Recomendado inicialmente |
| Runner | Podman rootless por operación/worktree | Recomendado; considerar microVM según amenaza |
| Observabilidad | OTel Collector + Prometheus/Grafana + Loki/Jaeger | Recomendado |
| GPU inicial | RTX 5090 32 GB | Hipótesis a validar, no compra aprobada |

### Missing inputs that block a final purchase recommendation

1. CAPEX máximo puesto en Chile y TCO permitido a tres años.
2. Usuarios interactivos y agentes simultáneos, carga media/pico y horario.
3. SLO de TTFT p95, E2E p95, cola máxima y disponibilidad.
4. Contexto de entrada p50/p95, longitud de salida y calidad mínima por tarea.
5. Potencia continua/pico admisible, circuito/UPS/climatización y dBA a 1 m.
6. RPO, RTO y retención de evidencia.
7. Nivel de aislamiento: contenedor rootless o VM/microVM para código hostil.
8. Licencias/políticas de uso aceptadas por la organización.

## 2. Model Comparison

La VRAM indicada es un rango de **pesos/checkpoint más margen básico**, no garantía de contexto publicado. KV cache, runtime, CUDA graphs, batch y concurrencia pueden elevarla significativamente. En producción se conserva 15–25 % de margen o el margen equivalente demostrado por prueba sostenida.

| Modelo | Clasificación/licencia | Parámetros total/activos | Contexto publicado | VRAM aproximada práctica | Rol recomendado | Fuente oficial |
|---|---|---:|---:|---:|---|---|
| **Qwen3-Coder-30B-A3B-Instruct** | OSS pesos/código, Apache 2.0 | 30,5B / 3,3B | 256K nativo; YaRN hasta 1M | Q4 ~15–18 GB; **24 GB mínimo, 32 GB recomendado** | Coding agent principal en workstation inicial | [Model card](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct), [blog](https://qwenlm.github.io/blog/qwen3-coder/) |
| **Qwen3-Coder-Next** | OSS pesos/código, Apache 2.0 | 80B / 3B | 256K | Q4 ~40 GB sólo pesos; **48–64 GB mínimo práctico**, 80–96 GB con holgura | Coding agent de mayor capacidad/recuperación | [Model card](https://huggingface.co/Qwen/Qwen3-Coder-Next) |
| **gpt-oss-20b** | OSS pesos/código, Apache 2.0; política de uso separada | 21B / 3,6B | 128K | MXFP4 ~16 GB; **24–32 GB práctico** | Planner, reviewer, structured output y tools | [OpenAI announcement](https://openai.com/index/introducing-gpt-oss/), [model card](https://openai.com/index/gpt-oss-model-card/) |
| **gpt-oss-120b** | OSS pesos/código, Apache 2.0; política de uso separada | 117B / 5,1B | 128K | MXFP4: clase **80 GB**; 96 GB preferible | Razonamiento/revisión de alta capacidad | [OpenAI](https://openai.com/index/introducing-gpt-oss/) |
| **Mistral Small 4 119B-A6B** | OSS/open-weight Apache 2.0 | 119B / 6,5B | 256K | NVFP4 oficial ~70,8 GB; **96 GB con margen limitado** | Generalista, reasoning, review, visión y tools | [Mistral](https://mistral.ai/news/mistral-small-4/), [docs](https://docs.mistral.ai/models/mistral-small-4-0-26-03), [weights](https://huggingface.co/mistralai/Mistral-Small-4-119B-2603-NVFP4) |
| **Granite 4.2** | OSS/open-weight Apache 2.0 | Familia densa 3B/8B/30B | 128K; 30B extensible 512K | 8B ~5–10 GB; 30B Q4 ~15–20 GB + KV | Router, RAG, planner/reviewer auditable | [IBM docs](https://www.ibm.com/granite/docs/models/granite4-2), [research](https://research.ibm.com/blog/introducing-granite-4-2) |
| **Gemma 4 26B-A4B** | OSS/open-weight Apache 2.0 | 25,2B / 3,8B | 256K | Q4 oficial ~14,4 GB + KV; **24–32 GB** | Generalista compacto, code/tools/visión | [Google model card](https://ai.google.dev/gemma/docs/core/model_card_4) |
| **Gemma 4 31B dense** | OSS/open-weight Apache 2.0 | 30,7B / 30,7B | 256K | Q4 publicado ~17,5 GB + KV; **32 GB mínimo práctico** | Baseline denso de reasoning/review | [Google model card](https://ai.google.dev/gemma/docs/core/model_card_4) |
| **Nemotron 3 Nano 30B-A3B** | **Open-weight, licencia propia NVIDIA Nemotron** | 31,6B / 3,2B (3,6B incl. embeddings) | hasta 1M | NVFP4 ~18–20 GB; FP8 ~30 GB; **24–32 GB** | Agentic/tools/RAG; candidato Blackwell | [NVIDIA research](https://research.nvidia.com/labs/nemotron/Nemotron-3/), [NVFP4 card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4) |
| **OLMo 3 Think/Instruct 32B** | Fully open, Apache 2.0 | 32B denso | 65.536 | Q4 ~16–20 GB; **24–32 GB** | Baseline transparente, reasoning/review | [Ai2](https://allenai.org/blog/olmo3), [model card](https://huggingface.co/allenai/Olmo-3-32B-Think) |
| **DeepSeek-V3.2** | Open-weight MIT | ~671B principal + MTP / 37B activos | ~128K | FP8 ~685 GB; Q4 >340 GB antes de KV | Referencia de calidad; cluster multi-GPU | [DeepSeek news](https://api-docs.deepseek.com/news/news251201/), [model card](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) |
| **DeepSeek-V4-Flash** | Open-weight MIT | 284B / 13B | 1M | >140 GB sólo pesos a ~4 bits | Referencia/servidor multi-GPU; fuera de workstation | [DeepSeek](https://api-docs.deepseek.com/news/news260424/), [model card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) |
| **DeepSeek-V4-Pro** | Open-weight MIT | 1,6T / 49B | 1M | orden >800 GB en formatos de baja precisión | Frontier multi-node/cloud privado | [GA announcement](https://api-docs.deepseek.com/news/news260813/), [model card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro) |

### Local embeddings

| Modelo | Licencia | Contexto | Recomendación |
|---|---|---:|---|
| Qwen3-Embedding 0.6B/4B/8B | Apache 2.0 | 32K | Empezar con 0.6B; escalar a 4B sólo por mejora medida en code retrieval. [Fuente](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) |
| Granite Embedding 97M/311M | Apache 2.0 | según variante | Alternativa ligera y multilingüe; buen fit empresarial. [Fuente](https://www.ibm.com/granite/docs/models/embedding) |
| EmbeddingGemma 300M | **términos Gemma propios**, no confundir con Gemma 4 | 2K | Sólo si se acepta su licencia y 2K es suficiente. [Fuente](https://ai.google.dev/gemma/docs/embeddinggemma/model_card) |

## 3. Runtime and Framework Comparison

### Serving runtimes

| Criterio | vLLM | Ollama | llama.cpp / llama-server | LM Studio / llmster |
|---|---|---|---|---|
| Licencia | Apache 2.0, OSS | MIT, OSS para runtime/repositorio | MIT, OSS | **Gratis propietario**, uso personal/interno |
| Rol | Producción concurrente | Laboratorio y gestión simple | GGUF, portabilidad CPU/GPU, fallback | GUI/UX de evaluación opcional |
| API | OpenAI Chat/Completions/Responses/Embeddings y APIs propias | Compatibilidad OpenAI parcial + API propia | Compatibilidad práctica; no promete identidad total | OpenAI/REST/Anthropic según runtime |
| Tools | Parsers por familia; named/auto/required/none | Tools y structured output dependientes de modelo | `--jinja`/templates; tools built-in experimentales desactivados | Parsers nativos/fallback; MCP aumenta superficie |
| Structured output | JSON Schema, regex, choice, grammar | JSON/JSON Schema | grammar/GBNF y JSON Schema | JSON Schema/grammar |
| Concurrencia | Continuous batching y tuning explícito | Paralelismo/cola simples | Slots + continuous batching | Parallel requests, menor control productivo |
| Multi-GPU | TP/PP/DP/EP, single/multi-node | reparto automático, poco control | split por capas; tensor split experimental | controles según backend |
| Cuantización | AWQ/GPTQ/FP8/INT4/MXFP4/Quark/KV; matriz variable | GGUF Q/K, KV q8/q4 | GGUF y KV cuantizada, CPU offload | GGUF/MLX |
| Observabilidad | Prometheus, TTFT/ITL/KV, dashboards, OTel | timings, `/api/ps`, logs; sin Prometheus oficial encontrado | métricas Prometheus/health/slots | log stream/stats; sin OTel/Prometheus oficial encontrado |
| Linux/GPU | CUDA y ROCm oficiales; mejor opción productiva | binario/systemd/Docker; CUDA/ROCm | CMake/Docker; CUDA/ROCm/Vulkan | daemon Linux cerrado |
| Riesgo clave | auth no cubre todos los endpoints; GGUF experimental | cloud opcional/endpoint sin auth propia robusta | templates/tools y multi-GPU requieren cuidado | dependencia propietaria y licencia restrictiva |

Fuentes: [vLLM server](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/), [tools](https://docs.vllm.ai/en/stable/features/tool_calling/), [quantization](https://docs.vllm.ai/en/stable/features/quantization/), [Ollama compatibility](https://docs.ollama.com/api/openai-compatibility), [Ollama FAQ](https://docs.ollama.com/faq), [llama-server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md), [LM Studio terms](https://lmstudio.ai/app-terms).

### Agent frameworks

| Framework | Licencia/condición | Durabilidad/HITL | Idempotencia y operación | Veredicto |
|---|---|---|---|---|
| **LangGraph core** | MIT OSS | Checkpoints por thread, pending writes, history/replay, `interrupt()`/`Command` | Efectos deben ser idempotentes; PostgresSaver en producción | **Principal v1** |
| **Temporal Server + SDK** | MIT OSS; Cloud es servicio propietario | Event History/replay, timers, Signals/Updates, workers desacoplados | Activities retry-safe/idempotentes, heartbeats/timeouts | **Capa futura** por SLA/multi-host |
| CrewAI core | MIT OSS; AMP es comercial | Flows con estado/persistencia/HITL | Garantías de replay menos precisas; ledger igualmente necesario | Alternativa de prototipo, no núcleo |
| Microsoft AutoGen | MIT OSS; **maintenance mode** | `save_state/load_state`; HITL | Persistencia/efectos dependen de la app | No iniciar proyecto nuevo |
| LangSmith self-hosted | Enterprise/licencia, no OSS gratuito | UI/deploy/tracing para LangGraph | Plataforma opcional | Excluir del camino local OSS inicial |

Fuentes: [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), [Temporal Activities](https://docs.temporal.io/activities), [Temporal messaging](https://docs.temporal.io/encyclopedia/workflow-message-passing), [CrewAI](https://github.com/crewAIInc/crewAI), [AutoGen](https://github.com/microsoft/autogen).

## 4. Target Architecture

```text
             ┌──────────────────────────────────────────────┐
             │ Operador: CLI + dashboard local              │
             │ approve/reject/edit/cancel · RBAC · CSRF     │
             └──────────────────┬───────────────────────────┘
                                │ HTTPS privado
             ┌──────────────────▼───────────────────────────┐
             │ API / Policy / Budget / Model Gateway        │
             │ idempotency · aliases · auth · rate limits   │
             └──────────────────┬───────────────────────────┘
                                │
             ┌──────────────────▼───────────────────────────┐
             │ LangGraph durable                            │
             │ plan → worktree → edit → test → evidence     │
             │      → review → HITL → merge local           │
             └──────┬───────────────┬────────────────┬──────┘
                    │               │                │
          ┌─────────▼──────┐ ┌──────▼────────┐ ┌────▼────────────┐
          │ PostgreSQL     │ │ Artifact Store│ │ Reverse proxy   │
          │ checkpoint     │ │ SHA-256       │ │ service auth    │
          │ ledger/outbox  │ │ redacted logs │ └────┬────────────┘
          │ leases/approval│ │ diffs/bundles │      │
          └─────────┬──────┘ └───────────────┘ ┌────▼────────────┐
                    │                           │ vLLM GPU        │
          ┌─────────▼────────────────┐          │ OpenAI contract │
          │ Runner rootless          │          └─────────────────┘
          │ worktree RW · host RO    │          Ollama/llama.cpp
          │ cgroups · net=none       │          sólo laboratorio
          │ Git/tests; nunca push    │
          └──────────────────────────┘
```

Estado durable mínimo: `job_id/thread_id`, workflow version, backlog/tarea/attempt, lifecycle enum, base/candidate SHA, diff hash, tests, review, checkpoint/approval, operation IDs, budgets, last event y referencias a artefactos. Cada efecto escribe primero una intención/ledger, usa clave idempotente y luego reconcilia resultado real.

## 5. Hardware Purchase Profiles

| Perfil | Configuración resumida | Coste estimado sin IVA/importación | Objetivo |
|---|---|---:|---|
| **Entrada** | R9700 32 GB; Ryzen 9 9950X; 128 GB ECC validada; NVMe 2+4 TB; 2.5/10 GbE; PSU 1000 W | **USD 3.800–5.000** | 1 agente; modelos 20–30B cuantizados; PoC ROCm obligatoria |
| **Recomendada** | RTX 5090 32 GB; Threadripper 9960X/TRX50; 256 GB ECC RDIMM; NVMe 2+8 TB; 10 GbE; PSU 1600 W | **USD 6.000–8.000** | 1–3 agentes, vLLM/CUDA, Qwen 30B + gpt-oss-20b alternados |
| **Alto rendimiento** | RTX PRO 6000 96 GB ECC; Threadripper PRO 9965WX/WRX90; 256–512 GB ECC; 2 TB + ≥15 TB NVMe; 10/25 GbE; PSU/chasis certificado | **USD 21.000–27.000** | 120B/119B cuantizado, mayor contexto/concurrencia |

El perfil recomendado prioriza líneas PCIe, ECC de sistema y expansión, no sólo CPU. Si no habrá segunda GPU/NIC/NVMe adicionales, puede abaratarse con AM5, pero se pierde flexibilidad. Para 5090/PRO 6000 deben validarse carga continua, conectores, temperatura ambiente y circuito/UPS. Para R9700, usar una versión de Ubuntu/RHEL expresamente soportada por ROCm.

## 6. Implementation Roadmap

1. **Benchmark:** construir dataset/runner reproducible; comparar modelos, cuantos, CUDA/ROCm y hardware disponible.
2. **Inferencia:** desplegar vLLM privado, alias/manifests, contract tests, métricas y Ollama/llama.cpp de laboratorio.
3. **Orquestador:** LangGraph + PostgreSQL; read-only, luego worktrees/runner, tests, review y HITL.
4. **Seguridad/operación:** egress policy, redacción, RBAC, backup/restore, alertas, runbooks y piloto controlado.
5. **Escalamiento:** ajustar contexto/batch/power cap; sólo entonces decidir 96 GB, réplica, segunda GPU o nodo separado.

El orden de las stories existentes puede mantenerse, pero Story 1.1 debe fijar PostgreSQL para producción; Story 1.5 debe usar ledger/leases además del checkpointer; Story 1.6 separa el nodo `interrupt()` del efecto aprobado; Story 1.8 conserva merge/deploy como gates independientes.

## 7. Benchmark and Acceptance Gates

### Reproducible protocol

- Manifest completo de hardware, OS/kernel/driver, runtime digest, model revision/hash/licencia, tokenizer/template/parser, cuantización y flags.
- Matriz de contextos 2K/8K/32K/objetivo, outputs 256/1K/4K y concurrencia 1/2/4/8.
- Warm-up + tres repeticiones; cold/warm; cache controlada; mediana/p95/p99.
- Suite real congelada: bugs, feature multiarchivo, refactor, navegación de repo, revisión de diff, tools/RAG y reinicio.
- Métricas: TTFT/TPOT/ITL/E2E, tokens/s/goodput, VRAM/KV/OOM, tests, tools, defectos, intervención, duplicados, secretos y Wh/tarea.
- Energía del sistema en pared; DCGM/ROCm SMI como telemetría complementaria; dBA y temperatura sostenida.

### Gate before purchase

- inputs humanos faltantes documentados;
- modelo/checkpoint/cuanto supera calidad mínima en repos representativos;
- SLO cumplido con concurrencia objetivo y margen operacional;
- prueba sostenida 8–24 h sin OOM/errores críticos;
- energía/ruido/temperatura dentro de límites;
- cotizaciones/garantía/TCO comparados;
- restore y compatibilidad exacta del stack demostrados.

### Gate before write automation

- ninguna capacidad/credencial/ruta de `git push`;
- worktree y runner aislados, red bloqueada y límites efectivos;
- cero duplicación bajo kill/reboot en puntos críticos;
- toda evidencia y aprobación está ligada a SHA/diff hash;
- merge/deploy separados y exclusivamente humanos;
- presupuestos detienen claramente el flujo;
- canarios de secretos y prompt injection pasan;
- backup/restore, cancelación, limpieza, rollback y runbooks probados;
- piloto read-only seguido de piloto write-isolated sin incidente crítico.

## 8. Risks and Human Decisions

| Prioridad | Riesgo | Respuesta |
|---|---|---|
| Alta | Modelo rápido pero incapaz de cerrar tareas reales | calidad/tests como gate; no optimizar tokens/s aislados |
| Alta | Duplicar efecto al reanudar | ledger, clave única, fencing/lease y reconciliación Git/filesystem |
| Alta | Prompt injection/exfiltración | policy fuera del prompt, tools mínimas, egress off, redacción y tests adversariales |
| Alta | Aprobación obsoleta | ligar a actor + SHA + diff hash + tests + policy; revalidar antes de merge |
| Alta | Pérdida de commits locales no enviados | Git bundles + artifact backup + PITR + restore drills |
| Media | OOM por KV/batch aunque pesos quepan | sweeps reales, límites de contexto/concurrencia y margen |
| Media | ROCm incompatibilidad por modelo/cuanto | PoC y pin exactos; NVIDIA si prima menor riesgo |
| Media | 5090/PRO 6000 excede potencia/ruido | power cap, chasis/PSU/circuito, medición sostenida |
| Media | CAPEX 96 GB no produce mejor resultado | benchmark ciego 30B vs 120B y TCO por tarea exitosa |
| Media | Upgrade rompe runs suspendidos | workflow version, drenaje/migración y tests de checkpoints |

Decisiones humanas pendientes: umbral de calidad, presupuesto, concurrencia/SLO, contexto, energía/dBA, RPO/RTO/retención, threat model de aislamiento, catálogo de repos/datos y política de licencias.

## 9. Licensing Classification

### 1 — Open source/permisivo Apache 2.0, MIT o equivalente

- Software: vLLM (Apache 2.0); LangGraph, Temporal, Ollama, llama.cpp, CrewAI, AutoGen (MIT); OpenTelemetry (Apache 2.0); PostgreSQL/pgvector (licencia PostgreSQL).
- Modelos: Qwen3-Coder, Qwen3-Coder-Next, gpt-oss, Mistral Small 4, Granite 4.2, Gemma 4, OLMo 3, DeepSeek-V3.2/V4 según cards exactas revisadas.

“Open source” aplicado a modelos sigue siendo discutido: la tabla usa la licencia publicada del checkpoint y distingue disponibilidad de pesos/código/datos. OLMo 3 ofrece el grado más fuerte de transparencia entre los candidatos.

### 2 — Open-weight con licencia propia o restricciones

- Nemotron 3 Nano: NVIDIA Nemotron Open Model License.
- EmbeddingGemma: términos Gemma propios.
- Cualquier modelo comunitario/quant derivado hereda obligaciones que deben verificarse por artefacto.

### 3 — Gratis pero no realmente open source

- LM Studio Desktop/llmster: binario propietario gratuito para uso personal/interno bajo sus términos; no dependencia crítica.
- LangSmith self-hosted y CrewAI AMP: productos/plataformas comerciales, no equivalen al core OSS.
- Endpoints web/API gratuitos o freemium: servicio gratuito no vuelve abiertos sus pesos, backend ni operación.

Cada manifest debe registrar `model_id`, revisión, hash, licencia, política de uso, origen, cuantización y aprobación legal/técnica.

## 10. Methodology, Confidence and Sources

### Methodology

Se revisaron los documentos locales, model cards, documentación y repositorios oficiales, especificaciones de GPU/CPU, matrices CUDA/ROCm y documentación operativa. Se separaron hechos publicados, cálculos aproximados e inferencias. No se usaron benchmarks de marketing como sustituto del benchmark propuesto.

### Confidence

- **Alta:** licencias de software, capacidades documentadas, parámetros/contextos publicados, especificaciones físicas de GPU, semántica de LangGraph/Temporal y arquitectura base.
- **Media:** VRAM práctica, concurrencia y rendimiento relativos; dependen de checkpoint/cuanto/runtime/hardware.
- **Baja hasta medir:** tasa de éxito en repos propios, SLO final, Wh/tarea, ruido real, coste puesto en Chile y beneficio de 120B frente a 30B.

### Primary source index

- [vLLM documentation](https://docs.vllm.ai/en/latest/), [license](https://github.com/vllm-project/vllm/blob/main/LICENSE), [benchmark CLI](https://docs.vllm.ai/en/latest/benchmarking/cli/).
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview), [persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), [license](https://github.com/langchain-ai/langgraph/blob/main/LICENSE).
- [Temporal docs](https://docs.temporal.io/), [Activities](https://docs.temporal.io/activities), [limits](https://docs.temporal.io/workflow-execution/limits), [server](https://github.com/temporalio/temporal).
- [Ollama docs](https://docs.ollama.com/), [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md), [LM Studio terms](https://lmstudio.ai/app-terms).
- [RTX 5090](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/), [RTX PRO 6000](https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000/), [R9700](https://www.amd.com/en/products/graphics/workstations/radeon-ai-pro/ai-9000-series/amd-radeon-ai-pro-r9700.html), [ROCm compatibility](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/native_linux/native_linux_compatibility.html).
- Model sources appear adjacent to every row in the comparison table.

## Technical Research Conclusion

La oportunidad no consiste sólo en alojar un LLM grande. El activo técnico es un sistema local reproducible que convierte propuestas probabilísticas en cambios candidatos limitados, probados, revisados, trazables y aprobados. La arquitectura recomendada logra ese objetivo con componentes OSS existentes y mantiene intercambiables modelo, runtime y GPU.

El siguiente paso correcto es aprobar una **fase 0 de benchmark**, no una GPU. Su resultado debe fijar el modelo principal y los SLO, completar los ocho inputs humanos pendientes y producir una recomendación económica puesta en Chile. Si 32 GB cumple calidad/concurrencia, la RTX 5090 o R9700 evitan sobredimensionamiento; si el valor de 120B es material y repetible, la RTX PRO 6000 ofrece el salto operacional más limpio.

**Technical Research Completion Date:** 2026-08-28  
**Source verification:** fuentes primarias vigentes enlazadas  
**Overall confidence:** alta en arquitectura/selección de stack; media en hardware hasta benchmark; compra final bloqueada por inputs humanos explícitos.
