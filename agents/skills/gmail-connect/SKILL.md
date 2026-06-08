---
name: gmail-connect
description: "Conectar Gmail por API OAuth2 para leer correos y crear borradores usando credenciales en `.env`. Usar cuando se necesite consultar inbox por query, extraer metadatos de mensajes o generar drafts automáticos sin enviar."
---

# Gmail Connect

## Objetivo

Operar Gmail por API con OAuth2 para:

- Leer correos (`read`) con filtros de búsqueda.
- Crear borradores (`draft`) listos para revisión/envío manual.

## Variables `.env` requeridas

- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`

Opcionales:

- `GMAIL_REDIRECT_URI` (default: `http://localhost:8080`)
- `GMAIL_USER` (default: `me`)

## Comandos

```bash
# 1) Generar URL de consentimiento OAuth
python3 .agents/skills/gmail-connect/assets/gmail_oauth_helper.py --project-root "$PWD" auth-url

# 2) Intercambiar authorization code y obtener refresh token
python3 .agents/skills/gmail-connect/assets/gmail_oauth_helper.py --project-root "$PWD" exchange-code --code "<CODE>"

# 3) Leer correos
python3 .agents/skills/gmail-connect/assets/gmail_client.py --project-root "$PWD" read --query "from:example@company.com newer_than:30d" --max-results 20

# 4) Crear borrador
python3 .agents/skills/gmail-connect/assets/gmail_client.py --project-root "$PWD" draft \
  --to "user@company.com" \
  --subject "Seguimiento" \
  --body "Hola, te comparto el estado..."
```

## Salidas

- Lectura correos: `doc/gmail/messages_latest.json`
- Draft creado: `doc/gmail/draft_latest.json`

## Reglas

- No hardcodear secretos OAuth.
- Cargar credenciales solo desde `.env`.
- No imprimir tokens ni secretos en logs.

## API Reutilizable

- Cliente compartido: `.agents/skills/gmail-connect/assets/api.py`
- Clases principales: `GmailOAuthClient`, `GmailApiClient`
- Scripts del skill deben usar estas clases para OAuth y llamadas Gmail API.

### Contrato API (`assets/api.py`)

Constantes:
- `TOKEN_URL = https://oauth2.googleapis.com/token`
- `AUTH_URL = https://accounts.google.com/o/oauth2/v2/auth`
- `GMAIL_API_BASE = https://gmail.googleapis.com/gmail/v1/users`
- `SCOPES`:
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.compose`

Funciones utilitarias:
- `load_env_file(env_path: Path) -> dict[str, str]`
- `env_get(key, env_values, env_path, required=True) -> str`

OAuth:
- `GmailOAuthClient(client_id, client_secret, redirect_uri)`
- `GmailOAuthClient.from_project_root(project_root: Path) -> GmailOAuthClient`:
  - Requiere `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`.
  - `GMAIL_REDIRECT_URI` opcional (default `http://localhost:8080`).
- `exchange_code(code: str) -> dict`:
  - Intercambia authorization code por tokens (incluye `refresh_token` en flujo de consent).

API Gmail:
- `GmailApiClient(client_id, client_secret, refresh_token, user_id="me")`
- `GmailApiClient.from_project_root(project_root: Path) -> GmailApiClient`:
  - Requiere `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`.
  - `GMAIL_USER` opcional (default `me`).
- `get_access_token() -> str`: refresca token OAuth2.
- `list_messages(query: str, max_results: int) -> dict`
- `get_message_metadata(msg_id: str) -> dict`
- `create_draft(raw_message: str) -> dict`

Errores:
- `RuntimeError` si falta configuración o token response inválida.
- Propaga `requests.HTTPError` en errores Google API.

Ejemplo:
```python
from pathlib import Path
from api import GmailOAuthClient, GmailApiClient

oauth = GmailOAuthClient.from_project_root(Path("/ruta/proyecto"))
token_payload = oauth.exchange_code("<CODE>")

gmail = GmailApiClient.from_project_root(Path("/ruta/proyecto"))
messages = gmail.list_messages("newer_than:7d", 10)
```
