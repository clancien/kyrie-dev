Genera `doc/project-context.md` a partir del codigo fuente existente de este proyecto.

Objetivo:
Crear un documento de contexto tecnico-operativo que permita a agentes AI entender el proyecto antes de modificarlo: arquitectura real, stack, convenciones, comandos, riesgos, restricciones y reglas de trabajo verificadas desde el repositorio.

Este prompt es portable:
- Todo dato debe salir del codigo, configuracion, scripts, documentacion local o evidencia observable del proyecto objetivo.

Agentes BMAD a activar o simular:
- `bmad-generate-project-context`: agente principal. Coordina la generacion del contexto y produce `doc/project-context.md`.
- `bmad-document-project`: documenta proyectos brownfield desde codigo fuente existente y ayuda a convertir hallazgos en documentacion util para agentes.
- `bmad-agent-architect`: identifica arquitectura, limites entre capas, patrones, decisiones tecnicas, integraciones y riesgos estructurales.
- `bmad-agent-dev`: inspecciona codigo, comandos, pruebas, scripts, dependencias, flujos de ejecucion y convenciones reales.
- `bmad-agent-analyst`: extrae dominio, usuarios, entidades, procesos, reglas de negocio y workflows visibles en el sistema.
- `bmad-agent-tech-writer`: sintetiza el resultado en Markdown claro, accionable, de alta senal y sin relleno.

Si algun agente BMAD no esta disponible:
- Continua simulando su rol con el mismo criterio.
- Indica en la seccion `## Evidencia y Limitaciones` que el agente no estuvo disponible.
- No bloquees la generacion si el codigo fuente puede inspeccionarse.

Reglas de entrada:
- Ejecutar desde la raiz del proyecto objetivo.
- Inspeccionar el proyecto como brownfield: el codigo existente es la fuente principal de verdad.
- Priorizar codigo y configuracion versionada por sobre README, wiki o comentarios cuando haya contradicciones.
- No inventar framework, version, comandos, endpoints, modelos, roles, integraciones ni reglas de negocio.
- No incluir secretos, tokens, credenciales ni valores sensibles. Si aparecen, reportar solo el riesgo y la ruta general.
- No ejecutar acciones destructivas, migraciones, seeders, deploys, comandos de escritura contra servicios externos, `git commit`, `git push`, `git pull` ni instalaciones globales.
- No modificar codigo fuente para generar el documento, salvo crear o actualizar `doc/project-context.md`.
- Si falta informacion critica, marcarla como `No verificado` o `No encontrado`, no completarla por intuicion.

Proceso obligatorio:

1. Orientacion inicial del repositorio
   - Identifica raiz del proyecto, nombre probable, tipo de aplicacion y estructura principal.
   - Lista archivos de configuracion relevantes: package managers, Docker, CI, framework, linters, test runners, env examples, monorepo config.
   - Detecta si es monorepo, multi-app, package unico, backend, frontend, full-stack, libreria, CLI, mobile, infraestructura o mezcla.

2. Inventario de stack y runtime
   - Detecta lenguajes, frameworks, librerias principales, base de datos, cola, cache, servicios externos, runtime y gestores de paquetes.
   - Extrae versiones solo desde archivos verificables: lockfiles, manifests, tool config, Dockerfiles, CI o docs locales confiables.
   - Distingue dependencias productivas, dev tooling y dependencias transitorias cuando sea relevante.

3. Mapa de arquitectura
   - Describe carpetas principales y responsabilidad de cada una.
   - Identifica capas: UI, API, dominio, servicios, jobs, workers, persistence, infra, adapters, shared, tests.
   - Identifica patrones reales: MVC, hexagonal, modular monolith, microservices, server components, event-driven, CQRS, ORM, repository, service layer, etc.
   - Explica limites importantes y reglas que un agente debe respetar al cambiar codigo.

4. Dominio y comportamiento del sistema
   - Extrae entidades, conceptos, roles, permisos, estados, workflows y reglas de negocio desde codigo, tests, rutas, schemas, factories, migrations, seeders y docs.
   - Señala invariantes: cosas que no deben mezclarse, estados que requieren transiciones validas, autorizaciones que deben mantenerse, reglas de calculo o validacion.
   - Si el dominio no puede inferirse con confianza, dilo explicitamente.

5. Superficies de entrada y salida
   - Documenta rutas HTTP, CLI commands, jobs, cron, queues, webhooks, scheduled tasks, eventos, public APIs, GraphQL, RPC o integraciones si existen.
   - Para UI, documenta rutas, layouts, componentes principales, flujo de navegacion, estado global y convenciones de diseño solo si son verificables.
   - Para librerias o paquetes, documenta API publica, entrypoints y contratos de uso.

