# Resumen Actual (Modular y Limpio)

## Estado final
La carpeta `scripts/bancochile` quedo simplificada al flujo estable y reutilizable:
- Login UI para crear/renovar sesion.
- Consumo API en modo servidor reutilizando sesion cacheada.

## Flujo operativo
1. Ejecutar `run.sh`.
2. `run.sh` intenta cache (`cache/session_storage_state.json`).
3. Si cache no sirve, ejecuta `bancochile_login_ui.py`.
4. Luego ejecuta `bancochile_server_api.py` para obtener saldos/movimientos/tarjetas.

## Modulos vigentes
- `bancochile_login.py`: funciones base de login Playwright.
- `bancochile_login_ui.py`: login CLI con UI.
- `bancochile_server_core.py`: logica API reusable.
- `bancochile_server_api.py`: wrapper CLI para `server_core`.
- `run.sh`: orquestador principal.
- `run_server.sh`: modo servidor puro.
- `setup_env.sh`: bootstrap del entorno.

## Limpieza aplicada
Se eliminaron scripts legacy/no usados:
- flujos API duplicados y experimentales
- login backend sin cache/no UI (inestable por anti-bot)
- scripts de debug obsoletos
- script UI legacy por scraping de tabla
- configs y logs asociados a esos flujos
- `__pycache__`

## Resultado
Estructura mas mantenible, menos duplicacion, y componentes reutilizables para evolucion futura.
