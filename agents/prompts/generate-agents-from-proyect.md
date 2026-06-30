Genera un archivo `AGENTS.md` basado en el contenido de `doc/project-context.md`.

Objetivo:
Crear una version operativa corta para agentes AI: alta senal, bajo ruido, orientada a decisiones y restricciones que cambian el comportamiento del agente.

Reglas de entrada:
- Debe existir `doc/project-context.md`.
- Si no existe, indica que primero debe generarse con el prompt `generate-proyect-context.md`.
- No inventes stack, versiones, rutas, comandos, dominios, convenciones ni decisiones que no aparezcan en `project-context.md`.
- Prioriza el codigo y la estructura actual del repositorio por sobre documentacion cuando haya contradiccion.

Requisitos de salida:
- Mantener maximo 100 lineas.
- Usar Markdown.
- Incluir frontmatter YAML con:
  - `project_name`
  - `date`
  - `status`
- Titulo: `# AGENTS.md — {project_name}`
- Incluir una referencia corta al contexto completo: `doc/project-context.md`.
- Mantener lenguaje directo, accionable y orientado a agentes.
- Conservar comandos exactos cuando sean importantes.
- Evitar duplicacion interna.

Criterio de corte:
- Conserva solo reglas que:
  - cambian comportamiento del agente;
  - evitan romper arquitectura critica;
  - no son inferibles del codigo;
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
2. `# Guia del Agente`
3. `## Contexto`
   - Contexto completo en `doc/project-context.md`.
4. `## Fuente de verdad`
   - Prioriza codigo y estructura actual del repositorio por sobre documentacion.
5. Secciones compactas adaptadas al stack real del proyecto.

Secciones base:
- `## Stack`
- `## Framework principal` o nombre real del framework.
- `## Arquitectura`
- `## Autorizacion` si aplica.
- `## UI / Frontend` si aplica.
- `## Rutas, Archivos y Nombres`
- `## Mapa Global App` si hay elementos externos, integraciones, servicios, jobs, colas, cron, APIs o dependencias operativas.
- `## Seguridad y Performance`
- `## Tests y Validacion`
- `## Git y Comandos`
- `## Dominio {project_name}`

Adapta o reemplaza secciones:
- Si una seccion no aplica, reemplazala por la equivalente del stack real.
- Si el proyecto usa un framework con restricciones de version o estructura, crea una seccion con el nombre concreto del framework.
- Si hay una capa UI especifica, crea una seccion con su nombre real.
- Si hay reglas de permisos, autenticacion o roles, mantenlas en `Autorizacion`.
- Si hay entidades, flujos o estados de negocio que no deben mezclarse, mantenlos en `Dominio`.

Reglas obligatorias para `## Arquitectura`:
- Siempre incluir: logica de negocio en Models, Services y Controllers; no en vistas.
- Siempre incluir: usar transacciones siempre que se realicen modificaciones en la base de datos.
- Siempre incluir: imports al inicio, en orden alfabetico; no usar FQN dentro del cuerpo.
- Siempre incluir: no introducir frameworks, servicios o tablas nuevas sin decision explicita de arquitectura.
- Siempre incluir: capturar excepciones y loguear con contexto.

Reglas obligatorias para `## Seguridad y Performance`:
- Siempre incluir: no hardcodear secretos, credenciales ni URLs; usar `.env` y documentar placeholders en `.env.example`.
- Siempre incluir: evitar consulta N+1; validar indices para busquedas frecuentes.

Reglas obligatorias para `## Tests y Validacion`:
- Siempre incluir: no ejecutar tests sin pedido explicito del usuario, salvo validacion sintaxis, coherencia y ejecucion del codigo.
- Siempre incluir: si no puedes validar por entorno faltante, dilo explicitamente.

Reglas obligatorias para `## Git y Comandos`:
- Siempre incluir: no ejecutar `git commit`, `git push` ni `git pull` sin pedido explicito.
- Siempre incluir: no commitear `.env`.
- Siempre incluir: validar sintaxis via Docker cuando el proyecto tenga runtime Docker documentado; conservar el comando exacto si aparece en el contexto.

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

Patrones genericos utiles a rescatar cuando aparezcan en el contexto:
- No reintroducir archivos legacy eliminados por el framework actual.
- No duplicar configuracion entre archivos de bootstrap/providers/config.
- Mantener rutas, alias, prefijos y middleware existentes si son consumidos por UI o integraciones.
- No introducir dependencias nuevas sin decision explicita.
- Validar permisos en backend; usar UI solo para condicionar visibilidad.
- No hardcodear IDs ni valores de dominio fragiles.
- Usar helpers seguros para rutas/URLs cuando existan.
- Paginar listados grandes.
- Para tests destructivos o costosos, conservar el comando exacto y el entorno requerido si aparecen en el contexto.
- En cambios sensibles, revisar permisos, filtros, paginacion, eventos UI, N+1 y flujo end-to-end.

Formato:
- Bullets cortos.
- Maximo una idea por bullet.
- Sin consejos genericos como "escribe codigo limpio".
- Sin explicaciones teoricas.
- Sin copiar todo `project-context.md`.
- Sin citas largas.
