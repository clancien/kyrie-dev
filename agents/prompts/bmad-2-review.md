# Fable o GPT-6.1 Sol
```
/bmad-review docs/specs/<feature>.md

- NO modifiques la spec ni el código.
- Output: docs/specs/<feature>.review.md, tabla | ID | Severidad (blocker/major/minor) | Sección | Hallazgo | Corrección |
- Veredicto final: LISTO / LISTO CON CAMBIOS / NO LISTO.
```

# Opus 5.5
```
/bmad-agent-architect

Aplica docs/specs/<feature>.review.md sobre docs/specs/<feature>.md.
- Blocker y major: aplicar todos. Si rechazas uno, justifica en una línea.
- Minor: aplicar solo si no agregan alcance.
- Mantén estructura y formato BMAD.
- Agrega al final un "Changelog de review" con IDs aplicados/rechazados.
```