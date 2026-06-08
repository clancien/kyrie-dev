---
name: trello-connect
description: "Conectar y operar Trello por API usando credenciales en `.env` para validar acceso, listar boards/listas y consultar tarjetas de forma reproducible. No persiste archivos en el workspace; solo imprime resultados por stdout. Usar cuando se necesite conectividad pura a Trello."
---

# Trello

## Flujo

1. Definir credenciales Trello en `.env`.
2. Cargar variables de entorno en la sesión shell.
3. Validar autenticación con `ping`.
4. Listar boards/listas y consultar tarjetas según necesidad.
5. Entregar JSON por stdout para que otros skills consuman el resultado.

## Variables `.env`

Ver detalle en `references/env-vars.md`.

Mínimas requeridas:
- `TRELLO_KEY`
- `TRELLO_TOKEN`

Opcionales:
- `TRELLO_BOARD_ID`
- `TRELLO_LIST_ID`

## Comandos

```bash
# Cargar variables de .env en la shell actual
set -a; source .env; set +a

# Validar token y conectividad
python3 .agents/skills/trello-connect/assets/trello_fetch.py ping

# Listar boards abiertos
python3 .agents/skills/trello-connect/assets/trello_fetch.py boards

# Listar listas de un board explícito
python3 .agents/skills/trello-connect/assets/trello_fetch.py lists --board-id <BOARD_ID>

# Listar listas usando TRELLO_BOARD_ID
python3 .agents/skills/trello-connect/assets/trello_fetch.py lists

# Listar tarjetas abiertas de una lista explícita
python3 .agents/skills/trello-connect/assets/trello_fetch.py cards --list-id <LIST_ID>

# Listar tarjetas usando TRELLO_LIST_ID
python3 .agents/skills/trello-connect/assets/trello_fetch.py cards

# Detalle completo de una tarjeta (adjuntos, miembros, comentarios)
python3 .agents/skills/trello-connect/assets/trello_fetch.py card --card-id <CARD_ID>
```

## Reglas

- No escribir artefactos en `doc/` ni en otras rutas del workspace.
- No hardcodear key/token/ids en scripts.
- Priorizar lectura de variables de entorno y permitir override por argumentos.
- Ante error HTTP, propagar código y mensaje exacto de API para trazabilidad.

## API Reutilizable

- Cliente compartido: `.agents/skills/trello-connect/assets/api.py`
- Clase principal: `TrelloClient`
- Todo script consumidor debe usar este cliente para llamadas Trello API (evitar `requests` directo duplicado).

### Contrato API (`assets/api.py`)

Funciones utilitarias:
- `load_env_file(env_path: Path) -> dict[str, str]`
- `env_get(key, env_values, env_path, required=True) -> str`

Clase:
- `TrelloClient(key: str, token: str, base_url="https://api.trello.com/1")`
- `TrelloClient.from_project_root(project_root: Path) -> TrelloClient`:
  - Requiere `TRELLO_KEY`, `TRELLO_TOKEN`.
- `get(path: str, **params) -> dict | list`:
  - Agrega automáticamente `key` y `token` al query string.
- `download_card_attachment(card_id, attachment_id, filename) -> requests.Response`:
  - Descarga binaria de adjuntos vía `trello.com/1/cards/.../download/...`.

Rutas:
- `path` se interpreta relativo a `https://api.trello.com/1`.
- Ejemplos: `members/me/boards`, `boards/<id>/lists`, `cards/<id>`.

Errores:
- Propaga `requests.HTTPError` con detalle del servicio.

Ejemplo:
```python
from pathlib import Path
from api import TrelloClient

client = TrelloClient.from_project_root(Path("/ruta/proyecto"))
boards = client.get("members/me/boards", filter="open")
cards = client.get("lists/<LIST_ID>/cards", filter="open")
resp = client.download_card_attachment("<CARD_ID>", "<ATT_ID>", "archivo.pdf")
```
