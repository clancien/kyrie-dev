- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Aislar la cartola almacenada por identidad de cliente para no exportar cuentas históricas de otra sesión.
  evidence: `accumulated_cartola` lee todos los `account_key` de SQLite; es un riesgo de privacidad existente fuera de la mejora CSS.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Coordinar el acceso simultáneo a SQLite entre el panel web y el CLI.
  evidence: Dos procesos pueden escribir la misma base y superar el tiempo de espera predeterminado; requiere definir una política de exclusión fuera del alcance visual.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Recuperar explícitamente bases SQLite vacías, corruptas o con esquema anterior al buscar el último mes.
  evidence: `latest_month_with_data` asume la tabla `cartola_months` si existe el archivo de base.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Publicar los JSON del panel como un conjunto atómico y versionado.
  evidence: Los cinco archivos de salida se escriben de forma independiente y una recarga puede observar datos de ejecuciones distintas.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Añadir una huella de respaldo para deduplicar movimientos sin identificador.
  evidence: La deduplicación actual solo actúa cuando el movimiento incluye `id`.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Definir un límite de terminación para la paginación cuando la API no entrega `masPaginas`.
  evidence: El fallback depende de que una página no tenga movimientos; faltaría comprobar respuestas variables de una API sin bandera. Severidad pendiente de confirmar con respuestas reales.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Conservar el producto seleccionado al terminar una actualización del panel.
  evidence: `render()` restablece la selección a la cuenta corriente; requiere una decisión de comportamiento no relacionada con CSS.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Paginar o virtualizar historiales de movimientos acumulados extensos.
  evidence: La tabla renderiza todos los movimientos filtrados y puede degradarse con historiales grandes; modificarlo alteraría el alcance de la cartola.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Optimizar la búsqueda de la cartola acumulada para historiales extensos.
  evidence: Cada pulsación serializa todos los movimientos mediante `JSON.stringify`; el impacto exacto depende del volumen de datos.
- source_spec: `doc/implementation-artifacts/spec-mejora-visual-panel-banco-chile.md`
  summary: Incorporar etiquetas accesibles a buscador y filtros de movimientos.
  evidence: Los controles se identifican solo con placeholder u opción inicial; es una mejora semántica ajena al alcance exclusivo de CSS.
