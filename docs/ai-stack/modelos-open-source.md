# Comparativa de modelos para desarrollo y agentes locales

**Fecha de verificación:** 2026-08-28  
**Criterio de inclusión:** pesos descargables y licencia que permita evaluar el uso local. Se distinguen modelos con licencia realmente permisiva de los meramente *open-weight*.

## Conclusión

Para una máquina especializada en desarrollo no conviene servir un único modelo gigantesco. El conjunto inicial más equilibrado es:

| Rol | Primera elección | Alternativa | Motivo |
| --- | --- | --- | --- |
| Modelo principal de desarrollo | **Qwen3-Coder-30B-A3B-Instruct** | `gpt-oss-20b` | Qwen está especializado en código y tareas agénticas; su arquitectura MoE reduce cómputo activo. |
| Razonamiento/revisión compleja | **gpt-oss-20b** | Granite 4.2 de tamaño medio | Apache 2.0, razonamiento configurable, tool use y requisitos manejables para una GPU de 32 GB. |
| Enrutamiento, extracción y tool calls baratos | **Granite 4.0 H-Tiny/Micro** | Qwen3 8B | Menor coste, licencia Apache 2.0, orientado a function calling/agentes. |
| Modelo de frontera posterior | **Mistral Small 4** | `gpt-oss-120b` | 119B/6.5B activos y 256K; necesita al menos ~80 GB operativos. |

No se recomienda utilizar Llama como base contractual del producto: publica pesos bajo una licencia comunitaria propia, no Apache/MIT. Gemma 4 sí declara Apache 2.0 y queda como candidato compacto. DeepSeek se mantiene como candidato de laboratorio, pero no debe entrar en la selección final sin revisar la licencia exacta del checkpoint elegido. Una licencia debe validarse por modelo y versión antes de producción.

## Modelos candidatos

La cifra de VRAM es un **orden de magnitud de los pesos cuantizados**; no incluye caché KV, contexto, batch, runtime ni margen operativo. Para producción reservar como mínimo un 20–30 % adicional y medir con el contexto objetivo.

| Modelo | Licencia | Parámetros total / activos | Contexto | Adecuación | Pesos a ~4 bits | Perfil de hardware |
| --- | --- | ---: | ---: | --- | ---: | --- |
| **gpt-oss-20b** | Apache 2.0 + política de uso | 21B / 3.6B | 128K | Muy buen razonamiento, tool use y salida estructurada; excelente revisor/orquestador. | ~13 GB (MXFP4 oficial) | 16 GB es el mínimo publicado; 24–32 GB es práctico. |
| **gpt-oss-120b** | Apache 2.0 + política de uso | 117B / 5.1B | 128K | Revisión y razonamiento de mayor calidad; modelo principal cuando existe VRAM suficiente. | ~61 GB (checkpoint MXFP4) | 80 GB publicado; 96 GB da margen real. |
| **Qwen3-Coder-30B-A3B-Instruct** | Apache 2.0 | 30B / 3B | verificar en model card al instalar | Coding y ejecución con herramientas a escala local. | ~15–18 GB | 24 GB mínimo razonable; 32 GB recomendado. |
| **Qwen3-Coder-Next** | Apache 2.0 | 80B / 3B | 256K nativo; 1M extendido | Coding agents y tool format; opción especializada de alta capacidad. | ~45–50 GB con margen | 48 GB mínimo práctico; 64 GB recomendado. |
| **Qwen3-Coder-480B-A35B-Instruct** | Apache 2.0 | 480B / 35B | 256K nativo; 1M extendido | Candidato frontier para repositorios grandes y coding agéntico. | ~240 GB sólo pesos | Nodo multi-GPU; no es objetivo de una workstation inicial. |
| **IBM Granite 4.0 H-Small** | Apache 2.0 | 32B / 9B | 128K | RAG, function calling y agentes empresariales; buen agente auxiliar. | ~16–20 GB | 24–32 GB. |
| **IBM Granite 4.2** | Apache 2.0 | familia de tamaños; confirmar variante | confirmar por model card | Actualización 2026 con razonamiento, código y tool use; evaluar antes de fijar versión. | depende de variante | Elegir según benchmark propio. |
| **Mistral Small 4** | Apache 2.0 | 119B / 6.5B | 256K | Generalista con código, razonamiento, agentes y visión. | ~60 GB sólo pesos | Prever 80 GB o más con KV y concurrencia. |
| **Gemma 4 26B A4B** | Apache 2.0 | 25.2B / 3.8B | 256K | Alternativa compacta con thinking, código, function calling y visión. | ~14.4 GB Q4 oficial | 24 GB permite operación inicial. |
| **NVIDIA Nemotron 3 Nano 30B-A3B** | Nemotron Open Model License (no Apache) | 30B / 3.5B | hasta 1M | Agentes, razonamiento y tool calling; evaluar si se prioriza el ecosistema NVIDIA. | ~18–20 GB | 24–32 GB; confirmar soporte NVFP4/runtime. |
| **OLMo 3 Think 32B** | Apache 2.0 | 32B denso | 65,536 | Opción de investigación con datos, código y checkpoints transparentes. | ~18–22 GB | 24–32 GB. |
| **Mistral Small 3.1** | Apache 2.0 | 24B denso | 128K | Multimodal y function calling; útil como referencia de benchmark. | ~12–16 GB | Está retirado para nuevas integraciones; usar Small 4 si el benchmark lo permite. |
| **DeepSeek-V3.2 / V4** | validar checkpoint; V3.2 declara MIT | muy grande (MoE) | validar model card | Investigación de razonamiento/agentes; alto coste de memoria total pese a pocos parámetros activos. | muy superior a 100 GB | No para la primera máquina. |

