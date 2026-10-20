# Comportamiento y aceptación

## Panel

Conservar la organización de Banco de Chile: cabecera con marca Santander y botón Actualizar; barra lateral con Cuentas y Tarjetas; área principal de movimientos con búsqueda, mes y tipo. Usar identidad visual Santander y recursos locales. Diseño adaptable; selección y foco de teclado visibles, filtros con etiquetas y mensajes de avance anunciables.

Al abrir sin selección: invitar a seleccionar un producto. Al seleccionar cuenta: historial acumulado de esa cuenta. Al seleccionar tarjeta: últimos movimientos por facturar, identificados como tales, con separación de moneda. No mostrar un extracto incompleto de tarjeta como historial mensual completo. Conservar selección después de actualizar si el producto sigue presente.

Columnas de cuenta: fecha contable, hora/fecha de operación disponible, descripción, cargo, abono y saldo. Origen o comentario solo si están presentes en datos bancarios verificados; no extraerlos mediante conjeturas desde nombres o texto libre. Tarjetas usan las columnas realmente disponibles. Formato `es-CL`, precisión monetaria apropiada y totales separados por moneda para el resultado filtrado.

Distinguir: sin productos, producto sin movimientos, filtros sin coincidencias, recurso no disponible, carga inicial fallida y datos anteriores conservados tras fallo. Una falla no se convierte en «sin movimientos». Mostrar última actualización por recurso y advertir si se están mostrando datos previos.

## Criterios Given/When/Then

| ID / capacidad | Given | When | Then |
| --- | --- | --- | --- |
| AC-1.1 / CAP-1 | Credenciales configuradas y sin sesión | Inicia el flujo interactivo | Abre Personas y su panel lateral, completa el acceso permitido y valida una consulta privada antes de guardar sesión |
| AC-1.2 / CAP-1 | Sesión guardada y vigente | Ejecuta modo servidor | Consulta sin abrir UI; al reiniciar el proceso restaura y valida el contexto requerido por cada host |
| AC-1.3 / CAP-1 | Sesión vencida o 401/403 | Ejecuta servidor o Actualizar | Servidor falla con instrucciones; Actualizar permite renovar por UI; no mezcla datos de otro titular ni reintenta indefinidamente |
| AC-1.4 / CAP-1 | Credenciales rechazadas o desafío pendiente | El acceso no termina | Informa el problema sin revelar secretos y conserva datos previos; el desafío queda a cargo del usuario |
| AC-2.1 / CAP-2 | Respuestas sanitizadas de corriente, vista y tarjeta CLP/USD | Carga productos | Los identifica sin duplicar moneda como otra tarjeta y presenta disponible/contable/utilizado/cupo según el recurso |
| AC-2.2 / CAP-2 | Un valor cero, un campo ausente y un recurso fallido | Renderiza | Muestra cero, no disponible y error/dato previo respectivamente, conservando precisión y moneda |
| AC-3.1 / CAP-3 | Base vacía y reloj controlado en Chile | Consulta sin fechas | Solicita el mes actual y los dos anteriores; fechas inválidas o invertidas fallan antes de usar red |
| AC-3.2 / CAP-3 | Mes con respuesta padre de 50 filas y dos mitades de 31 y 20 distintas | Descarga el mes | Guarda 51 filas de las hojas, sin usar como completo el resultado truncado del padre |
| AC-3.3 / CAP-3 | Intervalo dividido hasta un solo día que aún devuelve 50 o más | Actualiza | Falla explícitamente ese mes, no lo confirma ni sustituye su versión anterior; no inventa paginación |
| AC-3.4 / CAP-3 | Una hoja falla después de otras exitosas | Persiste | Revierte solo el mes incompleto; conserva otros meses confirmados y lo reintenta en otra ejecución |
| AC-3.5 / CAP-3 | Reloj controlado en `America/Santiago`: snapshot de octubre obtenido el 14, con movimientos o inicialmente vacío; banco incorpora movimientos del 15 al 31 | Repite la consulta en noviembre | Reconsulta todo octubre antes de habilitar reutilización, incorpora los nuevos movimientos sin duplicar y refresca noviembre; solo una consulta iniciada después del cierre y terminada válida y completamente permite reutilizar octubre después. Si la consulta final falla, conserva el snapshot anterior, deja octubre pendiente sin habilitar reutilización y lo reintenta; un vacío también requiere esa consulta final válida |
| AC-3.6 / CAP-3 | Historial anterior al rango nuevo y cuenta histórica | Exporta después de consultar rango menor | Mantiene todo lo acumulado y su cuenta identificable; el JSON nunca queda parcialmente escrito |
| AC-3.7 / CAP-3 | Dos cuentas con IDs similares, dos movimientos legítimos iguales y fechas contable/operación distintas | Normaliza y refresca | Conserva identidad y multiplicidad, agrupa por fecha contable y no elimina por fecha posterior al día local |
| AC-4.1 / CAP-4 | Cuenta seleccionada con cargos y abonos en varios meses | Combina búsqueda, mes y tipo | Filtra esa cuenta y recalcula recuentos/totales; limpiar filtros recupera el conjunto |
| AC-4.2 / CAP-4 | Tarjeta con CLP y USD | Selecciona movimientos | Identifica moneda y alcance por facturar, sin sumar CLP con USD ni inventar saldo/hora/códigos de tipo |
| AC-4.3 / CAP-4 | Sin selección, sin datos o filtros sin coincidencias | Abre o filtra | Presenta el mensaje específico y controles accesibles; el layout sigue utilizable en ancho reducido |
| AC-5.1 / CAP-5 | Base con último mes de movimientos anterior al actual | Pulsa Actualizar | Fuerza ese mes y los siguientes hasta actual; con base sin movimientos consulta tres meses; muestra avance y recarga preservando selección |
| AC-5.2 / CAP-5 | Actualización activa o CLI escribiendo la misma base | Solicita otra escritura | Evita trabajos superpuestos y resultados/exportaciones incoherentes; la web sigue consultable |
| AC-5.3 / CAP-5 | Falla de sesión, red, esquema o timeout | Termina el trabajo | Libera exclusión, muestra error accionable y mantiene datos previos señalados como tales |
| AC-6.1 / CAP-6 | Entorno configurado y Banco de Chile en 8030 | Ejecuta lanzadores desde otro directorio | Santander usa recursos y puerto propios; funciona local y Docker sin detener Banco de Chile |
| AC-6.2 / CAP-6 | Datos/sesión Santander persistidos | Reinicia o detiene local/Docker | Conserva archivos; status/logs corresponden al servicio propio; construcción Docker fallida mantiene el Santander local existente |
| AC-6.3 / CAP-6 | Panel iniciado | Solicita archivos privados/traversal o actualización desde origen ajeno | Niega acceso; solo expone frontend y proyecciones permitidas; logs y errores no contienen secretos |

## Demostración de cierre

Verificar acceso real con el `.env` final, consulta de ambos tipos de cuenta, resumen y movimientos de tarjeta por moneda, un rango histórico de cuentas y su repetición. Contrastar conteos y una muestra de campos con Santander sin guardar evidencias personales en la spec. Ejecutar fixtures del truncamiento verificado, del día saturado y del cierre octubre→noviembre con movimientos nuevos, snapshot inicialmente vacío y fallo de consulta final; comprobar renovación de sesión, actualización concurrente y persistencia en ambos modos.

Una UI que carga datos de ejemplo o un HTTP 200 aislado no satisface la demostración completa.
