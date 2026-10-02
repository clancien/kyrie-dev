# Stack local de IA para desarrollo

**Estado:** propuesta de especificación inicial  
**Actualizado:** 2026-08-28

Esta carpeta define una estación de trabajo soberana para ejecutar modelos de IA locales y un flujo de agentes capaz de planificar, modificar, validar y dejar evidencia de tareas de desarrollo. Es una evolución coherente con el orquestador descrito en `doc/awf:agentic-work-flow/epics.md` y conserva sus límites: worktrees aislados, persistencia, revisión, checkpoints humanos y ningún `push` remoto.

## Documentos

- [Comparativa de modelos](modelos-open-source.md): candidatos open source/open-weight, licencias, capacidad y ajuste de memoria.
- [Arquitectura recomendada](arquitectura-recomendada.md): decisión de stack, perfiles de hardware, interfaces y criterios de aceptación.

## Decisión resumida

Construir sobre software existente y permisivo: **vLLM** como servidor de producción, **Ollama** para pruebas y modelos GGUF, **LangGraph** como orquestador durable, **PostgreSQL + JSONL** para estado/evidencia, y **OpenTelemetry + Prometheus/Grafana** para observabilidad. No se propone crear un runtime de inferencia ni un motor de workflows propio.

Para la primera máquina se recomienda Linux y una GPU NVIDIA con al menos **32 GB de VRAM**; la configuración base es una RTX 5090, 128 GB de RAM ECC cuando la plataforma lo permita, 4 TB NVMe para modelos y datos, y un segundo NVMe separado para ejecuciones. Permite ejecutar de forma cómoda `gpt-oss-20b`, Qwen3-Coder-30B-A3B y modelos auxiliares. Para un modelo principal de ~120B cuantizado y varios agentes concurrentes, pasar a una RTX PRO 6000 Blackwell de 96 GB o a un nodo multi-GPU validado.

> No comprar ni instalar aún: el dimensionamiento final depende de concurrencia, latencia, presupuesto, energía y de si el modelo principal será 20–35B o ~120B. La arquitectura evita quedar atada a esa decisión.

## Alcance de la primera entrega

1. Un modelo principal de código, un modelo rápido de clasificación/enrutamiento y un modelo de embeddings locales.
2. API local compatible con OpenAI, autenticada y sólo accesible por red privada.
3. Flujo de agentes para planificar → ejecutar en worktree → probar → revisar → pedir aprobación humana.
4. Reanudación durable, trazabilidad por tarea y control explícito de presupuestos, tiempo y permisos.

Quedan fuera la autonomía de despliegue, la exposición pública del servicio y la ejecución sin aprobación de operaciones irreversibles.
