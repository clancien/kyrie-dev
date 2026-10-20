# Santander personal

Módulo independiente de lectura bancaria. Puerto `8031`, configurable mediante `SANTANDER_PORT` (8030 se rechaza). Ejecutar desde cualquier directorio:

```sh
/path/scripts/santander/setup_env.sh
/path/scripts/santander/run.sh --desde 2026-08 --hasta 2026-10
/path/scripts/santander/run_server.sh --help
/path/scripts/santander/server.sh up
```

Abrir http://localhost:8031. Credenciales `SANTANDER_RUT` y `SANTANDER_PASSWORD` en `.env` privado del módulo. No versionar credenciales, cache, datos ni exportaciones. Proteger también `.env` con `chmod 600`.

La instalación descarga Chromium. Login mantiene Personas e iframe y permite intervención manual durante tres minutos. Tras el acceso visita automáticamente las pantallas de solo lectura para capturar productos, saldos y tarjeta por host. `run_server.sh` consulta solo con sesión existente. Sesión vencida requiere `run.sh`, sin reintentos automáticos de contraseña.

Verificación real realizada: acceso Personas/iframe con credenciales configuradas, titular contrastado contra respuesta bancaria, consultas HTTP independientes tras cerrar navegador, saldos corriente/vista, tarjeta CLP/USD y repetición de septiembre/octubre. Se reprodujo el truncamiento 50 frente a 31+20=51 y se confirmó unión conservadora. Códigos desconocidos se rechazan. No se promete profundidad histórica ilimitada.

Docker: configuración validada; la construcción inicial falló por error interno BuildKit («forwarding Ping: no such job»), conservando el servicio local. Un segundo intento con constructor legacy alcanzó descarga de Chromium y falló al exportar la capa por «no space left on device» en el almacenamiento de Docker Desktop. La persistencia y renovación en contenedor deben verificarse tras resolver ese bloqueo del entorno.

Historial SQLite por titular/producto/moneda/mes, decimales como strings, multiplicidad preservada y exportación acumulada atómica en `data/history.json`. Mes abierto siempre es snapshot. Mes previo solo se reutiliza después de consulta completa iniciada tras cierre en Chile. Un día de 50 filas o más es posiblemente truncado y no reemplaza la partición.

Operación y límites en [docs/operacion.md](docs/operacion.md) y [docs/arquitectura.md](docs/arquitectura.md).
