---
title: "Brief de producto: motor local de IA para desarrollo"
status: draft
created: 2026-08-28
updated: 2026-08-28
---

# Brief de producto: motor local de IA para desarrollo

## Resumen ejecutivo

Se propone una workstation soberana que ejecute modelos locales para asistir y automatizar desarrollo de software. El producto combina inferencia de modelos abiertos/permisivos con un orquestador durable de agentes: planifica trabajo, ejecuta cambios sólo en worktrees aislados, prueba y revisa los resultados, y solicita una decisión humana antes de merge, deploy u otra acción irreversible.

La primera versión privilegia herramientas open source disponibles: vLLM, Ollama, LangGraph, PostgreSQL/pgvector y OpenTelemetry. La selección inicial de modelos es Qwen3-Coder-30B-A3B para código, gpt-oss-20b para planificación/revisión y Granite pequeño para enrutamiento. La solución escala a gpt-oss-120b sólo si se justifica una GPU de 80–96 GB.

## Problema

El desarrollo de sistemas complejos —en particular la evolución de SIS hacia Abax— demanda inspección extensa de código, migraciones, documentación, pruebas y revisión constante. Los agentes cloud pueden comprometer soberanía, datos y previsibilidad de coste; ejecutar una sola IA grande en una máquina sin workflow controlado no entrega trazabilidad ni seguridad operativa.

La documentación existente exige persistencia, reanudación, evidencia por SHA, límites, worktrees y checkpoints humanos. Falta la especificación que convierta esos requisitos en una estación local dimensionable y en una selección verificable de modelos y componentes.

## Solución

Una API local de modelos, un orquestador basado en grafo de estados y una capa de herramientas acotada trabajan como un sistema único. El router selecciona el modelo según complejidad; el planificador genera tareas estructuradas; el ejecutor opera en un worktree; el revisor valida el diff y los tests; y el humano resuelve operaciones sensibles. PostgreSQL y artefactos de evidencia permiten retomar una ejecución después de un reinicio.

La configuración inicial sugerida es Linux, RTX 5090 de 32 GB, 128 GB de RAM y 6 TB NVMe repartidos en dos unidades. Es suficiente para la primera validación con modelos de 20–35B cuantizados y deja explícita la ruta de escalamiento a una GPU de 96 GB para modelos de ~120B.

## Diferenciación y principios

- Soberanía práctica: código, prompts, resultados y memoria permanecen locales por defecto.
- Gobernanza antes de autonomía: no hay `push` remoto ni aprobación implícita de merge/deploy.
- Evidencia reproducible: toda tarea enlaza modelo, versión, prompt, comando, base SHA, candidate SHA, tests y veredicto.
- Selección por licencia y medición: Apache/MIT se prefiere a licencias de pesos con condiciones propias; el hardware se decide por benchmark real.

## Usuarios y éxito

El usuario primario es el equipo técnico que opera y moderniza sistemas informáticos con datos sensibles. Tiene éxito cuando puede delegar tareas repetibles o de exploración sin perder control de cambios, cuando una interrupción no pierde progreso y cuando puede auditar por qué un agente realizó una acción.

La primera fase se considera exitosa si ejecuta una tarea representativa de punta a punta con revisión y checkpoint humano, recupera una ejecución interrumpida sin repetir efectos, no expone secretos en la evidencia y publica benchmarks de calidad, latencia y VRAM para decidir el hardware final.

## Alcance inicial

Incluye inferencia local, tres roles de modelo, API autenticada de red privada, worktrees, pruebas, revisión, checkpoint humano, dashboard/CLI, trazas y memoria documental local. Excluye exposición pública, despliegue automático, acceso a datos reales sensibles, multi-repositorio simultáneo y la compra de hardware sin benchmark.

## Riesgos y preguntas abiertas

- [ASSUMPTION] La carga inicial es de pocos agentes concurrentes; definir usuarios simultáneos, SLA y presupuesto antes de adquirir la GPU.
- Confirmar las licencias de cada checkpoint y cuantización elegidos, no sólo las de la familia.
- Definir si el executor será exclusivamente local o incluirá Codex CLI como adaptador sujeto a política de datos y créditos.
- Validar compatibilidad y rendimiento del modelo elegido en el hardware final, especialmente contextos grandes y múltiples worktrees.
