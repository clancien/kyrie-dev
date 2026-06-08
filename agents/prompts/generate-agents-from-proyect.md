Genera un archivo AGENTS.md basado en el contenido de project-context.md.

Objetivo:
Crear una versión operativa corta para agentes AI.

Requisitos:
- Mantener máximo 100 líneas.
- Usar Markdown.
- Incluir frontmatter YAML con:
  - project_name
  - date
  - status
- El primer párrafo debe indicar que project-context.md es la fuente de verdad.
- No copiar todo project-context.md: resumir solo reglas críticas, no obvias o con riesgo de romper el proyecto.
- Mantener lenguaje directo, accionable y orientado a agentes.
- Evitar duplicación interna.
- Conservar comandos exactos cuando sean importantes.
- No inventar stack, versiones, rutas ni convenciones que no aparezcan en project-context.md.

Estructura requerida:

1. Frontmatter
2. Título: `# AGENTS.md — {project_name}`
3. Fuente de Verdad: Prioriza el código y estructura actual del repositorio por sobre documentación.
4. Contexto Completo App: `doc/project-context.md`
5. Secciones:
   - `## Stack`
   - `## Laravel 13` o framework principal equivalente
   - `## Arquitectura`
   - `## Autorización`
   - `## Livewire 3` o capa UI equivalente
   - `## Mapa Global App` incluyando todos los elementos externos del sistema
   - `## Seguridad y Performance`
   - `## Tests y Validación`
   - `## Git y Comandos`
   - `## Dominio {project_name}`

Reglas de síntesis:
- Usa bullets cortos.
- Agrupa reglas similares.
- Elimina explicaciones largas.
- Si una sección no aplica al proyecto, reemplázala por la equivalente del stack real.
- Prioriza:
  - comandos que el agente debe o no debe ejecutar
  - rutas críticas
  - convenciones de archivos
  - restricciones de framework
  - reglas de autorización
  - reglas de dominio
  - validaciones obligatorias
  - riesgos de seguridad/performance

Entrada:
A continuación está el contenido completo de project-context.md:

```markdown
{PEGAR_AQUI_PROJECT_CONTEXT_MD}