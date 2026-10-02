# Especificación de arquitectura: motor de IA local para desarrollo

**Estado:** propuesta inicial; no instala ni expone servicios.  
**Fecha:** 2026-08-28

## Decisión de arquitectura

Se adopta un stack compuesto por proyectos open source existentes:

```text
Operador / Dashboard local
        │ HTTPS privado + RBAC
        ▼
API de control ───────► PostgreSQL (estado, tareas, aprobaciones)
        │                         └── JSONL/artefactos redactados
        ▼
LangGraph (orquestación durable y checkpoints humanos)
        ├── planificador / revisor ─► API OpenAI-compatible de vLLM ─► GPU/modelos
        ├── ejecutor ───────────────► Codex CLI u otro adaptador, worktree aislado
        ├── herramientas ───────────► Git, tests, linters, SAST, documentación
        └── memoria/RAG ────────────► embeddings + PostgreSQL/pgvector
                                      ▲
                         Ollama (laboratorio, GGUF y fallback local)
```

| Capa | Elección | Justificación |
| --- | --- | --- |
| Inferencia de servicio | **vLLM** | OpenAI-compatible API, tool calling, reasoning parsers, salida estructurada, batching continuo y soporte de MoE; apropiado para varios agentes. |
| Inferencia de laboratorio | **Ollama** | Gestión simple de modelos y GGUF para pruebas locales o fallback; no es el servidor de alta concurrencia. |
| Orquestación | **LangGraph** | MIT, estado durable, pausas/reanudación y human-in-the-loop; encaja con las épicas existentes. |
| Durabilidad de mayor escala | **Temporal** (opcional, fase posterior) | MIT y workflows con retries durables. No agregarlo en v1: LangGraph + PostgreSQL cubre el alcance actual. |
| Persistencia | PostgreSQL + pgvector; archivos de evidencia inmutables | Estado transaccional, memoria recuperable y trazabilidad. SQLite sigue válido para el prototipo de un operador ya especificado. |
| Observabilidad | OpenTelemetry + Prometheus + Grafana + Loki | Estándares abiertos para métricas, trazas y logs; redactar secretos antes de persistir. |
| Aislamiento | worktrees Git + contenedor/rootless por tarea + política de comandos | Conserva `main`, limita alcance y permite reproducir cada cambio. |

No se selecciona CrewAI ni AutoGen como núcleo. CrewAI es MIT pero añade una abstracción que no se necesita para el grafo explícito requerido; AutoGen está en maintenance mode. Tampoco se selecciona un framework visual como sustituto del orquestador: puede ser una interfaz posterior, no la fuente de verdad de los estados y aprobaciones.

## Roles y modelos

| Agente | Responsabilidad | Modelo inicial | Límites obligatorios |
| --- | --- | --- | --- |
| Router | Clasificar complejidad, elegir modelo y presupuesto | Granite pequeño/Qwen pequeño | No ejecuta comandos ni modifica repositorios. |
| Planner | Crear tareas estructuradas y conciliación de backlog | `gpt-oss-20b` | JSON validado, máximo de reintentos y sin confiar instrucciones del repositorio. |
| Executor | Cambios en worktree y verificaciones | Qwen3-Coder-30B-A3B; Qwen3-Coder-Next desde 48 GB de VRAM, o adaptador Codex | Sólo directorio de tarea, allowlist de comandos/red, timeout y sin `push`. |
| Reviewer | Revisar diff exacto, criterios y tests | `gpt-oss-20b`; escalar a 120b cuando exista | No aprueba su propio cambio; invalida revisión al cambiar SHA. |
| Retrieval | Recuperar reglas, arquitectura y documentación | embeddings locales | Sólo lectura; fuentes y fragmentos citados. |
| Human gate | Aprobar, editar, rechazar o cancelar | humano | Merge, deploy, credenciales, borrados y acceso externo requieren decisión explícita. |

## Especificación de hardware

### Perfil recomendado: workstation extensible

- Linux LTS, preferentemente Ubuntu Server/Desktop LTS o equivalente soportado por drivers CUDA.
- CPU: 16 o más núcleos modernos con líneas PCIe suficientes para la GPU y dos NVMe; priorizar plataforma con ECC si el presupuesto lo permite.
- RAM: **128 GB** (mínimo 64 GB). Evita degradar la máquina al indexar repositorios, compilar y sostener caché/artefactos.
- GPU: **NVIDIA RTX 5090, 32 GB GDDR7**, para ejecutar modelos de 20–35B cuantizados y desarrollo CUDA/vLLM con el mejor ecosistema.
- Almacenamiento: NVMe 4 TB para modelos/datasets + NVMe 2 TB separado para SO, bases de datos, worktrees y logs. Cifrado de volumen y copias de seguridad verificadas.
- Red: Ethernet 2.5/10 GbE si atenderá a otros equipos; nunca exponer vLLM/Ollama directamente a Internet.
- Fuente, placa y chasis: dimensionados para GPU de alto consumo, refrigeración continua y futura segunda GPU; confirmar con el integrador la separación PCIe, conectores y límites térmicos.

