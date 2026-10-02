# Opus 5.5
```
/bmad-spec

Feature: <nombre corto>
Objetivo de negocio: <qué problema resuelve y para quién>

Requerimientos:
- <req 1>
- <req 2>

Restricciones:
- Stack: <ej. Next.js 15, Postgres, Prisma>
- Integraciones: <APIs, auth, etc.>
- No funcionales: <perf, seguridad, i18n>

Agentes:
- /bmad-agent-analyst: clarifica requerimientos y edge cases antes de redactar.
- /bmad-agent-architect: modelo de datos, contratos de API, decisiones técnicas con trade-off.
- /bmad-agent-ux: solo si hay UI; flujos y estados (vacío, error, carga).

Reglas:
- Haz todas tus preguntas en un solo bloque antes de escribir la spec.
- Marca cada supuesto como [SUPUESTO].
- Criterios de aceptación en Given/When/Then, testeables.
- Sección "Fuera de alcance" explícita.
- Divide en stories implementables de forma independiente, con orden y dependencias.

Output: docs/specs/<feature>.md
```