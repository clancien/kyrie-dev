---
name: gitlab
description: "Conectar y operar GitLab por API usando credenciales en `.env` para validar acceso, listar proyectos y consultar merge requests de forma reproducible. Usar cuando se necesite trabajar con repositorios, MRs o metadata de GitLab desde terminal/script en este workspace."
---

# GitLab

## Flujo

1. Definir credenciales GitLab en `.env`.
2. Cargar variables de entorno en la sesión shell.
3. Validar autenticación con `ping`.
4. Listar proyectos disponibles para confirmar alcance de permisos.
5. Consultar merge requests del proyecto objetivo.

## Variables `.env`

Ver detalle en `references/env-vars.md`.

Mínimas requeridas:
- `GITLAB_BASE_URL`
- `GITLAB_TOKEN`

Opcional:
- `GITLAB_PROJECT_ID`

## Comandos

```bash
# Cargar variables de .env en la shell actual
set -a; source .env; set +a

# Validar token
python3 .agents/skills/gitlab/scripts/gitlab_fetch.py ping

# Listar proyectos a los que tiene acceso el token
python3 .agents/skills/gitlab/scripts/gitlab_fetch.py projects --per-page 50

# Buscar proyecto por texto
python3 .agents/skills/gitlab/scripts/gitlab_fetch.py projects --search sidot

# Listar MRs abiertas de un proyecto (usa GITLAB_PROJECT_ID si existe)
python3 .agents/skills/gitlab/scripts/gitlab_fetch.py mrs --state opened

# Listar MRs de un proyecto explícito
python3 .agents/skills/gitlab/scripts/gitlab_fetch.py mrs --project-id 12345678 --state all
```

## Reglas

- No hardcodear tokens ni URLs de instancia en scripts.
- Priorizar lectura desde variables de entorno.
- Ante error HTTP, registrar mensaje exacto de API para trazabilidad.
- Usar este skill como base y extender scripts para endpoints adicionales (issues, pipelines, releases) cuando sea necesario.
