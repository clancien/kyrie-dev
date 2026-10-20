---
title: 'Panel financiero Santander'
type: 'feature'
created: '2026-10-14'
status: 'in-progress'
baseline_commit: '1a0e4c9b730adcb767e50bf688cb48ec408d434e'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/docs/specs/spec-panel-financiero-santander/SPEC.md'
  - '{project-root}/docs/specs/spec-panel-financiero-santander/integracion-santander.md'
  - '{project-root}/docs/specs/spec-panel-financiero-santander/comportamiento-y-aceptacion.md'
  - '{project-root}/docs/specs/spec-panel-financiero-santander/arquitectura-y-operacion.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** Falta un panel local Santander para consultar productos e historial personal con sesión reutilizable, filtros y actualización visible.

**Enfoque:** Construir un módulo autónomo Python, Playwright, requests, SQLite y HTML/CSS/JS en `scripts/santander/`. El contrato completo es SPEC-panel-financiero-santander y sus tres companions de `context`. Preservar CAP-1–CAP-6 y todos los criterios AC-1.1–AC-6.3, incluida la demostración real de cierre; las referencias no reducen su aceptación.

## Boundaries & Constraints

**Siempre:** Acceso desde Personas manteniendo contexto padre/iframe. Capturar autorización real por host y validar consultas privadas antes de guardar o reutilizar sesión; verificar titular antes de persistir. Solo lectura bancaria. Credenciales desde `.env` del módulo; material privado con permisos restrictivos y sin secretos en logs. Puerto configurable 8031, distinto de 8030; publicación loopback. Monedas separadas, decimales exactos y valores ausentes nulos.

**Nunca:** Modificar Banco de Chile, copiar sus datos/sesión, asumir sus códigos/paginación, automatizar desafíos, importar cartolas o recorrer facturados. No presentar tarjetas por facturar como historia completa. No modificar kernel, companions o memoria como implementación.

## I/O & Edge-Case Matrix

| Escenario | Entrada / estado | Resultado | Error |
|---|---|---|---|
| Acceso | Sesión nueva/vigente/vencida | Login lateral validado o consulta sin UI tras reinicio | Renovación accionable sin bucles; datos conservados |
| Productos | Corriente/vista/tarjeta CLP/USD | Identidad estable y líneas por moneda; cero distinto de ausente | Código/esquema desconocido explícito |
| Truncamiento | Padre 50; mitades 31+20 | 51 filas de hojas disjuntas; fechas contables inclusivas | Día ≥50 no confirma ni sustituye mes |
| Persistencia | Una hoja falla; filas legítimas iguales | Transacción por titular/cuenta/moneda/mes; multiplicidad intacta | Mes pendiente, otros meses sobreviven |
| Cierre | Snapshot abierto vacío o con datos | Consulta final completa iniciada tras cierre mensual Chile habilita reutilización atómica | Fallo conserva snapshot y obliga a reintentar |
| Exportación | Rango menor y cuentas históricas | JSON acumulado completo y atómico | Sin archivos parciales |
| Panel | Selección/filtros/vacíos/fallos | Estados específicos y totales por moneda | Datos previos señalados |
| Actualización | CLI/web escribiendo misma base | Exclusión global de escritura y avance consultable | Rechazo simultáneo y liberación ante fallo |
| Operación | Otro directorio y reinicio local/Docker | Recursos propios persistentes, build antes de detener local | Colisión clara; rutas privadas/origen ajeno denegados |

</frozen-after-approval>

## Code Map

- `scripts/bancochile/bancochile_login.py`: patrón de perfil persistente; Santander requiere otros selectores y captura real de autorización.
- `scripts/bancochile/bancochile_server_core.py`: patrón de núcleo/SQLite; no copiar paginación, conversión UTC ni reutilización de meses abiertos.
- `scripts/bancochile/bancochile_server_api.py`: referencia de CLI delgada y parámetros mensuales.
- `scripts/bancochile/bancochile_web_server.py`: patrón de trabajo en segundo plano y token; nueva allowlist y proyección sin raw ni encabezados.
- `scripts/bancochile/web/`: referencia de barra lateral, selección y filtros; adaptar identidad Santander, accesibilidad y monedas.
- `scripts/bancochile/server.sh`: patrón de control exclusivo, identificación de PID y construcción previa al cambio de modo.
- `scripts/bancochile/docker-compose.yml`: referencia de escritorio Linux; nuevos recursos y publicación loopback.
- `docs/specs/spec-panel-financiero-santander/`: contrato y evidencia de endpoints; límites técnicos pendientes se verifican durante build, sin inventar códigos.

## Tasks & Acceptance

