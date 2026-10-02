# Sonnet 5.5
```
/bmad-build docs/specs/<feature>.md

Agente: /bmad-agent-dev

Reglas:
- Implementa story por story en el orden de la spec; un commit por story (conventional commits).
- Tests primero para cada criterio de aceptación.
- No agregues funcionalidad fuera de la spec.
- Si encuentras ambigüedad o la spec contradice el código: detente en esa story, regístralo en docs/specs/<feature>.blockers.md y continúa con la siguiente independiente.
- Antes de marcar una story como done: tests, lint y typecheck en verde.

Al terminar: estado por story (done / blocked) y comandos para verificar.
```     