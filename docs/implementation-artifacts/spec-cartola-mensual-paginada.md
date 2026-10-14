---
title: 'Consulta mensual paginada de cartola'
type: 'feature'
created: '2026-10-07'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** La consulta de cartola usa el rango predeterminado del banco, por lo que no permite recuperar historia anterior de forma controlada.

**Approach:** Añadir filtros CLI por mes y un rango mensual inclusivo; consultar cada mes con su paginación y registrar los rangos solicitados en la salida.

</frozen-after-approval>

## Implementation Notes

- Se añadieron `--month` y el rango inclusivo `--from-month` / `--to-month`.
- Cada mes se convierte desde medianoche de Chile a UTC y reinicia su paginación.
- La paginación se detiene con `pagina[0].masPaginas`; la lista `movimientos` se prioriza sobre listas auxiliares de la respuesta.
- `run.sh` y `run_server.sh` reenvían los argumentos al CLI.

## Review Triage Log

- Corregido: los lanzadores fijaban dos páginas y descartaban argumentos; ambos reenvían ahora `"$@"` después de sus valores predeterminados.
- Corregido: `--month` con `--to-month` se rechaza explícitamente para evitar que el valor sea ignorado.
- Corregido: se validan años entre 0001 y 9998 antes de crear fechas.
- Corregido: se agregaron pruebas unitarias para límites mensuales, DST, validación y paginación.
