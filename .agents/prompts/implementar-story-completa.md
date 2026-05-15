---
name: implementar-story-completa
description: Ejecuta el ciclo BMad completo para una historia.
variables:
  story_key: "Identificador de historia, ej: 1-4-registrar-decisiones-operativas-de-la-linea-base"
---

Ejecuta de forma secuencial y autónoma, usando subagentes cuando aporte, el ciclo completo BMad para la historia `{{story}}`:

1. `[$bmad-create-story] crea la siguiente historia: {{story}}`
2. `[$bmad-create-story] valida la historia creada: {{story}}`
3. `[$bmad-dev-story] implementa la historia validada: {{story}}`
4. `[$bmad-code-review] revisa el cambio de la historia: {{story}}`


Repite implementación + code review las veces necesarias hasta que el review quede sin hallazgos accionables. No me pidas supervisión salvo bloqueo real o decisión que no pueda inferirse del repo. Respeta las instrucciones de AGENTS.md: no ejecutes suite automatizada salvo pedido explícito, usa validaciones puntuales/reproducibles y mantén los cambios enfocados.

Actualiza doc/implementation-artifacts/sprint-prompt.md en los prompts ejecutados.

Termina con resumen muy conciso de lo realizado,documentado y/o implementado; y con los pendientes.
