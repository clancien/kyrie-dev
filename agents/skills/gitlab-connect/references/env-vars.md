# Variables `.env` para GitLab

## Requeridas

- `GITLAB_BASE_URL`: URL base de GitLab (ej: `https://gitlab.com` o `https://gitlab.miempresa.com`).
- `GITLAB_TOKEN`: Personal Access Token con permisos de lectura para API (`read_api` o equivalente).

## Opcional

- `GITLAB_PROJECT_ID`: ID numérico del proyecto por defecto para consultas de merge requests.

## Ejemplo

```dotenv
GITLAB_BASE_URL=https://gitlab.com
GITLAB_TOKEN=glpat_xxxxxxxxxxxxxxxxxxxx
GITLAB_PROJECT_ID=12345678
```