6. Datos, persistencia e integraciones
   - Identifica base de datos, ORM, migrations, schemas, modelos, indices visibles, transacciones y patrones de acceso.
   - Registra integraciones externas, variables de entorno requeridas, storage, email, pagos, analytics, auth providers, feature flags, observabilidad.
   - No expongas valores reales de secretos. Usa nombres de variables y placeholders.

7. Comandos operativos
   - Extrae comandos exactos para instalar, ejecutar, testear, lint, build, format, migrar, seed, storybook, e2e, docker y CI.
   - Indica la fuente de cada comando cuando sea posible: `package.json`, `Makefile`, `README`, CI, scripts.
   - Diferencia comandos seguros de comandos destructivos o dependientes de entorno.
   - Si un comando no se puede validar sin riesgo, documentalo como no ejecutado.

8. Calidad, testing y validacion
   - Identifica frameworks de test, ubicacion de tests, convenciones de nombres, fixtures/factories y comandos.
   - Resume que debe validarse antes/despues de cambios comunes.
   - Señala gaps visibles: no hay tests, tests parciales, ausencia de lint, CI inexistente, comandos ambiguos.

9. Seguridad, performance y riesgos
   - Revisa patrones visibles de auth, permisos, sanitizacion, validacion, CORS, CSRF, rate limiting, secrets, logging, uploads, SSRF, SQL/NoSQL injection, XSS.
   - Revisa riesgos de performance: N+1, paginacion, indices, cache, queries pesadas, bundles, imagenes, background work.
   - Reporta riesgos con evidencia, no como auditoria especulativa.

10. Sintesis y escritura
   - Crea o actualiza `doc/project-context.md`.
   - Si `doc/project-context.md` existe, leelo primero para recopilar información relevante.
   - Usa Markdown.
   - Mantén lenguaje directo, tecnico y accionable para agentes AI.
   - Incluye solo informacion que cambie decisiones de implementacion, validacion o investigacion futura.

Estructura requerida de `doc/project-context.md`:

```markdown
---
project_name: "{nombre_verificado_o_probable}"
generated_at: "{fecha_iso}"
source: "existing source code"
status: "{draft|verified|partial}"
confidence: "{high|medium|low}"
---

# Project Context - {project_name}

## Resumen Ejecutivo

## Evidencia y Limitaciones

## Stack y Runtime

## Estructura del Repositorio

## Arquitectura

## Dominio y Reglas de Negocio

## Superficies de Entrada y Salida

## Datos y Persistencia

## Integraciones y Variables de Entorno

## Comandos

## Testing y Validacion

## Seguridad

## Performance y Escalabilidad

## Convenciones para Agentes AI

## Riesgos y Puntos Fragiles

## Preguntas Abiertas
```

Adaptacion de secciones:
- Si una seccion no aplica, mantenla con `No aplica` o reemplazala por una seccion equivalente mas precisa.
- Si el proyecto es monorepo, agrega `## Workspaces / Paquetes`.
- Si hay frontend relevante, agrega `## Frontend y UI`.
- Si hay mobile, agrega `## Mobile`.
- Si hay infraestructura significativa, agrega `## Infraestructura y Deploy`.
- Si hay APIs publicas, agrega `## Contratos Publicos`.
- Si hay autorizacion compleja, agrega `## Autenticacion y Autorizacion`.

Contenido esperado por seccion:

`## Resumen Ejecutivo`
- Que es el proyecto.
- Para que sirve.
- Tipo de sistema.
- Stack principal.
- Restricciones mas importantes para agentes AI.

`## Evidencia y Limitaciones`
- Archivos y carpetas inspeccionadas.
- Archivos no encontrados o informacion no verificable.
- Comandos ejecutados y comandos evitados.
- Agentes BMAD usados o simulados.

`## Stack y Runtime`
- Lenguajes, frameworks, runtime, package managers, version managers.
- Bases de datos, cola, cache, storage, servicios externos.
- Versiones verificadas con fuente.

`## Estructura del Repositorio`
- Mapa de carpetas principales.
- Responsabilidad de cada carpeta.
- Entry points.
- Ubicacion de configuracion, tests, scripts y assets.

`## Arquitectura`
- Patron arquitectonico real.
- Flujo de datos.
- Separacion de responsabilidades.
- Dependencias entre capas.
- Reglas que deben respetarse antes de mover logica o introducir abstracciones.
- Siempre incluir: logica de negocio en Models, Services y Controllers; no en vistas.
- Siempre incluir: usar transacciones siempre que se realicen modificaciones en la base de datos.
- Siempre incluir: imports al inicio, en orden alfabetico; no usar FQN dentro del cuerpo.
- Siempre incluir: no introducir frameworks, servicios o tablas nuevas sin decision explicita de arquitectura.
- Siempre incluir: capturar excepciones y loguear con contexto.

`## Dominio y Reglas de Negocio`
- Entidades y conceptos principales.
- Roles, permisos, estados y transiciones.
- Reglas de validacion.
- Workflows criticos.
- Invariantes que no deben romperse.

