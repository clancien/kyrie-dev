---
id: SPEC-panel-financiero-santander
companions:
  - integracion-santander.md
  - comportamiento-y-aceptacion.md
  - arquitectura-y-operacion.md
sources:
  - ../../../scripts/bancochile/README.md
  - ../../../scripts/bancochile/docs/arquitectura.md
  - ../../../scripts/bancochile/docs/operacion.md
---

> **Contrato canónico.** Esta SPEC y sus companions constituyen el contrato completo para construir, probar y validar el cambio. Derivados de `.memlog.md` mediante bmad-spec.

# Panel financiero Santander

## Why

El usuario necesita consultar sus finanzas personales Santander con la misma experiencia local de `scripts/bancochile`: cuentas, saldos, tarjetas y movimientos filtrables con historial acumulado. El desarrollo vivirá en `scripts/santander/`, con operación Python y Docker independiente del panel existente.

## Capabilities

- **CAP-1**
  - **intent:** El usuario puede acceder a Santander y reutilizar una sesión válida para consultar sus datos.
  - **success:** Given acceso desde Personas, When completa el login y luego ejecuta otra consulta con sesión vigente, Then obtiene datos sin repetir el login; si vence o requiere intervención, recibe una indicación accionable sin reintentos repetidos ni exposición de secretos.
- **CAP-2**
  - **intent:** El usuario puede consultar sus cuentas y tarjetas con sus saldos y cupos por moneda.
  - **success:** Given los productos obtenidos del banco, When abre el panel, Then distingue corriente, vista y tarjetas, CLP y USD, y valores cero de información no disponible.
- **CAP-3**
  - **intent:** El usuario puede acumular el historial de movimientos de sus cuentas sin perder datos entre ejecuciones.
  - **success:** Given un rango mensual, When termina una descarga completa, Then incorpora todos sus movimientos y exporta el historial acumulado; una respuesta truncada o fallida no confirma el mes ni reemplaza su versión anterior. Una descarga completa durante el mes abierto es un snapshot; solo una consulta completa iniciada después del cierre mensual en `America/Santiago` permite reutilizarlo. Aplican las reglas y pruebas de partición de los companions.
- **CAP-4**
  - **intent:** El usuario puede explorar movimientos de una cuenta o tarjeta mediante búsqueda y filtros.
  - **success:** Given un producto seleccionado, When combina texto, mes y cargo/abono, Then ve solo sus movimientos y sus totales por moneda, con estados vacíos y de error diferenciados.
- **CAP-5**
  - **intent:** El usuario puede actualizar el panel y conocer el resultado de la descarga.
  - **success:** Given el panel abierto, When pulsa Actualizar, Then ve avance, puede completar el acceso si corresponde y recibe el resultado con datos recargados; otra actualización simultánea se rechaza y una falla conserva los datos previos confirmados.
- **CAP-6**
  - **intent:** El usuario puede operar el panel localmente con Python o Docker y ejecutar consultas por CLI.
  - **success:** Given una instalación documentada, When inicia, consulta, reinicia o detiene Santander desde cualquier directorio, Then actúa únicamente sobre sus recursos, conserva datos y sesión, y puede coexistir con Banco de Chile.

## Constraints

- Implementación autocontenida en `scripts/santander/`; no modificar Banco de Chile ni copiar sus datos o sesión. La documentación de esta spec conserva la ubicación nativa BMAD.
- Python, Playwright, requests, SQLite y HTML/CSS/JS siguiendo la separación existente de login, núcleo, CLI y servidor web. Contratos Santander y límites verificados en [integración](integracion-santander.md).
- Iniciar acceso en `https://banco.santander.cl/personas` y abrir el panel lateral; conservar el contexto padre/iframe. Capturar y validar autorización de consultas reales; `storage_state` con cookies por sí solo no demuestra una sesión reutilizable.
- Solo lectura bancaria. Credenciales en `.env`; sesión, encabezados privados, base y respuestas crudas fuera del versionado y de rutas públicas. Panel personal en loopback y puerto distinto de 8030.
- Rangos mensuales inclusivos y mes actual en `America/Santiago`. No asumir paginación Banco de Chile: Santander truncó a 50 filas; aplicar partición conservadora y fallo explícito ante un día posiblemente truncado.
- Conservar moneda, precisión, fecha contable y fecha de operación; no fabricar valores ausentes ni sumar monedas diferentes. Tarjetas muestran últimos movimientos por facturar, sin prometer un historial mensual completo.

## Non-goals

- **Fuera de alcance:** pagos, transferencias, contratación, inversiones, créditos, revelación de datos completos de tarjeta y cambios en productos bancarios.
- Multiusuario, acceso por red o Internet, consolidación entre bancos, migración de datos Banco de Chile y automatización de desafíos de seguridad.
- Importar cartolas PDF/Excel, recorrer todo el historial facturado de tarjetas o prometer una profundidad histórica que Santander no haya demostrado.
- Implementar código o crear stories durante este flujo de especificación.

## Success signal

- Una demostración de solo lectura obtiene cuentas y tarjetas reales, acumula dos consultas sin duplicar ni perder movimientos, recupera el caso verificado de 51 filas frente al rango truncado de 50 y permite filtrar y actualizar el panel. La instalación local y Docker conserva los datos y coexiste con Banco de Chile; se verifican renovación de sesión y protección de rutas privadas.