## Modelos que no son la base recomendada

| Familia | Razón |
| --- | --- |
| Llama 4 | Licencia comunitaria propia, no Apache/MIT; revisar términos comerciales y de distribución antes de adoptarla. |
| AutoGen | Es un framework, no un modelo; su repositorio oficial está en modo de mantenimiento. No iniciar un proyecto nuevo sobre él. |

## Selección por VRAM

| VRAM disponible | Modelo/uso viable | Decisión |
| --- | --- | --- |
| 16 GB | `gpt-oss-20b` como mínimo declarado; modelos 3–8B auxiliares | laboratorio y un agente a la vez. |
| 24 GB | Qwen3-Coder-30B-A3B cuantizado o Mistral Small 3.1 con contexto moderado | entrada aceptable; el margen de KV es limitado. |
| **32 GB** | Qwen3-Coder-30B-A3B + `gpt-oss-20b` cargados de forma alternada/por servidor; Granite auxiliar | **punto de partida recomendado**. |
| 48–64 GB | Qwen3-Coder-Next, mayor contexto y modelos densos de 32B con holgura | buen nodo de evaluación, no sustituye 96 GB para 120B. |
| 80–96 GB | `gpt-oss-120b` MXFP4 o Mistral Small 4 con contexto/productividad razonables | modelo principal de alta capacidad. |
| Multi-GPU > 160 GB | Qwen3-Coder-480B-A35B u otros MoE frontier | sólo después de pruebas de throughput, partición y coste energético. |

## Fuentes primarias consultadas

- [OpenAI: introducción y requisitos de gpt-oss](https://openai.com/index/introducing-gpt-oss/) — tamaños, contexto, MXFP4 y 16/80 GB.
- [OpenAI: ficha de gpt-oss-120b](https://developers.openai.com/api/docs/models/gpt-oss-120b) — Apache 2.0, tool use y 117B/5.1B.
- [Qwen: Qwen3-Coder](https://qwenlm.github.io/blog/qwen3-coder/) — 480B/35B, 256K/1M y enfoque agentic coding.
- [Qwen3-Coder-30B-A3B model card](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct) — licencia Apache 2.0 e instrucciones de inferencia.
- [Repositorio Qwen3-Coder](https://github.com/QwenLM/Qwen3-Coder) — Qwen3-Coder-Next y su uso local.
- [IBM Granite 4.0](https://www.ibm.com/granite/docs/models/granite4-0) y [Granite 4.2](https://research.ibm.com/blog/introducing-granite-4-2) — agentes, tamaños y Apache 2.0.
- [Mistral Small 4](https://mistral.ai/news/mistral-small-4/) y [su ficha](https://docs.mistral.ai/models/mistral-small-4-0-26-03) — capacidad y requisitos de despliegue.
- [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) — licencia, arquitectura y variantes.
- [Nemotron 3 Nano 30B-A3B model card](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b/modelcard) — licencia y enfoque agéntico.
- [OLMo 3](https://allenai.org/blog/olmo3) — transparencia y licencia Apache 2.0.
- [DeepSeek Transparency Center](https://www.deepseek.com/en/transparency/) y [model card V3.2](https://fe-static.deepseek.com/chat/transparency/deepseek-v3.2-model-card-0414-EN.pdf) — estado y licencia declarada.
