# Verificación de build Santander

Estado de entrega: **blocked**. Estado operativo: **in-progress**. El panel local está en http://localhost:8031.

Contrato: [SPEC nativa](../specs/spec-panel-financiero-santander/SPEC.md) y sus tres companions. Implementación: [spec operativa](spec-panel-financiero-santander.md). Código: [scripts/santander](../../scripts/santander/README.md).

## Comprobaciones ejecutadas

Directorio `/home/clancien/workspace/dev`, salvo el reinicio explícito desde `/tmp`.

| Comando | Resultado |
|---|---|
| `scripts/santander/.venv/bin/python -m unittest discover -s scripts/santander/tests -v` | 22 pruebas aprobadas, sin credenciales ni red bancaria |
| `node --check scripts/santander/web/app.js` | exit 0 |
| `bash -n scripts/santander/server.sh scripts/santander/run.sh scripts/santander/run_server.sh scripts/santander/setup_env.sh` | exit 0 |
| `docker compose -p santander-panel -f scripts/santander/docker-compose.yml config --quiet` | exit 0 |
| `git diff --check` | exit 0 |
| `/home/clancien/workspace/dev/scripts/santander/server.sh restart local` desde `/tmp` | disponible en localhost:8031 |
| Instalación de venv y Chromium Santander | correcta |
| Login UI final y consulta CLI restaurada | acceso/captura/validación reales correctos |
| CLI histórica septiembre/octubre, repetida | snapshots sin duplicación; mes abierto no reutilizable |
| Navegador real del panel, filtros y Actualizar | selección conservada, filas recargadas, ancho reducido utilizable, sin errores JS |

## Matriz → pruebas aprobadas

| Fila operativa | Evidencia automatizada |
|---|---|
| Acceso | `test_http_business_and_holder`: 401, HTML, fallo de negocio, titular diferente; acceso y renovación real comprobados adicionalmente |
| Productos | `test_verified_product_fixture`, `test_card_decimal_and_codes`, `test_exact_and_unknown`: agrupación multimoneda, cero/nulo y códigos desconocidos |
| Truncamiento | `test_partition`, `test_saturated_day`, `test_foreign_date`: hojas disjuntas, 50→51, día saturado y cobertura inválida |
| Persistencia | `test_later_leaf_failure_keeps_previous_partition`, `test_dates_and_duplicates`, `test_previous_balance_survives`: fallo tras hoja exitosa, multiplicidad, fechas contable/operación y valores previos |
| Cierre | `test_full_update_closure`: reloj octubre→noviembre, datos nuevos, snapshot vacío, fallo final, reintento y reutilización solo tras cierre confirmado |
| Exportación | `test_export_historical_and_identity`, `test_empty_identity_and_alias_lock`: historial y productos anteriores, separación de cuentas, titular aun sin productos |
| Panel | `test_filters_currencies_failure_and_mobile`: filtros, totales separados, fallo con datos previos y selección, tarjeta sin columnas inventadas, móvil y errores JS |
| Actualización | `test_update_background_and_writer_rejection`, `test_lock`: progreso, lectura durante trabajo, rechazo de segundo escritor CLI/web |
| Operación | `test_allowlist`, `test_custom_database_preserves_existing_parent_permissions`; Bash/Compose y reinicio local desde otro directorio correctos. **Demostración Docker pendiente** |

La suite usa fixtures sintéticas y nunca credenciales ni solicitudes al banco. Las consultas reales fueron comprobaciones separadas autorizadas, de solo lectura. El caso bancario de truncamiento reprodujo 50 frente a 31+20=51 y conservó las filas del padre en la unión. No se versionaron capturas ni datos personales.

## Bloqueo y continuación

Tres intentos de construcción Docker fallaron: BuildKit perdió su job; legacy agotó espacio al exportar; una imagen optimizada sin duplicar navegadores tampoco dispuso del espacio requerido por apt. Logs temporales de sesión: `/tmp/santander-docker-build.log`, `/tmp/santander-docker-legacy.log`, `/tmp/santander-docker-focused.log`. El servicio local permaneció activo y no se inició el servicio Docker. No se limpiaron recursos ajenos.

Pendiente: disponer de espacio en el almacenamiento Docker, construir, verificar consulta/renovación y persistencia en contenedor, y completar las tres capas de revisión de bmad-build. La inspección del principal y los tests no sustituyen esa revisión. El paso 3 no permite pasar a revisión mientras falte aceptación; por eso la spec y el índice permanecen `in-progress`. Sin commit ni cierre de spec.

Se preservaron el contrato fuente, Banco de Chile y cambios previos del usuario. La regla global `.reviews` apareció en el diff general pero no fue agregada por este build y se preservó; el bloque añadido por build a `.gitignore` cubre solo material privado Santander.