### Perfil de alto rendimiento

Una **NVIDIA RTX PRO 6000 Blackwell Workstation Edition (96 GB ECC)** permite ejecutar `gpt-oss-120b` en su formato MXFP4 con margen operacional. Requiere gabinete y fuente para hasta 600 W de GPU, además de plataforma que soporte su tamaño y refrigeración. Es la opción preferible a una multi-GPU de consumo cuando la prioridad es una sola instancia de alta capacidad y operación estable.

### Alternativa AMD

La Radeon AI PRO R9700 ofrece 32 GB, ECC en Linux, 300 W y ROCm. Es una alternativa viable si se valida primero el modelo exacto y vLLM/ROCm con una prueba de rendimiento. NVIDIA sigue siendo la opción de menor riesgo para esta primera implementación por disponibilidad de contenedores, kernels y ejemplos de despliegue; no es una restricción arquitectónica.

## Requisitos no funcionales

1. **Seguridad:** red privada por defecto, autenticación, RBAC, TLS, secretos fuera del prompt/log, escaneo de dependencias y política explícita de egress.
2. **Control humano:** no autoaprobar merge/deploy; soportar `approve`, `reject`, `edit`, `cancel`, con usuario, fecha, motivo y SHA exacto.
3. **Durabilidad:** cada efecto externo tiene `operation_id`; el reinicio no lo duplica. Estado recuperable desde PostgreSQL y evidencias con checksum.
4. **Trazabilidad:** cada tarea referencia objetivo, prompt versionado, modelo/quantización, herramientas, base SHA, candidate SHA, diff, resultados de tests y revisión.
5. **Control de recursos:** concurrencia por modelo, límite de tokens/contexto, timeout, máximo de iteraciones, cuota por tarea y parada segura.
6. **Privacidad:** por la naturaleza de SIS/Abax y datos de salud, no enviar código, dumps de BD ni datos personales a servicios externos por defecto; usar datos mock y redacción antes de RAG/logs.

## Plan de adopción

| Fase | Resultado verificable |
| --- | --- |
| 0. Validación | Benchmark reproducible de 2–3 modelos en la GPU elegida: tokens/s, latencia, VRAM, calidad en tareas reales y tool calls. |
| 1. Inferencia | vLLM autenticado en red privada, modelos versionados, health checks y Ollama sólo para laboratorio. |
| 2. Orquestador | Implementar Stories 1.1–1.7 ya definidas: estado, worktree, revisión, checkpoints, reanudación y límites. |
| 3. Gate operacional | Dashboard, alertas, backups, restauración probada, política de secretos y revisión de seguridad. |
| 4. Escalamiento | Medir saturación. Sólo entonces decidir segunda GPU, RTX PRO 6000 o un nodo independiente. |

## Criterios de aceptación de la fase 0

- Un `docker compose` o servicio reproducible inicia vLLM, PostgreSQL y el orquestador sin credenciales embebidas.
- Los modelos se eligen por alias versionado, con hash/origen/licencia registrados.
- Una tarea de ejemplo crea un worktree, pasa pruebas, produce diff y queda en checkpoint de aprobación; no modifica `main` ni hace `push`.
- Tras reiniciar durante la tarea, `resume <thread_id>` no duplica comandos ni efectos.
- El dashboard y CLI muestran el mismo estado; los secretos de una prueba controlada no aparecen en logs ni artefactos.
- Se publica el benchmark y la decisión de compra/upgrade con VRAM observada, no con supuestos.

## Fuentes técnicas

- [vLLM](https://docs.vllm.ai/en/stable/) — API compatible con OpenAI, tool calling, structured outputs y soporte MoE.
- [LangGraph: durable execution](https://docs.langchain.com/oss/python/langgraph/overview) y [human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop).
- [Licencia MIT de LangGraph](https://github.com/langchain-ai/langgraph/blob/main/LICENSE) y [Temporal](https://github.com/temporalio/temporal).
- [AutoGen: maintenance mode](https://github.com/microsoft/autogen) y [CrewAI: licencia MIT](https://github.com/crewAIInc/crewAI).
- [RTX 5090: 32 GB](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/), [RTX PRO 6000 Blackwell: 96 GB ECC/600 W](https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000/) y [Radeon AI PRO R9700: 32 GB](https://www.amd.com/en/products/graphics/workstations/radeon-ai-pro/ai-9000-series/amd-radeon-ai-pro-r9700.html).
