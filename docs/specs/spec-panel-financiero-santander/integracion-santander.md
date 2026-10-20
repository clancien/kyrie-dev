# Integración Santander: evidencia y contrato

## Evidencia de Chrome MCP

Descubrimiento del 14 de octubre de 2026 sobre sesión real iniciada manualmente por el usuario. Las referencias de red son evidencia de esta sesión, no identificadores persistentes. Se omitieron RUT, números de cuenta, nombres, saldos, credenciales, tokens y encabezados con valores privados.

El acceso normal parte en `https://banco.santander.cl/personas`, botón «Ingresar al sitio privado», y abre `iframe#login-frame` con ruta `https://mibanco.santander.cl/UI.Web.HB/Private_new/frame/#/public/login-frame/ing/0010`. Dentro están `input#rut`, `input#pass` y «Ingresar». La clave tiene `maxlength=10`. No truncar silenciosamente una configuración inválida. Abrir el iframe como pestaña independiente no sustituye este flujo.

Se observaron rechazos de credenciales antes de la última corrección del `.env`. El acceso manual posterior llegó a `/UI.Web.HB/Private_new/frame/#/private/main`. No se comprobó aún el login automático con el archivo final; esa verificación corresponde a CAP-1.

Rutas privadas observadas, relativas al hash de `frame/`:

| Pantalla | Ruta |
| --- | --- |
| Inicio y productos | `/private/main` |
| Saldos de cuenta | `/private/saldos/main/mi-cuenta` |
| Movimientos de cuenta | `/private/saldos/main/movimientos` |
| Cartolas | `/private/saldos/main/cartolas` |
| Cupos de tarjeta | `/private/Saldos_TC/main/detail` |
| Por facturar | `/private/Saldos_TC/main/bill` |
| Facturados | `/private/Saldos_TC/main/billed` |

## Consultas verificadas

Todos los siguientes endpoints son POST. Base **DSK**: `https://api-dsk.santander.cl/perdsk/`. Base **OB**: `https://openbanking.santander.cl/`.

| Recurso | Endpoint relativo | Entrada observada | Salida útil |
| --- | --- | --- | --- |
| Productos | DSK `datosCliente/cruceProductosOnline` | `cabecera`, `INPUT` con documento, canal y cruce | `DATA.OUTPUT.MATRICES.MATRIZCAPTACIONES.e1` |
| Saldos | OB `account_balances_transactions_and_withholdings_retail/v1/current-accounts/balances` | `accountId`, `currency`, `commercialGroup` | `additionalInfo`, `balance` |
| Movimientos de cuenta | OB `account_balances_transactions_and_withholdings_retail/v1/current-accounts/transactions` | Los anteriores más `openingDate`, `closingDate` en `YYYY-MM-DD` | `additionalInfo`, `movements` |
| Últimos movimientos de tarjeta | DSK `tarjetasDeCredito/consultaUltimosMovimientos` | `Cabecera`, `Entrada.{Entidad,Centro,Cuenta,Moneda}` | `DATA.Informacion`, `DATA.MatrizMovimientos` |

Los productos contienen `NUMEROCONTRATO`, `PRODUCTO`, `SUBPRODUCTO`, `MONTODISPONIBLE`, `MONTOUTILIZADO`, `CUPO`, `GLOSACORTA`, `NUMEROPAN`, `CODIGOMONEDA` y `AGRUPACIONCOMERCIAL`. En esta sesión se verificaron corriente, vista y tarjeta con CLP/USD. Construir el adaptador por identificadores de contrato y moneda verificados; no derivar códigos Santander de `CTD` u otros códigos de Banco de Chile. Filtrar productos ajenos al alcance.

`balance` contiene `totalBalance`, `currencyCode`, `availableBalance`, `overdraftAgreement`, `balanceLca`, `agreedTurns`, `draftsMade`. No confundir saldo contable, disponible y línea de crédito. Los montos observados son strings; no asumir el mismo formato decimal en todos los recursos.

Cada movimiento de cuenta contiene `accountingDate`, `transactionDate`, `operationTime`, `newBalance`, `codeOperationMovement`, `movementAmount`, `observation`, `expandedCode`, `movementNumber`, `chargePaymentFlag`. Se contrastó `D` = cargo y `H` = abono con la UI. `operationTime` apareció como `HHmm`. La fecha contable puede ser posterior a la de operación y al día local de consulta; preservar ambas.

`additionalInfo` incluyó `code-ms=00` y `message-ms` vacío para consultas exitosas. Validar resultado de negocio además de HTTP. Un error, estructura desconocida o respuesta HTML no equivale a lista vacía. Para DSK validar `METADATA` y el bloque `INFO`/`Informacion` correspondiente antes de consumir matrices.

Tarjetas devuelve `Fecha`, `Descripcion`, `Comercio`, `Importe`, `DescripcionRubro`, `Ciudad`, `TipoBen`, `IndicadorDebeHaber`. Se observaron 15 filas en CLP y cambio de consulta mediante «Pesos»/«Dólares». Verificar los códigos de debe/haber propios de esta respuesta antes de normalizarlos; no trasladar automáticamente D/H desde cuentas. Etiquetar como últimos movimientos por facturar y conservar separación por moneda, sin afirmar completitud mensual.

## Autorización y reutilización

