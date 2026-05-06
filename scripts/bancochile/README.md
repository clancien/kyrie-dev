# BancoChile Scripts

Automatización modular para obtener datos de Banco de Chile usando:
1. Login UI (Playwright) para generar sesión válida.
2. Consumo API en modo server reutilizando `session_storage_state.json`.

## Docs
- Arquitectura: `docs/arquitectura.md`
- Operación (runbook): `docs/operacion.md`
- Resumen histórico: `RESUMEN.md`

## Estructura principal
- `bancochile_login.py`: utilidades de login Playwright.
- `bancochile_login_ui.py`: CLI de login interactivo.
- `bancochile_server_core.py`: núcleo reusable para APIs.
- `bancochile_server_api.py`: wrapper CLI del core.
- `run.sh`: orquestador principal (cache -> UI fallback -> API).
- `run_server.sh`: modo server puro (solo cache).
- `web/`: mini sitio para visualizar resultados.
- `docker-compose.yml`: servicio liviano de la web.

## Setup rápido
```bash
cd /home/clancien/workspace/dev
./scripts/bancochile/setup_env.sh
source scripts/bancochile/.venv/bin/activate
```

## Variables de entorno
Configura `scripts/bancochile/.env`:
- `BANCHILE_RUT`
- `BANCHILE_PASSWORD`
- opcional: `BANCHILE_NOMBRE_CLIENTE`, `BANCHILE_CLASE_CUENTA`

## Ejecución
### Flujo recomendado (auto-recuperable)
```bash
bash scripts/bancochile/run.sh
```

### Solo server (sin abrir UI)
```bash
bash scripts/bancochile/run_server.sh
```

### Renovar sesión UI manualmente
```bash
source scripts/bancochile/.venv/bin/activate
python scripts/bancochile/bancochile_login_ui.py --browser chromium
```

## Datos de salida
- Cache:
  - `cache/session_storage_state.json`
  - `cache/all_api_server_latest.json`
- Output:
  - `output/all_api_server_latest.json`

## Web local con Docker
```bash
cd scripts/bancochile
docker compose up -d
```

En `/etc/hosts`:
```txt
127.0.0.1 bancochile.local
```

Abrir:
- `http://bancochile.local:8030`

## Nota
Login 100% backend sin UI no es estable por controles anti-automatización.
