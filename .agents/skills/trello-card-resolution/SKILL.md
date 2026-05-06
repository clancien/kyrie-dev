---
name: trello-card-resolution
description: "Resolver tarjetas de soporte SIDOT desde Trello con flujo operativo reproducible: configurar credenciales/lista de trabajo, sincronizar tarjetas y adjuntos, mantener índice `doc/.trello/cards.json`, mover tarjetas cerradas a `doc/.trello/.done/`, y producir scripts SQL usando plantillas de `doc/sql/operacion/templates/`. Usar cuando se pida triage o resolución de tickets SIDOT basados en Trello."
---

# Trello Card Resolution

## Flujo

1. Configurar Trello con `setup.sh` (interactivo o lectura).
2. Usar skill `trello-connect` para obtener boards/listas/tarjetas por stdout.
3. Sincronizar tarjetas desde `TRELLO_LIST_ID` con `get_trello_cards.py` (internamente consume skill `trello-connect`).
4. Revisar `doc/.trello/cards.json` y `analysis.md` por tarjeta.
5. Resolver IDs operativos en SIDOT de forma nativa usando skill `sidot-connect` (ej: `donante_id`, `trasplante_id`).
6. Crear SQL de resolución en `doc/sql/operacion/{YEAR}/` con templates.
7. Marcar `SOLUCIONADO` en `cards.json` cuando aplique.
8. Al cerrarse en Trello, re-ejecutar sync para mover carpeta a `.done/` y marcar `CERRADO`.

## Rutas

- Índice: `doc/.trello/cards.json`
- Carpeta activa por tarjeta: `doc/.trello/{nombre_tarjeta}/`
- Carpeta cerrada por tarjeta: `doc/.trello/.done/{nombre_tarjeta}/`
- Templates SQL: `doc/sql/operacion/templates/`
- SQL resultante: `doc/sql/operacion/{YEAR}/YYYYMMDD_{accion}_{codigo_sidot}.sql`

## Variables `.env` requeridas

- `TRELLO_KEY`
- `TRELLO_TOKEN`
- `TRELLO_LIST_ID` (fuente de `get_trello_cards.py`)
- Opcional para utilidades de exploración: `TRELLO_BOARD_ID`

## Comandos

```bash
# Configuración interactiva (selecciona board y lista; escribe IDs en .env)
./.agents/skills/trello-card-resolution/assets/setup.sh --project-root "$PWD"

# Ver configuración actual y resolver nombre de board/lista
./.agents/skills/trello-card-resolution/assets/setup.sh --read --project-root "$PWD"

# Consultar conectividad Trello (skill `trello-connect`; solo stdout)
python3 .agents/skills/trello-connect/assets/trello_fetch.py --project-root "$PWD" ping
python3 .agents/skills/trello-connect/assets/trello_fetch.py --project-root "$PWD" boards
python3 .agents/skills/trello-connect/assets/trello_fetch.py --project-root "$PWD" lists --board-id <BOARD_ID>
python3 .agents/skills/trello-connect/assets/trello_fetch.py --project-root "$PWD" cards --list-id <LIST_ID>
python3 .agents/skills/trello-connect/assets/trello_fetch.py --project-root "$PWD" card --card-id <CARD_ID>

# Sincronizar tarjetas abiertas de la lista configurada
python3 .agents/skills/trello-card-resolution/assets/get_trello_cards.py --project-root "$PWD"
python3 .agents/skills/trello-card-resolution/assets/get_trello_cards.py --project-root "$PWD" --stdout

# Generar UI estática de tarjetas
python3 .agents/skills/trello-card-resolution/assets/render_cards_html.py --project-root "$PWD"
```

Implementación de setup:
- `setup.sh` es wrapper shell.
- Lógica Python: `.agents/skills/trello-card-resolution/assets/setup_trello.py`.
- Conectividad Trello del setup: cliente `TrelloClient` desde `trello-connect/assets/api.py`.

## Estado de tarjetas en `cards.json`

- `DESCARGADO`: tarjeta abierta sincronizada.
- `SOLUCIONADO`: resolución técnica aplicada/validada localmente.
- `CERRADO`: tarjeta ya no está abierta en Trello; carpeta movida a `.done/`.

Campos relevantes por tarjeta en `cards.json`:
- `members`: arreglo de asignados (`id`, `full_name`, `username`).
- `comments`: arreglo de comentarios (`id`, `date`, `text`, `member`).

## UI estática (`render_cards_html.py`)

- Entrada: `doc/.trello/cards.json`
- Salida: `doc/.trello/cards-ui/`
- `index.html`: tabla navegable (fila clickeable).
- `card_<id>.html`:
- renderiza `analysis.md` en HTML con `marked.js` (CDN).
- muestra miembros asignados y comentarios sincronizados.
- muestra adjuntos.
- abre adjuntos y botón `Abrir análisis (.md)` en iframe lateral derecho.
- incluye botón `Volver al listado`.

## Reglas de trabajo

- No inventar IDs ni datos no trazables.
- Mantener 1:1 entre tarjeta y evidencia (`analysis.md` + SQL generado).
- Priorizar templates existentes para SQL.
- Mantener rutas/nombres consistentes con este skill.
- La obtención de datos de Trello debe hacerse vía skill `trello-connect` (stdout JSON), no con persistencia intermedia.
- Para datos que dependan del portal SIDOT (ej: `donante_id`, `trasplante_id`, catálogo de hospitales), usar el skill `sidot-connect` en vez de estimaciones manuales.
- Al resolver una tarjeta, actualizar `analysis.md` de la tarjeta con:
  - decisiones tomadas,
  - plan implementado (pasos ejecutados),
  - referencia explícita al/los SQL generado(s) en `doc/sql/operacion/{YEAR}/`.

## Integración API Skills

- Conectividad Trello: usar cliente de `trello-connect` (`assets/api.py`) o su script `trello_fetch.py`.
- Conectividad SIDOT: usar cliente de `sidot-connect` (`assets/api.py`) para datos operativos.
- Evitar llamadas HTTP directas duplicadas a servicios externos dentro de este skill.

Métodos usados por este skill:
- Trello (vía `trello-connect`):
  - `TrelloClient.get("lists/<id>/cards", ...)`
  - `TrelloClient.get("cards/<id>", ...)`
  - `TrelloClient.download_card_attachment(card_id, attachment_id, filename)`
- SIDOT (cuando aplique resolución de IDs):
  - `SidotClient.login()`
  - `SidotClient.get("/donante/?...")`
  - `SidotClient.get("/donante/extraccion/<donante_id>")`
