# Arquitectura

## Objetivo
Obtener datos bancarios (productos, cartola, tarjetas) con un flujo robusto:
- login interactivo con UI para crear sesión válida
- consumo posterior en modo server reutilizando sesión cacheada

## Componentes
- `bancochile_login.py`
  - Librería de login con Playwright.
  - Contiene funciones reutilizables de autenticación y verificación de sesión.

- `bancochile_login_ui.py`
  - CLI de login interactivo.
  - Genera `cache/session_storage_state.json`.

- `bancochile_server_core.py`
  - Núcleo reusable sin Playwright.
  - Carga cookies desde storage state.
  - Consulta endpoints API y arma payload consolidado.

- `bancochile_server_api.py`
  - Wrapper CLI del core.
  - Expone flags (`--account-number`, `--max-pages`, etc.).

- `run.sh`
  - Orquestador principal.
  - Si cache es válida, ejecuta server directo.
  - Si cache no sirve, hace login UI y reintenta.

- `run_server.sh`
  - Ejecución no interactiva (solo cache).

- `web/`
  - Sitio estático para visualizar resultados (`all_api_server_latest.json`).

## Flujo de datos
1. `run.sh` valida cache.
2. Si cache inválida, ejecuta `bancochile_login_ui.py`.
3. `bancochile_server_api.py` llama `run_all_api()` del core.
4. Core consulta:
   - `selectorproductos/selectorProductos/obtenerProductos?incluirTarjetas=false`
   - `bff-pper-prd-cta-movimientos/movimientos/getCartola` (por cuenta)
   - `tarjetas/widget/informacion-tarjetas`
5. Guarda salida en:
   - `output/all_api_server_latest.json`
   - `cache/all_api_server_latest.json`

## Principios de diseño
- Modularidad: lógica de negocio en core, CLI delgada.
- Reutilización: sesión cacheada para evitar login repetitivo.
- Trazabilidad: respuesta API raw siempre preservada en `api_raw`.
- Seguridad: credenciales por entorno (`.env`), no hardcodeadas.

## Estructura de salida (alto nivel)
- `api_raw.*`: respuestas tal cual de API.
- `derived.*`: agregaciones locales para consumo (movimientos por cuenta, totales).

