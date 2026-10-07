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

## Cartola histórica por mes
La API acepta un intervalo de fechas. Para evitar mezclar períodos y respetar su
paginación, el CLI consulta cada mes del rango de forma independiente:

```bash
source scripts/bancochile/.venv/bin/activate
python scripts/bancochile/bancochile_server_api.py --desde 2026-01 --hasta 2026-01
python scripts/bancochile/bancochile_server_api.py \
  --desde 2025-01 --hasta 2025-12
bash scripts/bancochile/run_server.sh --desde 2026-01 --hasta 2026-01
```

`--desde` y `--hasta` son inclusivos y deben tener formato `YYYY-MM`.
Sin argumentos se incluyen tres meses terminando en el actual. La base acumulativa
es `data/cartola.sqlite3`: los meses anteriores completos no vuelven a descargarse,
el mes actual se actualiza y los JSON exportan todo el histórico almacenado.
Para respaldo, copia la base cuando el script no esté ejecutándose.

## Ver resultados
- `scripts/bancochile/output/all_api_server_latest.json`
- `scripts/bancochile/cache/all_api_server_latest.json`

## Web local

### Iniciar, detener y consultar el servidor

Desde la raíz del proyecto:

```bash
# Iniciar Python local (modo predeterminado)
bash scripts/bancochile/server.sh up

# Construir la imagen e iniciar Docker Compose
bash scripts/bancochile/server.sh up docker

# Detener ambos modos, conservando la base y la sesión
bash scripts/bancochile/server.sh down

# Detener solo un modo
bash scripts/bancochile/server.sh down local
bash scripts/bancochile/server.sh down docker

# Reiniciar
bash scripts/bancochile/server.sh restart local
bash scripts/bancochile/server.sh restart docker

# Consultar estado y últimos 100 registros
bash scripts/bancochile/server.sh status
bash scripts/bancochile/server.sh logs local
bash scripts/bancochile/server.sh logs docker

# Mostrar ayuda
bash scripts/bancochile/server.sh --help
```

`up`, `restart` y `logs` usan el modo `local` si no se especifica otro.
`down` sin modo detiene tanto el servidor local como Docker; también admite `all`.
No necesitas activar `.venv` para usar el script: utiliza el Python de esa carpeta.
El modo local requiere haber ejecutado `setup_env.sh`; el modo Docker requiere
Docker Compose disponible y espacio para construir la imagen con Chromium.
El login visible requiere un escritorio Linux con `DISPLAY` y `XAUTHORITY`.

El script detiene el otro modo antes de ocupar el puerto 8030. Al iniciar Docker,
construye primero la imagen: si la construcción falla, mantiene el servidor local.
`down docker` ejecuta `docker compose down` sin borrar volúmenes ni datos locales.
Los comandos de control simultáneos se bloquean con `flock` (util-linux).

En modo local usa `bancochile-panel.service` de systemd de usuario si está disponible;
si no, ejecuta en segundo plano con `nohup` y guarda PID/registros en
`scripts/bancochile/cache/web-server/`. La unidad systemd es temporal; después de
reiniciar el equipo, ejecuta nuevamente `server.sh up`.
El script resuelve sus archivos desde su propia ubicación, por lo que también
puedes invocarlo con una ruta absoluta desde otro directorio.

Abre `http://localhost:8030`. Para usar `http://bancochile.local:8030`, agrega a
`/etc/hosts`:

```txt
127.0.0.1 bancochile.local
```

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