La consulta de saldos fuera de Chrome respondió 403 con un subconjunto incompleto de encabezados y 200 al reproducir los encabezados de la solicitud observada, excluyendo los de transporte. Se confirmó lectura HTTP independiente con la sesión vigente; no se confirmó duración, renovación automática ni supervivencia tras reiniciar el navegador.

Encabezados observados que afectan al adaptador: `authorization`, `x-client-code`, `x-santander-client-id`, `x-organization-code`, `x-schema-id`, `origin`, `referer`, `user-agent`; también aparecieron `x-b3-spanid`, encabezados de negociación y de contexto del navegador. La prueba exitosa no aisló el conjunto mínimo. Capturar el contexto necesario por host a partir de solicitudes bancarias legítimas; verificarlo con una consulta de lectura antes de usarlo. No fijar tokens de esta investigación en código ni suponer equivalencia de autorización entre hosts.

Guardar material de autenticación en cache privado con permisos restrictivos junto al estado de navegador necesario. Validar titular antes de escribir datos. Un rechazo de credenciales no provoca bucles; un 401/403, redirección al login o falta de contexto invalida la reutilización y solicita renovar por el flujo normal. En modo solo servidor, fallar con instrucciones sin abrir UI. El modo interactivo permite completar desafíos manualmente.

## Truncamiento e historial de cuentas

La pantalla anuncia «últimos 40 días», pero una consulta HTTP de agosto de 2026 devolvió movimientos de ese mes. Esto demuestra consulta anterior al período visual para el caso probado; no demuestra historial ilimitado.

Prueba de cuenta vista, septiembre de 2026:

| Intervalo inclusivo | Filas |
| --- | ---: |
| 01–27 | 50 |
| 01–13 | 31 |
| 14–27 | 20 |
| Unión de las mitades | 51 distintas |

La unión recuperó una fila adicional y conservó las 50 originales. No apareció cursor ni bandera de continuación. Una consulta con inicio y fin en el mismo día devolvió los movimientos de ese día. No usar `masPaginas` ni incrementos heredados de Banco de Chile.

Regla contractual: dividir cada mes solicitado en intervalos inclusivos disjuntos. Si una respuesta tiene **50 o más filas**, dividir por días y consultar ambas mitades; repetir hasta que cada hoja tenga menos de 50 filas. No mezclar el resultado truncado del padre con el de sus hijos. Si una hoja de un día mantiene 50 o más filas, abortar ese mes con «posiblemente truncado»; no inventar un cursor ni certificar completitud. Un cambio de esquema o nuevas señales de continuación exige adaptar este contrato con evidencia.

Persistir por fecha contable y comprobar límites con fixtures que incluyan fechas de operación diferentes. Si el resultado contradice el rango solicitado o no permite probar cobertura, no confirmarlo. Una descarga con todas las hojas válidas acredita el snapshot hasta la consulta, no que el mes haya cerrado. Meses futuros explícitamente solicitados no deben confirmarse como historia cerrada; el mes actual siempre se vuelve a consultar. Un mes anterior solo es reutilizable si la consulta completa de su primer a último día se inició después del cierre del mes en `America/Santiago` y terminó con todas las hojas válidas y commit exitoso. Haber cambiado de mes no convierte un snapshot anterior, incluso vacío, en cerrado. Si esa consulta final falla, conservar la versión previa sin habilitar reutilización y reintentar el cierre en otra ejecución.

## Cartolas y facturados: límite del descubrimiento

Se observaron DSK `datosCliente/ultCartolaHistorica`, `serviciosCliente/documentos/DocRecientes` y `datosCliente/buzonVirtual`. La UI busca por mes y ofrece PDF/Excel; que el calendario permita un año no demuestra que existan todos sus documentos.

`buzonVirtual` recibe `cabecera` e `INPUT.{formato,contrato,rutCliente,fechaInicio,fechaFin,tipoDocumento}`; entrega `DATA.OUTPUT.INFO` y `FILE` base64. La UI confirmó una descarga Excel, pero el contenido decodificado observado era texto sin tabla HTML/XML ni encabezados reconocibles de movimientos. No se validó un parser. **No importar este formato en este alcance**: usar el endpoint de movimientos y su partición.

En tarjetas facturadas se observaron `cuentasDisponibles`, `estadoCuentaNacional` y `estadoDeCuenta`. El primero enumera períodos y el segundo incluye `NumExtracto`, `NumMov`, `FilasRecuperar`, `ID-RECALL` y matriz de movimientos. Se documentan para evitar confundirlos con últimos movimientos; no se recorrerán como historial completo en CAP-3.

## Límites pendientes de verificación durante build

- Login automatizado con el `.env` final y captura de contexto por host; sesión restaurada tras reinicio y comportamiento al expirar.
- Formatos y códigos monetarios por recurso, identificación estable y alcance real de `movementNumber`.
- Mayor profundidad histórica, productos distintos de los observados y posibles cambios del límite de 50. Ante falta de cobertura, error explícito y mes pendiente.
- Caso de un solo día con 50 filas: fallo definido, sin promesa de recuperación completa por esta vía.

Estos son límites técnicos con comportamiento definido, no decisiones de producto sin consultar. No hay supuestos aceptados que presenten esos hechos como ya demostrados.
