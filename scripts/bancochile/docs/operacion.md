# Operación (Runbook)

## Prerrequisitos
```bash
cd /home/clancien/workspace/dev
./scripts/bancochile/setup_env.sh
source scripts/bancochile/.venv/bin/activate
```

Configura `.env`:
- `BANCHILE_RUT`
- `BANCHILE_PASSWORD`
- opcional: `BANCHILE_NOMBRE_CLIENTE`, `BANCHILE_CLASE_CUENTA`

## Ejecución recomendada
```bash
bash scripts/bancochile/run.sh
```

Comportamiento:
- Reutiliza cache de sesión si está vigente.
- Si no, abre login UI y renueva sesión.
- Ejecuta extracción API y deja salida consolidada.

## Modo servidor puro
```bash
bash scripts/bancochile/run_server.sh
```
Usar cuando ya existe `cache/session_storage_state.json` válido.

## Ver resultados
- `scripts/bancochile/output/all_api_server_latest.json`
- `scripts/bancochile/cache/all_api_server_latest.json`

## Web local
```bash
cd scripts/bancochile
docker compose up -d
```
Hosts:
```txt
127.0.0.1 bancochile.local
```
Abrir:
- `http://bancochile.local:8030`

## Errores comunes

### 1) `No existe ... cache/session_storage_state.json`
Causa: no hay sesión cacheada.
Acción: ejecutar `run.sh` (hará login UI) o correr `bancochile_login_ui.py` manualmente.

### 2) `devolvio no-JSON ... Inicia sesión ...`
Causa: sesión vencida/no válida en backend.
Acción: regenerar sesión UI y reintentar (`run.sh`).

### 3) `ModuleNotFoundError` (dotenv/requests)
Causa: dependencias faltantes en `.venv`.
Acción:
```bash
source scripts/bancochile/.venv/bin/activate
pip install -r scripts/bancochile/requirements.txt
```

### 4) Login UI finaliza en `sitiospublicos/personas`
Causa: login no completado realmente.
Acción: repetir login UI con Chromium y validar que luego `run.sh` obtenga JSON de API.

## Mantenimiento
- Renovar cache de sesión cuando expira.
- Verificar cambios de schema en `api_raw` antes de ajustar `derived`.
- Evitar commits de credenciales o cookies sensibles.

