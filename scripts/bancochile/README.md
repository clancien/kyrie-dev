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

### Cartola histórica por meses
```bash
# Un mes; cada mes admite la paginación indicada.
python scripts/bancochile/bancochile_server_api.py --desde 2026-01 --hasta 2026-01

# Rango inclusivo, consultado mes a mes.
python scripts/bancochile/bancochile_server_api.py \
  --desde 2025-01 --hasta 2025-12

# Los lanzadores también reenvían estos argumentos.
bash scripts/bancochile/run.sh --desde 2026-01 --hasta 2026-01
```

Sin fechas se consultan el mes actual y los dos anteriores. `--hasta` por defecto
es el mes actual; si solo indicas `--hasta`, `--desde` será dos meses antes.
Se recorren todas las páginas hasta la señal de fin del banco. Los meses completos
anteriores se reutilizan desde `data/cartola.sqlite3`; el mes actual se vuelve a
consultar para incorporar nuevos movimientos. Cada mes se guarda en una transacción
independiente, incluidos meses vacíos. Una descarga fallida se reintenta la próxima vez.
Los JSON de `output/` muestran todo el historial acumulado, aunque la descarga
solicite un rango menor. `--database` permite elegir otra base SQLite.
Los resultados anteriores a esta base se conservan hasta la siguiente exportación,
pero no se importan como meses completos: pueden provenir de descargas truncadas.

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

### Control del servidor (desde cualquier directorio)
```bash
# Iniciar Python local (modo predeterminado)
bash scripts/bancochile/server.sh up

# Construir e iniciar Docker Compose
bash scripts/bancochile/server.sh up docker

# Detener ambos, sin borrar datos ni sesión
bash scripts/bancochile/server.sh down

# Otros comandos
bash scripts/bancochile/server.sh down local
bash scripts/bancochile/server.sh down docker
bash scripts/bancochile/server.sh restart local
bash scripts/bancochile/server.sh status
bash scripts/bancochile/server.sh logs local
bash scripts/bancochile/server.sh logs docker
```

El script usa rutas relativas a su ubicación. Si tienes systemd de usuario,
administra `bancochile-panel.service`; de lo contrario usa `nohup` y guarda PID/log
en `cache/web-server/`. En modo Docker construye la imagen antes de detener el
servidor local, para conservar el panel si falla la construcción.

```bash
cd scripts/bancochile
docker compose up -d --build
```

En `/etc/hosts`:
```txt
127.0.0.1 bancochile.local
```

Abrir:
- `http://bancochile.local:8030`

## Nota
Login 100% backend sin UI no es estable por controles anti-automatización.

## Actualizar desde el panel
El botón **Actualizar** consulta desde el último mes con movimientos en SQLite,
incluido ese mes, hasta el actual. Si la base está vacía, consulta tres meses.
Comprueba la sesión guardada; si venció o no existe, abre Chromium, espera el login
y después descarga todas las páginas. Muestra avance, resultado y vuelve a cargar
el historial del panel. No inicia dos actualizaciones web a la vez.

El servidor Python sustituye a Nginx. Docker conserva datos/sesión en los volúmenes
locales y publica `http://localhost:8030`. El login visible requiere el escritorio
Linux con `DISPLAY`, `/tmp/.X11-unix` y `XAUTHORITY` (se montan en Compose).
Para ejecutar sin Docker usando el entorno local:

```bash
source scripts/bancochile/.venv/bin/activate
python scripts/bancochile/bancochile_web_server.py
```

Solo un servidor puede usar el puerto 8030: detén el servicio local antes de
volver a levantar Docker. En la sesión de desarrollo actual se ejecuta como
`bancochile-panel.service` de systemd de usuario; se detiene con
`systemctl --user stop bancochile-panel.service`. La unidad es temporal;
después de reiniciar el equipo usa el comando Python anterior o Docker Compose.
