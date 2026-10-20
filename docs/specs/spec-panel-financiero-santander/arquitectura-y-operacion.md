# Arquitectura y operación

## Referencia y separación

La referencia es `scripts/bancochile/`: Python con Playwright para login, requests para consultas autenticadas, SQLite para historial y frontend HTML/CSS/JS servido por Python; lanzadores Bash y Docker Compose. Reutilizar el patrón y la experiencia, adaptando contratos y límites Santander. No crear una abstracción multibanco ni depender en ejecución de los módulos del panel existente.

El desarrollo futuro reside en `scripts/santander/`, incluyendo login reutilizable, CLI de login, núcleo de extracción/normalización/persistencia, CLI de consultas, servidor web, `web/`, requisitos, lanzadores, Docker y documentación. Separar extracción de presentación y mantener la CLI delgada. El `.env` existente contiene `SANTANDER_RUT` y `SANTANDER_PASSWORD`; leerlo desde la carpeta del módulo sin imprimir sus valores.

## Contrato de datos local

- Productos: clave estable de banco/titular/contrato/tipo/moneda; etiqueta, máscara y saldos/cupos con su moneda. Tarjetas multimoneda conservan identidad de tarjeta y líneas separadas.
- Movimientos: producto, moneda, fecha contable, fecha de operación, hora disponible, descripción, tipo cargo/abono, importe decimal exacto, saldo disponible por movimiento e identificador bancario si existe. Campos ausentes permanecen nulos; un código desconocido no se transforma silenciosamente en cargo, abono o cero.
- Mantener metadatos de fuente, cobertura solicitada, inicio de la consulta y completitud del snapshot; registrar por separado si la partición cumple el cierre reutilizable. Evaluar el inicio y el cierre mensual en `America/Santiago`. Respuestas bancarias útiles quedan en almacenamiento privado para diagnóstico sin encabezados de autenticación. La web recibe solo proyecciones normalizadas necesarias para el panel.
- Identidad y deduplicación deben verificarse por recurso. No borrar dos movimientos legítimos por compartir fecha, descripción e importe. Sustituir la partición completa cuenta/mes al refrescarla evita duplicación entre ejecuciones. No deduplicar cuentas diferentes por `movementNumber`.

SQLite mantiene particiones por titular/cuenta/moneda/mes con transacción independiente. Solo se sustituye una partición tras reunir y validar todas las hojas de consulta. Error de una hoja revierte esa partición y preserva su versión anterior; otros meses ya confirmados sobreviven. Un mes realmente vacío se registra solo tras una respuesta exitosa con cobertura demostrada. El commit de un snapshot del mes abierto no habilita su reutilización futura. El cierre reutilizable se registra atómicamente con la partición solo si una consulta de todo el mes iniciada después de su cierre en `America/Santiago` reúne todas las hojas válidas. Si falla esa consulta final, conservar el snapshot anterior, mantener el mes pendiente de cierre y no habilitar reutilización.

Exportar JSON del historial acumulado completo, aunque la ejecución solicite un rango menor. Publicar la exportación de manera atómica para que el lector nunca vea JSON incompleto. Mantener fecha y resultado de la última consulta por recurso; un saldo previo tras un error aparece como previo, no como actualizado.

## Fechas y actualización

CLI admite `--desde YYYY-MM`, `--hasta YYYY-MM`, cuenta opcional y ruta de base opcional siguiendo el patrón Banco de Chile. Intervalo inclusivo de meses. Sin fechas: mes actual y dos anteriores en `America/Santiago`; con solo `--hasta`: los tres meses terminando ahí; con solo `--desde`: hasta el mes actual. Rechazar formato inválido y rango invertido antes de consultar.

Cada mes se traduce a primer y último día inclusivos para Santander. No copiar la conversión UTC ni el fin exclusivo de Banco de Chile. El adaptador debe respetar la partición descrita en integración.

Solo se reutilizan meses anteriores con cierre reutilizable registrado: consulta completa de todo el mes iniciada después de su cierre en `America/Santiago` y confirmada exitosamente. El mes actual y los meses pendientes, incluidos snapshots obtenidos mientras estaban abiertos aunque fueran vacíos, se consultan nuevamente. Octubre consultado el 14 requiere una consulta final en noviembre antes de reutilizarse; esta incorpora también movimientos del 15 al 31. Actualizar desde la web fuerza recarga desde el último mes con movimientos almacenados hasta el actual, incluido ese último mes; si la base no tiene movimientos, usar tres meses. Conservar particiones de meses anteriores a ese rango y cuentas históricas sin producto activo. Si una consulta falla, informar qué cobertura quedó pendiente y mantener el historial previo.

Una sola actualización web activa por instancia. El servidor responde pronto, ejecuta la tarea fuera del request y permite consultar avance; estados visibles: preparando, comprobando sesión, esperando acceso, descargando, completado y error. La exclusión cubre todo el trabajo y se libera incluso al fallar. Serializar también escrituras simultáneas de CLI/web sobre la misma base para impedir reemplazos cruzados o exportaciones incoherentes.

## Operación local y Docker

Lanzadores equivalentes a `setup_env.sh`, `run.sh`, `run_server.sh`, `server.sh` y Compose, con ayuda y documentación de uso. `run.sh` valida cache y renueva por UI si hace falta; `run_server.sh` usa solo sesión existente y falla sin abrir navegador. `server.sh` ofrece `up`, `down`, `restart`, `status`, `logs` para local/Docker, usando local por defecto. Resolver rutas desde la ubicación del script, incluso invocado fuera de la raíz.

Elegir un puerto Santander configurable y distinto de 8030, comprobar disponibilidad y fallar claramente ante colisión. No detener procesos por puerto ni actuar sobre servicios Banco de Chile. Identificadores de servicio, PID/logs, contenedor y volúmenes exclusivos de Santander. Al cambiar de modo, construir Docker antes de detener un Santander local funcional; `down` conserva sesión/base/exports. Documentar el puerto elegido y acceso mediante localhost, sin exigir cambios en `/etc/hosts`.

Docker publica solo en loopback y persiste cache, SQLite y exportaciones en volúmenes de Santander. El login visible requiere escritorio y las variables/montajes correspondientes, como la referencia Linux; si falta, informar cómo renovar desde un entorno con UI. No prometer renovación interactiva en un contenedor sin escritorio.

## Confidencialidad y rutas

Escuchar en `127.0.0.1`. Validar Host y, para el disparo de actualización, Origin y token de la instancia. Servir una lista explícita de recursos web y proyecciones JSON; negar `.env`, cache, material de sesión, SQLite, respuestas crudas y navegación de directorios, incluidos intentos de traversal.

Excluir del versionado `.env`, sesión, cache, datos, exportaciones y entorno virtual de Santander. Las reglas existentes de Banco de Chile no cubren automáticamente estos directorios nuevos; build debe añadir una regla apropiada sin alterar entradas ajenas. Limitar permisos del material de autenticación y evitar que errores o logs impriman tokens, claves, cabeceras o cuerpos bancarios.

## Verificación esperada

Usar fixtures sanitizadas y pruebas focalizadas para partición a 50, fronteras inclusivas, cargo/abono, decimales y CLP/USD, persistencia transaccional, identidad, exportación acumulativa, errores de sesión, concurrencia y rutas privadas. No usar las credenciales en pruebas automatizadas ni descargar datos bancarios durante una suite normal. La demostración real final es de solo lectura y usa el entorno autorizado del usuario.