`## Superficies de Entrada y Salida`
- Rutas HTTP, controllers, pages, endpoints, CLI, jobs, queues, cron, webhooks, events, APIs publicas.
- Contratos observables: request/response, schemas, DTOs, commands, events.
- Consumidores internos o externos si son verificables.

`## Datos y Persistencia`
- ORM o capa de datos.
- Modelos, migrations, schemas, seeds.
- Relaciones, indices visibles, constraints.
- Uso de transacciones.
- Riesgos de consistencia.

`## Integraciones y Variables de Entorno`
- Variables de entorno requeridas con placeholders.
- Servicios externos.
- Configuracion local vs produccion.
- Riesgos por secretos o dependencias externas.

`## Git y Comandos`
- Tabla con columnas: `Proposito`, `Comando`, `Fuente`, `Notas`.
- Incluir instalar, dev, build, test, lint, format, docker, migrations, seed, e2e si existen.
- Marcar comandos destructivos o dependientes de entorno.
- Siempre incluir: no ejecutar `git commit`, `git push` ni `git pull` sin pedido explicito.
- Siempre incluir: no commitear `.env`.
- Siempre incluir: validar sintaxis via Docker cuando el proyecto tenga runtime Docker documentado; conservar el comando exacto si aparece en el contexto.

`## Testing y Validacion`
- Frameworks de test.
- Tipos de pruebas presentes.
- Ubicacion de tests.
- Como correr validaciones.
- Validaciones minimas recomendadas para cambios comunes.
- Gaps de cobertura verificables.
- Siempre incluir: no ejecutar tests sin pedido explicito del usuario, salvo validacion sintaxis, coherencia y ejecucion del codigo.
- Siempre incluir: si no puedes validar por entorno faltante, dilo explicitamente.

`## Seguridad`
- Auth, autorizacion, validacion, secrets, input handling, uploads, logging, permisos.
- Riesgos observados con evidencia.
- Reglas obligatorias para cambios sensibles.
- Siempre incluir: no hardcodear secretos, credenciales ni URLs; usar `.env` y documentar placeholders en `.env.example`.
- Siempre incluir: evitar consulta N+1; validar indices para busquedas frecuentes.


`## Performance y Escalabilidad`
- Puntos de carga, queries, paginacion, cache, colas, jobs, bundles, imagenes.
- Riesgos observados.
- Reglas practicas para evitar regresiones.

`## Convenciones para Agentes AI`
- Reglas compactas que cambian comportamiento del agente.
- Donde poner logica nueva.
- Que comandos puede correr y cuales requieren permiso.
- Rutas y archivos que no debe tocar sin contexto.
- Convenciones de nombres, imports, errores, logging, tests.
- Reglas de git: no hacer commit, push o pull sin pedido explicito.
- Reglas de secretos: no leer ni exponer `.env` si contiene valores reales; usar `.env.example` o nombres de variables.

`## Riesgos y Puntos Fragiles`
- Lista priorizada de areas donde cambios pueden romper comportamiento.
- Incluir evidencia: archivo, patron, comando, dependencia o flujo.
- Separar riesgo confirmado de sospecha razonable.

`## Preguntas Abiertas`
- Solo preguntas que bloquean decisiones futuras.
- No incluir preguntas cuya respuesta pueda obtenerse inspeccionando mas codigo.

Reglas de estilo:
- Escribe en español salvo que el proyecto objetivo este claramente documentado en otro idioma y se pida conservarlo.
- Se directo y especifico.
- Usa bullets y tablas cuando mejoren lectura.
- Evita teoria, buenas practicas genericas y tutoriales.
- Evita frases vagas como "seguir buenas practicas" o "mantener codigo limpio".
- Cada afirmacion tecnica importante debe poder rastrearse a evidencia local.
- Usa rutas relativas desde la raiz del proyecto.
- No copies archivos completos.
- No cites bloques largos de codigo.
- No incluyas secretos ni datos personales.

Reglas de evidencia:
- Para hechos criticos, incluye rutas o fuentes entre parentesis.
- Si algo se infiere, dilo: `Inferido desde ...`.
- Si hay contradiccion entre fuentes, registra la contradiccion y prioriza codigo/configuracion vigente.
- Si solo aparece en README y no en codigo/config, marca como documentado pero no verificado.

Checklist de finalizacion:
- `doc/project-context.md` existe.
- El documento no depende de conocimiento externo al proyecto objetivo.
- El documento no contiene secretos.
- Las versiones y comandos tienen fuente local.
- Las limitaciones estan declaradas.
- Las reglas para agentes AI son accionables.
- Las preguntas abiertas no son reemplazo de investigacion basica.

Salida final al usuario:
- Indica que `doc/project-context.md` fue creado o actualizado.
- Resume en 5 bullets maximo las areas cubiertas.
- Menciona comandos ejecutados para inspeccion o validacion.
- Menciona limitaciones o informacion no verificada.
