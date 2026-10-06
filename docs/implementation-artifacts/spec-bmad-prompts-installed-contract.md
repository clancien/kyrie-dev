---
title: 'Actualizar las recomendaciones de prompts para el contrato BMad instalado'
type: 'chore'
created: '2026-09-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `agents/bmad/custom/prompts.md` recomienda campos, placeholders y selección de modelos que no corresponden al contrato de BMad 6.12.0 instalado.

**Approach:** Reescribir la guía para distinguir capas de revisión compatibles de prompts que requieren otro workflow, usar las entradas reales y documentar cómo configurar modelos ligeros en el runtime antes de ejecutar BMad.

</frozen-after-approval>

## Implementation Notes

- Verificada la instalación BMAD-METHOD 6.12.0 en `_bmad/_config/manifest.yaml`.
- Alineada la guía con `bmad-build`: `review_layers` usa `{diff_file}` y
  `{claims_file}`; las capas one-shot inspeccionan el worktree.
- Se conservó el uso de modelos ligeros mediante la configuración de sesión de
  Codex, usando Terra para revisiones extensas y respetando el requisito de BMad
  de igual capacidad entre sesión y revisores.
- Se separaron los prompts que producen parches, triage o extracción de las capas
  de hallazgos, porque la instalación no consume esas salidas desde una review
  layer.

## Review Triage Log

- `patch` — La guía podía sugerir que editarla activaba una customización; se
  aclaró que sólo `_bmad/custom/bmad-build.toml` se resuelve automáticamente.
- `patch` — Se precisó que Terra es el modelo ligero para revisión extensa y que
  `codex -m gpt-5.6-terra` debe iniciar también la sesión principal.
- `patch` — Se distinguió la configuración de runtime de Codex de la
  customización de BMad y se añadió su comprobación en el cliente.
- `patch` — Se reemplazó la referencia ambigua a hooks por los cuatro campos
  reales expuestos por ATDD y Sprint Planning.
- `patch` — La variante one-shot ya no presupone un diff inyectado; usa el
  worktree y `git diff` sólo cuando Git está disponible.
