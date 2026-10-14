Genera un archivo `AGENTS.md` analizando directamente el repositorio actual. 

Objetivo:
Crear una version operativa corta para agentes AI: alta senal, bajo ruido, orientada a decisiones y restricciones que cambian el comportamiento del agente.

Fase 1 — Descubrimiento (antes de escribir):
- Explora el repositorio y reune evidencia solo de fuentes reales:
  - Manifiestos y dependencias: `composer.json`, `package.json`, `pom.xml`, `build.gradle`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Gemfile`, etc.
  - Entorno y ejecucion: `Dockerfile`, `docker-compose*.yml`, `Makefile`, `.env.example`, scripts de `package.json`/`composer.json`, CI (`.github/`, `.gitlab-ci.yml`).
  - Estructura de directorios, rutas, puntos de entrada y configuracion de framework.
  - Tests: carpeta, framework, comandos de ejecucion.
  - Convenciones: linters, formatters, `.editorconfig`, nombres de archivos y clases dominantes.
  - Documentacion existente (`README`, `docs/`, `CLAUDE.md`, `AGENTS.md` previo): usala solo como pista secundaria.
- Si existe un `AGENTS.md` previo, usalo como base y actualizalo en lugar de empezar de cero; conserva reglas vigentes y elimina las obsoletas.
- Para nombre del proyecto: usa el del manifiesto o del directorio raiz.

Reglas de veracidad:
- No inventes stack, versiones, rutas, comandos, dominios, convenciones ni decisiones que no puedas verificar en el repositorio.
- Prioriza codigo, configuracion y estructura actual por sobre documentacion cuando haya contradiccion.
- Si un dato relevante no se puede determinar, omitelo o marcalo como `por confirmar`; no lo supongas.
- Verifica que cada comando y ruta citados existan realmente (script definido, archivo presente).
- Si el repositorio esta vacio o casi vacio, indicalo y genera solo la estructura minima con lo verificable.

Requisitos de salida:
- Escribir el resultado en `AGENTS.md` en la raiz del repositorio.
- Mantener maximo 100 lineas.
- Usar Markdown.
- Incluir frontmatter YAML con:
  - `project_name`
  - `date`
  - `status`
- Titulo: `# AGENTS.md — {project_name}`
- Mantener lenguaje directo, accionable y orientado a agentes.
- Conservar comandos exactos cuando sean importantes.
- Evitar duplicacion interna.
- Si existe documentacion util, referenciala por su ruta real en una linea.

Criterio de corte:
- Conserva solo reglas que:
  - cambian comportamiento del agente;
  - evitan romper arquitectura critica;
  - no son inferibles leyendo el codigo;
  - contienen comandos, rutas, convenciones, restricciones, validaciones o riesgos concretos.
- Elimina:
  - buenas practicas genericas;
  - teoria, justificaciones o explicaciones largas;
  - contenido estilo README/wiki;
  - repeticiones;
  - instrucciones vagas que no cambian una decision.

Transformaciones requeridas:
- Parrafos largos -> bullets compactos.
- Reglas absolutas -> reglas condicionales cuando aplique.
- Listas numericas -> bullets sin numero, salvo que el orden sea obligatorio.
- Instrucciones vagas -> reglas especificas o eliminar.
- Repeticion -> una sola fuente o una referencia.

Estructura recomendada:

1. Frontmatter YAML.
2. `# AGENTS.md — {project_name}`
3. `## Fuente de verdad`
   - Prioriza codigo y estructura actual del repositorio por sobre documentacion.
4. Secciones compactas adaptadas al stack real del proyecto.

Secciones base:
- `## Stack`
- `## Framework principal` o nombre real del framework.
- `## Arquitectura`
- `## Autorizacion` si aplica.
- `## UI / Frontend` si aplica.
- `## Rutas, Archivos y Nombres`
- `## Mapa Global App` si hay integraciones, servicios, jobs, colas, cron, APIs o dependencias operativas.
- `## Seguridad y Performance`
- `## Tests y Validacion`
- `## Git y Comandos`
- `## Dominio {project_name}`

Adapta o reemplaza secciones:
- Si una seccion no aplica, reemplazala por la equivalente del stack real o eliminala.
- Si el proyecto usa un framework con restricciones de version o estructura, crea una seccion con el nombre concreto del framework.
- Si hay una capa UI especifica, crea una seccion con su nombre real.
- Si hay reglas de permisos, autenticacion o roles, mantenlas en `Autorizacion`.
- Si hay entidades, flujos o estados de negocio que no deben mezclarse, mantenlos en `Dominio`.

Reglas por defecto (incluir solo si aplican al stack detectado; adaptar terminologia al stack real):

`## Arquitectura`:
- Logica de negocio en la capa correspondiente del stack (p. ej. Models/Services/Controllers); no en vistas.
- Usar transacciones en modificaciones de base de datos, si el proyecto usa base de datos.
- Imports al inicio, en orden alfabetico; no usar nombres totalmente calificados en el cuerpo, si el lenguaje lo permite.
- No introducir frameworks, servicios o tablas nuevas sin decision explicita de arquitectura.
- Capturar excepciones y loguear con contexto.

`## Seguridad y Performance`:
- No hardcodear secretos, credenciales ni URLs; usar `.env` y documentar placeholders en `.env.example` (si el proyecto usa `.env`).
- Evitar consulta N+1; validar indices para busquedas frecuentes (si hay base de datos).

`## Tests y Validacion`:
- No ejecutar tests sin pedido explicito del usuario, salvo validacion de sintaxis, coherencia y ejecucion del codigo.
- Si no puedes validar por entorno faltante, dilo explicitamente.
- Incluir el comando exacto de tests solo si existe en el repositorio.

`## Git y Comandos`:
- No ejecutar `git commit`, `git push` ni `git pull` sin pedido explicito.
- No commitear `.env`.
- Validar sintaxis via Docker cuando el proyecto tenga runtime Docker; conservar el comando exacto detectado en el repositorio.

Prioridad de sintesis:
- Comandos que el agente debe o no debe ejecutar.
- Rutas criticas.
- Convenciones de archivos y nombres.
- Restricciones de framework/version.
- Reglas de autorizacion y validacion backend.
- Reglas de dominio y estados sensibles.
- Validaciones obligatorias antes/despues de cambios.
- Riesgos de seguridad/performance.
- Integraciones externas y puntos fragiles del sistema.

Patrones genericos utiles a rescatar cuando aparezcan en el codigo:
- No reintroducir archivos legacy eliminados por el framework actual.
- No duplicar configuracion entre archivos de bootstrap/providers/config.
- Mantener rutas, alias, prefijos y middleware existentes si son consumidos por UI o integraciones.
- No introducir dependencias nuevas sin decision explicita.
- Validar permisos en backend; usar UI solo para condicionar visibilidad.
- No hardcodear IDs ni valores de dominio fragiles.
- Usar helpers seguros para rutas/URLs cuando existan.
- Paginar listados grandes.
- Para tests destructivos o costosos, conservar el comando exacto y el entorno requerido.
- En cambios sensibles, revisar permisos, filtros, paginacion, eventos UI, N+1 y flujo end-to-end.

Formato:
- Bullets cortos.
- Maximo una idea por bullet.
- Sin consejos genericos como "escribe codigo limpio".
- Sin explicaciones teoricas.
- Sin copiar documentacion existente.
- Sin citas largas.

Verificacion final (antes de entregar):
- El archivo tiene 100 lineas o menos.
- Todo comando y ruta citados existen en el repositorio.
- No hay reglas genericas ni datos supuestos.
- Informa al usuario brevemente que datos quedaron `por confirmar`.
