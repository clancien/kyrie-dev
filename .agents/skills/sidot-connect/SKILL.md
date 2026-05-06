---
name: sidot-connect
description: "Navegar SIDOT vía sesión autenticada para obtener datos operativos: login, búsqueda de donante por código SIDOT, consulta de extracciones por donante_id y utilidades de catálogo de hospitales."
---

# SIDOT Web Navigator

## Objetivo

Obtener datos desde SIDOT de forma reproducible usando scripts:

- Login autenticado y obtención de cookie de sesión.
- Búsqueda de donante por código SIDOT.
- Búsqueda de extracciones por `donante_id` con resolución de `trasplante_id`.
- Búsqueda de usuarios en SIDOT por texto libre.
- Validación de login para un usuario SIDOT específico sin persistir ni imprimir la clave.
- Exportación de hospitales SIDOT.

## Variables `.env` requeridas

- `SIDOT_USER`
- `SIDOT_PWD`
- `SIDOT_URL` (ej: `https://sidot.minsal.cl`)

## Comandos

```bash
# 1) Login y persistencia de sesión
python3 .agents/skills/sidot-connect/assets/sidot_login.py --project-root "$PWD"

# 2) Buscar donante por código SIDOT
python3 .agents/skills/sidot-connect/assets/sidot_search_donante.py --project-root "$PWD" --codigo-sidot 2025094935

# 3) Buscar extracciones por donante_id
python3 .agents/skills/sidot-connect/assets/sidot_search_extracciones.py --project-root "$PWD" --donante-id 5714

# 4) Exportar catálogo de hospitales
python3 .agents/skills/sidot-connect/assets/fetch_hospitales.py --project-root "$PWD"
python3 .agents/skills/sidot-connect/assets/fetch_hospitales.py --project-root "$PWD" --stdout

# 5) Buscar usuarios en SIDOT
python3 .agents/skills/sidot-connect/assets/sidot_search_usuarios.py --project-root "$PWD" --query "cyrille"

# 6) Validar login de un usuario SIDOT sin imprimir la clave
printf '%s' "$CLAVE_TEMPORAL" | python3 .agents/skills/sidot-connect/assets/sidot_verify_login.py --project-root "$PWD" --username "Cfulgeris" --password-stdin --stdout

# Salida esperada explícita:
# $PROJECT_ROOT/doc/.sidot/hospitales.json
```

## Salidas

- Sesión/cookies: `doc/.sidot/session/cookies.json`
- Última respuesta login: `doc/.sidot/session/login_response.html`
- Búsqueda donante:
  - HTML: `doc/.sidot/donante_search/donante_<codigo>.html`
  - JSON parseado: `doc/.sidot/donante_search/donante_<codigo>.json`
- Extracciones:
  - HTML: `doc/.sidot/extracciones/extracciones_donante_<id>.html`
  - JSON parseado: `doc/.sidot/extracciones/extracciones_donante_<id>.json`
  - HTML detalle por extraíble (cuando aplica fallback): `doc/.sidot/extracciones/extraible_<donante_id>_<extraible_id>.html`
- Hospitales:
  - JSON: `$PROJECT_ROOT/doc/.sidot/hospitales.json` (ejemplo: `doc/.sidot/hospitales.json`)
- Usuarios:
  - HTML: `doc/.sidot/usuarios/usuarios_<query>.html`
  - JSON parseado: `doc/.sidot/usuarios/usuarios_<query>.json`
- Validación de clave:
  - No persiste archivos ni imprime la clave.
  - Salida segura por consola: usuario, `authenticated`, `auth_url`, `status_code` y timestamp.

## Reglas de trabajo

- Nunca hardcodear usuario o contraseña.
- Cargar credenciales solo desde `.env` del `--project-root`.
- Para validar claves temporales, preferir `--password-stdin`; no registrar claves en consola, bitácoras ni archivos.
- Mantener outputs bajo `doc/.sidot/`.
- Si falla login, no intentar scrapear páginas de negocio.
- Resolución de IDs:
  - `sidot_search_donante.py` detecta `donante_id` desde rutas `/donante/identificacion/<id>` y equivalentes.
  - `sidot_search_extracciones.py` primero busca `trasplante_id` en el listado y, si no aparece, abre cada detalle `/donante/extraccion/extraible/<donante>/<extraible>` para detectar enlaces `/trasplante/<id>`.

## API Reutilizable

- Cliente compartido: `.agents/skills/sidot-connect/assets/api.py`
- Clase principal: `SidotClient`
- Scripts del skill deben autenticarse y navegar SIDOT a través de este cliente.
- Para probar credenciales de usuarios finales, usar `assets/sidot_verify_login.py` con `SidotClient(base_url, username, password)` y no `SidotClient.from_project_root`, ya que este último usa las credenciales administrativas del `.env`.

### Contrato API (`assets/api.py`)

Funciones utilitarias:
- `load_env_file(env_path: Path) -> dict[str, str]`
- `env_get(key, env_values, env_path, required=True) -> str`
- `extract_csrf_token(html_text: str) -> str`: extrae `__csrftoken` desde `/login`.

Clase:
- `SidotClient(base_url: str, username: str, password: str)`
- `SidotClient.from_project_root(project_root: Path) -> SidotClient`:
  - Requiere `SIDOT_URL`, `SIDOT_USER`, `SIDOT_PWD`.
- `login() -> dict`:
  - Flujo: `GET /login` -> extrae CSRF -> `POST /logon`.
  - Devuelve metadata de autenticación (`auth_url`, `status_code`, `authenticated`, etc.).
- `ensure_login() -> None`: ejecuta login si no hay sesión autenticada.
- `get(path_or_url: str, **kwargs) -> requests.Response`:
  - Si recibe URL absoluta, la usa directamente.
  - Si recibe ruta relativa, concatena con `SIDOT_URL`.
  - Usa sesión autenticada (`requests.Session`) del cliente.

Comportamiento de sesión:
- `SidotClient.session` queda disponible para `POST`/`GET` avanzados cuando se necesita mantener cookies.
- Headers browser-like por defecto (`User-Agent`, `Accept`, `Accept-Language`).

Errores:
- `RuntimeError` si falla CSRF o autenticación.
- Propaga `requests.HTTPError` en respuestas no 2xx.

Ejemplo:
```python
from pathlib import Path
from api import SidotClient

client = SidotClient.from_project_root(Path("/ruta/proyecto"))
client.login()
donantes = client.get("/donante/?busqueda=&busqueda.codigoSidot=2025094935")
usuarios = client.get("/pref/usuario/?busqueda.query=juan")
```
