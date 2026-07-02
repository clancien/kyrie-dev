---
name: gitlab-connect
description: "Conectar y operar GitLab por API usando credenciales en `.env` para validar acceso, listar proyectos, consultar merge requests y administrar milestones de proyecto/issue de forma reproducible. Usar cuando se necesite trabajar con repositorios, MRs, issues o metadata de GitLab desde terminal/script en este workspace."
---

# GitLab

## Flujo

1. Definir credenciales GitLab en `.env`.
2. Cargar variables de entorno en la sesión shell.
3. Validar autenticación con `ping`.
4. Listar proyectos disponibles para confirmar alcance de permisos.
5. Consultar merge requests, issues o milestones del proyecto objetivo.

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
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py ping

# Listar proyectos a los que tiene acceso el token
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py projects --per-page 50

# Buscar proyecto por texto
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py projects --search sidot

# Listar MRs abiertas de un proyecto
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py mrs --project-id $GITLAB_PROJECT_ID --state opened

# Listar MRs de un proyecto explícito
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py mrs --project-id $GITLAB_PROJECT_ID --state all

# Listar Issues (tickets) de un proyecto
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py issues --project-id $GITLAB_PROJECT_ID --state opened

# Listar Issues de un proyecto explícito
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py issues --project-id $GITLAB_PROJECT_ID --state all

# Listar milestones activos del proyecto
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py milestones --project-id $GITLAB_PROJECT_ID --state active

# Buscar milestone por título exacto
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py milestones --project-id $GITLAB_PROJECT_ID --title "Mantenciones Octubre 2025"

# Crear milestone mensual
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py milestone-create --project-id $GITLAB_PROJECT_ID --title "Mantenciones Octubre 2025"

# Asignar milestone a un issue
python3 .agents/skills/gitlab-connect/scripts/gitlab_fetch.py milestone-assign --project-id $GITLAB_PROJECT_ID --issue-iid 123 --milestone-id 456
```

## Reglas

- No hardcodear tokens ni URLs de instancia en scripts.
- Priorizar lectura desde variables de entorno.
- Ante error HTTP, registrar mensaje exacto de API para trazabilidad.
- Usar este skill como base y extender scripts para endpoints adicionales (issues, milestones, pipelines, releases) cuando sea necesario.

## API Reutilizable

- Cliente compartido: `.agents/skills/gitlab-connect/assets/api.py`
- Clase principal: `GitLabClient`
- Todo script consumidor debe usar este cliente para llamadas GitLab API (evitar `requests/urllib` directo duplicado).

### Contrato API (`assets/api.py`)

Funciones utilitarias:
- `load_env_file(env_path: Path) -> dict[str, str]`: carga pares `KEY=VALUE` desde `.env`.
- `env_get(key, env_values, env_path, required=True) -> str`: obtiene variable desde `.env`/entorno; si falta y `required=True`, lanza `RuntimeError`.

Clase:
- `GitLabClient(base_url: str, token: str)`
- `GitLabClient.from_project_root(project_root: Path) -> GitLabClient`:
  - Requiere `GITLAB_BASE_URL`, `GITLAB_TOKEN`.
- `get(path: str, query: dict | None = None) -> dict | list`
- `post(path: str, form: dict | None = None) -> dict | list`
- `put(path: str, form: dict | None = None) -> dict | list`
- `list_project_milestones(project_id: str, query: dict | None = None) -> dict | list`
- `find_project_milestone(project_id: str, title: str) -> dict | None`
- `create_project_milestone(project_id: str, title: str, description: str | None = None, due_date: str | None = None, start_date: str | None = None) -> dict`
- `assign_issue_milestone(project_id: str, issue_iid: str, milestone_id: str | int) -> dict`
- `request(method, path, query=None, form=None) -> dict | list`:
  - Usa `PRIVATE-TOKEN`.
  - Codifica `form` como `application/x-www-form-urlencoded`.

Rutas:
- `path` se interpreta relativo a `/api/v4` (ej: `/user`, `/projects/.../issues`).

Errores:
- `RuntimeError("GitLab API error <code>: <detail>")` para errores HTTP.
- `RuntimeError("Cannot reach GitLab: ...")` para conectividad.

Ejemplo:
```python
from pathlib import Path
from api import GitLabClient

client = GitLabClient.from_project_root(Path("/ruta/proyecto"))
me = client.get("/user")
issues = client.get("/projects/123/issues", query={"state": "opened"})
note = client.post("/projects/123/issues/10/notes", form={"body": "Comentario"})
milestone = client.find_project_milestone("123", "Mantenciones Octubre 2025")
```
