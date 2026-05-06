# Comparativa Actualizada de IA de Pesos Abiertos (Open-Weight)

Actualizado: **8 de abril de 2026**.

Este documento prioriza datos verificables desde fuentes oficiales (model cards y blogs de los laboratorios). Se usa el término **open-weight** porque no todos estos modelos cumplen la definición estricta de open source de la OSI.

## Resumen ejecutivo

1. El ecosistema open-weight maduró rápido entre 2025 y 2026: hay modelos fuertes para razonamiento, agentes, coding y multimodal.
2. La diferencia real ya no es solo "calidad"; es **licencia + costo de inferencia + contexto + tooling**.
3. Varias comparativas virales mezclan cifras no oficiales. Aquí se corrigen con datos de origen.

## Tabla comparativa (modelos relevantes)

| Modelo | Tipo de apertura / licencia | Parámetros (total / activos) | Contexto | Modalidad | Comentario práctico |
| --- | --- | --- | --- | --- | --- |
| **Llama 4 Scout** (Meta) | Licencia **Llama 4 Community** (no OSI) | 109B / 17B (MoE) | 10M | Texto + imagen (salida texto/código) | Muy fuerte en contexto ultra largo, pero con licencia propia y restricciones de uso a gran escala. |
| **Llama 4 Maverick** (Meta) | Licencia **Llama 4 Community** (no OSI) | 400B / 17B (MoE) | 1M | Texto + imagen (salida texto/código) | Variante mayor de Llama 4; buen equilibrio capacidad/costo por MoE. |
| **Qwen3-235B-A22B-Instruct-2507** | **Apache 2.0** | 235B / 22B (MoE) | 262,144 nativo (extensible ~1,010,000) | Texto | Muy competitivo en agente/tool use y coding; versión 2507 mejora contexto largo. |
| **DeepSeek-V3** | Código MIT + licencia de modelo propia | 671B / 37B (MoE) | 128K | Texto | Muy fuerte en razonamiento/código; uso comercial permitido según model card, bajo su licencia de modelo. |
| **NVIDIA Nemotron 3 Super** | Open-weight + datos/recetas abiertas (ecosistema Nemotron) | 120B / 12B (MoE híbrido Mamba-Transformer) | hasta 1M | Texto (enfoque agentic) | Enfocado a throughput y agentes multietapa; fuerte apuesta de NVIDIA en 2026. |
| **Mistral Small 3.1 (24B)** | **Apache 2.0** | 24B denso | 128K | Texto + imagen | Muy buena opción local/empresa para multimodal liviano y function calling. |
| **Gemma 3 (Google)** | Licencia Gemma (pesos abiertos con términos) | 1B / 4B / 12B / 27B | 32K (1B), 128K (4B/12B/27B) | Texto + imagen (excepto 1B texto) | Excelente relación calidad/recursos para despliegue local y edge. |
| **gpt-oss-120b / gpt-oss-20b** (OpenAI) | **Apache 2.0** | 117B / 5.1B y 21B / 3.6B (MoE) | 128K | Texto | Open-weight de OpenAI (2025), diseñado para razonamiento + tool use eficiente. |
| **Phi-4-reasoning / Phi-4-mini-instruct** (Microsoft) | **MIT** | 14B (reasoning) / 3.8B (mini) | 32K (reasoning), 128K (mini) | Texto | Buen rendimiento por costo en hardware más acotado. |

## Modelos nuevos (no estaban en el listado anterior)

Estas familias/modelos aparecieron o tomaron relevancia después del set que teníamos originalmente:

| Modelo/Familia | Estado reciente | Parámetros / contexto (según fuente oficial) | Licencia | Nota práctica |
| --- | --- | --- | --- | --- |
| **Gemma 4** (Google DeepMind) | Lanzado el 2 de abril de 2026 | E2B, E4B, 26B MoE, 31B Dense; 128K (edge) y hasta 256K (largos) | **Apache 2.0** | Salto importante para edge + agentic; reemplaza a Gemma 3 como referencia principal de la familia. |
| **Qwen 3.5** (Alibaba/Qwen) | Nueva familia posterior a Qwen3 | Ejemplo: 397B total / 17B activos, 262,144 nativo (extensible ~1,010,000) | **Apache 2.0** | Muy fuerte para tool use/coding/visión-lenguaje en variantes grandes. |
| **Nemotron 3 Ultra / Omni / VoiceChat** (NVIDIA) | Expansión anunciada 16 de marzo de 2026 | Ultra (familia 3): ~500B total / ~50B activos; Omni y VoiceChat agregan multimodal/voz | Open-weight (ecosistema Nemotron) | Línea claramente orientada a agentes multimodales y producción sobre stack NVIDIA. |
| **OLMo 3.1** (Ai2) | Update de OLMo 3 anunciado el 12 de diciembre de 2025 | Checkpoints 32B Think/Instruct (familia 7B/32B) | **Apache 2.0** | Destaca por transparencia de datos/recetas y reproducibilidad científica. |
| **Mistral 3 / Ministral 3** (Mistral AI) | Nueva generación abierta publicada en 2026 | Ministral 14B/8B/3B + Mistral Large 3 (675B total / 41B activos) | **Apache 2.0** | Cobertura completa desde edge/local hasta frontier open model empresarial. |
| **Granite 4.0** (IBM) | Lanzado el 2 de octubre de 2025 y consolidado en 2026 | Familia híbrida (incluye MoE), p. ej. 32B total / 9B activos en variantes H-Small; 128K | **Apache 2.0** | Muy fuerte en costo/eficiencia para RAG y agentes empresariales. |