**Execution:**
- [x] `scripts/santander/tests/test_core.py` — fixtures sanitizadas y pruebas rojas de partición a 50, fronteras inclusivas, fechas distintas, decimales, identidad/multiplicidad, cierre octubre→noviembre (datos nuevos, vacío y fallo final), rollback y exportación — proteger CAP-2/CAP-3.
- [x] `scripts/santander/santander_server_core.py` — adaptador POST por host, validación HTTP/negocio/titular, normalización y partición recursiva sin mezclar padres truncados; SQLite transaccional y exclusión CLI/web — implementar CAP-2/CAP-3.
- [x] `scripts/santander/santander_login.py` y `santander_login_ui.py` — acceso normal, captura privada de contexto por host y verificación real; restauración, expiración e intervención manual — implementar CAP-1.
- [x] `scripts/santander/santander_server_api.py` — CLI delgada con --desde/--hasta, cuenta/base opcionales y validación antes de red; acumulado completo — implementar CAP-6.
- [x] `scripts/santander/tests/test_web.py` y `santander_web_server.py` — trabajo fuera del request, progreso, exclusión, renovación interactiva permitida, errores seguros y allowlist/Host/Origin/token — implementar CAP-5 y AC-6.3.
- [x] `scripts/santander/web/index.html`, `app.js` y `styles.css` — panel Santander adaptable y accesible con búsqueda/mes/tipo, estados por recurso, totales por moneda y selección preservada — implementar CAP-4.
- [ ] `scripts/santander/requirements.txt`, `setup_env.sh`, `run.sh`, `run_server.sh`, `server.sh`, `docker-compose.yml` y `docker/Dockerfile` — operación desde cualquier directorio, recursos propios, disponibilidad de puerto, escritorio y persistencia — implementar CAP-6.
- [x] `.gitignore` y `scripts/santander/README.md`, `docs/arquitectura.md`, `docs/operacion.md` — excluir archivos privados; documentar instalación, puerto, límites y recuperación.
- [ ] `scripts/santander/tests/` — completar aceptación y demostración de cierre del companion, contrastar campos/conteos reales sin versionar información personal.

**Acceptance Criteria:**
- Given el contrato y respuestas reales/sanitizadas, when termina implementación y revisión, then se verifican todos los criterios AC-1.1–AC-6.3 y la demostración de cierre, con evidencia y límites explícitos.
- Given el árbol con cambios previos autorizado por el usuario, when se entrega, then se preservan esos cambios y Banco de Chile permanece intacto.

## Implementation Notes

- Implementación y comprobaciones locales realizadas; estado de entrega `blocked`, estado operativo `in-progress`. No se modificó el bloque congelado ni el contrato fuente.
- Login real Personas/iframe con captura automática por host, titular contrastado desde respuesta, sesión HTTP restaurada, cuentas corriente/vista y tarjetas CLP/USD comprobados. Dos consultas históricas conservaron identidad/multiplicidad. Reproducción bancaria del caso 50 frente a 31+20=51, sin usar el padre truncado.
- Verificación principal: 22 pruebas offline aprobadas (incluye navegador con datos sintéticos), `node --check`, `bash -n`, Compose `config --quiet` y `git diff --check` aprobados desde la raíz. Reinicio local desde `/tmp` correcto; servicio en localhost:8031. Banco de Chile sin cambios.
- Inspección principal del diff y correcciones de permisos en base personalizada, cierre de conexiones SQLite, decimales sin notación exponencial y puertos dinámicos de prueba. No sustituye las tres capas formales de revisión de step-04, pendientes.
- Bloqueo externo: Docker BuildKit falló con `forwarding Ping: no such job`; legacy falló por falta de espacio al exportar capa; último build optimizado falló por espacio insuficiente en `/var/cache/apt/archives`. Logs de esta sesión en `/tmp/santander-docker-build.log`, `/tmp/santander-docker-legacy.log` y `/tmp/santander-docker-focused.log`. No se eliminaron recursos ajenos; el temporal propio de un build fallido fue eliminado por el implementador.
- Falta demostrar persistencia/renovación en contenedor y después completar revisión formal y cierre. El gate de step-03 exige: “If any task is not done or any acceptance criterion is not satisfied, finish the missing work before proceeding”. Por eso no se avanzó a in-review/done ni se creó commit.
- Trazabilidad y matriz de pruebas en [informe de verificación](spec-panel-financiero-santander.verificacion.md).

## Spec Change Log

## Review Triage Log

## Design Notes

No hay decisiones de producto pendientes ni migraciones destructivas. Huella: módulo nuevo completo, regla de exclusión y tracking BMAD. Las consultas son de lectura y generan almacenamiento local privado. Cierre reutilizable requiere consulta completa iniciada después del cierre en America/Santiago; un cambio de calendario o snapshot vacío no basta.

## Verification

**Commands:**
- `python3 -m unittest discover -s scripts/santander/tests -v` — fixtures sin credenciales ni red bancaria.
- `bash -n scripts/santander/*.sh` y ayuda de lanzadores desde `/tmp` — sintaxis/rutas independientes.
- `node --check scripts/santander/web/app.js` — JavaScript válido.
- `docker compose -f scripts/santander/docker-compose.yml config` — configuración propia y persistente.

**Comprobaciones reales:** login con configuración final, reinicio/restauración, renovación, cuentas/tarjetas por moneda, rango histórico repetido, persistencia local/Docker y filtros/actualización. Un bloqueo de entorno o autenticación pendiente impide afirmar cierre completo.
