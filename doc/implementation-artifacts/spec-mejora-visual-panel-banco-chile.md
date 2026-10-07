---
title: 'Mejora visual del panel Banco de Chile'
type: 'feature'
created: '2026-10-07'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** El panel ya presenta la información y los flujos correctos, pero su composición visual puede comunicar mejor la jerarquía entre productos, filtros y cartola, especialmente en anchos intermedios y móviles.

**Approach:** Refinar únicamente el CSS existente para hacer más legible y consistente el layout de escritorio y responsive, sin modificar datos, textos, estructura HTML, JavaScript ni comportamiento de actualización y filtros.

</frozen-after-approval>

## Implementation Notes

- Se modificará exclusivamente `scripts/bancochile/web/styles.css`.
- Se conservarán los selectores y el DOM ya usados por `index.html` y `app.js`.
- La tabla conservará sus ocho columnas y dispondrá de desplazamiento horizontal cuando el ancho no permita una lectura cómoda.
- Se cubrirán estados perceptibles de foco, hover y activo, además de los anchos 1440, 1024, 768 y 375 px.
- Se ajustaron tokens, superficies, espaciado, estados interactivos y jerarquía de la navegación lateral sin cambiar la información ni el comportamiento.
- Se añadió un mínimo de ancho a la tabla y un punto de quiebre intermedio para que las columnas se desplacen horizontalmente en vez de comprimirse.

## Review Triage Log

- defer — La exportación de cuentas históricas de SQLite necesita aislamiento por cliente; no fue causada por el CSS y se registró para trabajo posterior.
- defer — La coordinación de escrituras SQLite requiere una decisión de concurrencia fuera del alcance visual.
- defer — Una base con esquema inválido puede fallar al buscar el último mes; requiere recuperación de datos fuera de alcance.
- defer — Los JSON se publican individualmente y pueden observarse de forma mixta durante una actualización; requiere una estrategia de publicación aparte.
- defer — Movimientos sin `id` no se deduplican; requiere definir una huella estable del dominio.
- defer — El límite de paginación sin `masPaginas` es un riesgo no confirmado con respuestas reales; quedó registrado con su evidencia.
- defer — La actualización restablece el producto seleccionado; es una decisión funcional ajena a CSS.
- defer — Renderizar todos los movimientos puede degradarse con historiales grandes; requiere paginación o virtualización funcional.
- defer — La búsqueda serializa cada movimiento por pulsación; el impacto depende del volumen de datos y queda diferido.
- defer — Los controles de filtro no tienen etiqueta accesible; es una mejora HTML semántica fuera del alcance pedido.