## Correcciones clave respecto a comparativas antiguas

1. **"Open source" vs "open-weight"**: Llama 4 y Gemma 3 publican pesos, pero sus licencias no son equivalentes a Apache/MIT.
2. **Llama 4 licencia**: incluye términos comerciales adicionales (por ejemplo, cláusula de MAU altos), por lo que no conviene tratarla como Apache-like.
3. **DeepSeek-V3**: no es simplemente "MIT" para todo; el código está en MIT, y el modelo bajo licencia específica.
4. **Mistral**: lo más sólido y realmente abierto en 2025-2026 para uso amplio sigue siendo la línea Apache 2.0 (por ejemplo, Mistral Small 3.1).
5. **Qwen3**: la rama reciente 2507 sube notablemente el contexto nativo frente a versiones previas.
6. **Gemma**: la referencia actual ya es **Gemma 4** (Apache 2.0), no Gemma 3.
7. **NVIDIA Nemotron**: además de Nano/Super/Ultra, en 2026 aparecen Omni y VoiceChat para casos multimodales y voz en tiempo real.

## Recomendación rápida por perfil

1. **Empresa que prioriza licencia permisiva**: Qwen3 o Mistral Small 3.1 (Apache 2.0), también gpt-oss (Apache 2.0).
2. **Agentes con contexto largo**: Llama 4 Scout (10M) o Nemotron 3 (hasta 1M), validando licencia y costo real de inferencia.
3. **Local con hardware moderado**: Gemma 4 (E2B/E4B) y Phi-4-mini-instruct.
4. **Coding + tool use de alto nivel**: Qwen3-235B-A22B-Instruct-2507, DeepSeek-V3 o gpt-oss-120b según presupuesto y stack.

## Fuentes (oficiales)

- Meta Llama 4 Scout model card: https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct
- Meta Llama 4 Maverick model card: https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct
- Qwen3-235B-A22B-Instruct-2507: https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507
- Qwen3-235B-A22B: https://huggingface.co/Qwen/Qwen3-235B-A22B
- DeepSeek-V3 model card: https://huggingface.co/deepseek-ai/DeepSeek-V3
- NVIDIA Nemotron portal: https://developer.nvidia.com/nemotron
- NVIDIA Nemotron 3 family: https://research.nvidia.com/labs/nemotron/Nemotron-3/
- NVIDIA Nemotron 3 Super: https://research.nvidia.com/labs/nemotron/Nemotron-3-Super/
- Mistral Small 3.1 model card: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
- Gemma 3 model card (Google): https://huggingface.co/google/gemma-3-12b-pt
- Gemma 3 overview (HF): https://huggingface.co/blog/gemma3
- OpenAI gpt-oss announcement: https://openai.com/index/introducing-gpt-oss/
- OpenAI gpt-oss-120b model card: https://huggingface.co/openai/gpt-oss-120b
- Microsoft Phi-4-reasoning: https://huggingface.co/microsoft/Phi-4-reasoning
- Microsoft Phi-4-mini-instruct: https://huggingface.co/microsoft/Phi-4-mini-instruct
- Gemma 4 announcement (Google): https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
- Gemma 4 edge/developer details: https://developers.googleblog.com/bring-state-of-the-art-agentic-skills-to-the-edge-with-gemma-4/
- Qwen3.5-397B-A17B model card: https://huggingface.co/Qwen/Qwen3.5-397B-A17B
- Qwen3.5-35B-A3B model card: https://huggingface.co/Qwen/Qwen3.5-35B-A3B
- NVIDIA Nemotron expansion (Ultra/Omni/VoiceChat): https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Expands-Open-Model-Families-to-Power-the-Next-Wave-of-Agentic-Physical-and-Healthcare-AI/default.aspx
- NVIDIA Nemotron 3 family page: https://research.nvidia.com/labs/nemotron/Nemotron-3/
- Ai2 OLMo 3 / 3.1 announcement: https://allenai.org/blog/olmo3
- OLMo 3.1 32B Instruct model card: https://huggingface.co/allenai/Olmo-3.1-32B-Instruct
- Mistral 3 announcement: https://mistral.ai/news/mistral-3
- IBM Granite 4.0 announcement: https://www.ibm.com/new/announcements/ibm-granite-4-0-hyper-efficient-high-performance-hybrid-models
- IBM Granite docs (4.0): https://www.ibm.com/us-en/granite/docs/models/granite
