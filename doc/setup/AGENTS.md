# Repository Guidelines

## Inicio
- Al comenzar cada sesión, lee este `AGENTS.md` antes de hacer cambios.

## Source Of Truth
- Prioriza el código y estructura actual del repositorio por sobre documentos antiguos.
- No asumas funcionalidades completas solo porque hay dependencias instaladas.
- Cuando haya conflicto entre documentación y comportamiento real, documenta la diferencia y sigue el estado real del sistema.

## Project Structure & Ownership
- Describe aquí los módulos principales (frontend, backend, admin, scripts, docs, etc.).
- Mantén separadas las responsabilidades por capa/superficie.
- Antes de agregar archivos nuevos, revisa si existe un módulo o carpeta donde encaje mejor el cambio.

## Stack & Runtime
- Lenguajes y versiones:
- Frameworks principales:
- Base de datos y servicios externos:
- Forma de ejecución local: (nativa, Docker, etc.)

## Skills
- Usar los skills disponibles en `.agents/skills/index.md` cuando es adecuado.
- Actualiza la lista de skills disponibles y su descripción si haces cambios en ellos.

## Commands
- Comando de arranque local:
- Comando de build:
- Comando de tests:
- Comando de lint/format:
- Comandos de migración o seed (si aplica):

Incluye siempre comandos listos para copiar/pegar y ejecutables desde la raíz del proyecto.

## Do / Don't
Do:
- Mantener coherencia con arquitectura y convenciones existentes.
- Documentar decisiones cuando afecten a más de un módulo.
- Verificar impacto en rutas, config y datos antes de cerrar.

Don't:
- Romper compatibilidad sin advertirlo explícitamente.
- Mezclar cambios no relacionados en el mismo commit.
- Asumir contexto no documentado sin validarlo en el código.
- Ejecutar test unitario sin que se lo pida el usuario.

## Coding Style & Naming
- Respeta convenciones existentes del repositorio antes de proponer nuevas.
- Usa nombres explícitos y consistentes con el módulo (`camelCase`, `PascalCase`, `kebab-case`, etc., según corresponda).
- Mantén funciones/métodos acotados y evita mezclar lógica de negocio con capa de presentación.
- Agrega comentarios solo cuando expliquen intención o reglas no obvias.
- Importa nuevas clases en la sección de declaración inicial del archivo para evitar el uso de package/namespace de las clases en el código.

## Implementation Guardrails
- No introducir frameworks o herramientas nuevas sin necesidad clara.
- No mover lógica de negocio a vistas o templates.
- No hardcodear credenciales, URLs de entorno o secretos.
- Prefiere cambios pequeños, locales y trazables por sobre refactors masivos.

## Testing Guidelines
- Ejecuta pruebas relevantes del módulo afectado antes de cerrar cambios.
- Si no existen tests automáticos, deja validación manual reproducible (pasos concretos).
- Cuando agregues funcionalidad nueva, considera pruebas mínimas de regresión.

## Commit & Pull Request Guidelines
- Commits cortos, imperativos y enfocados en un solo objetivo.
- PRs deben incluir: resumen, paths afectados, impacto técnico, cambios de configuración y validación realizada.
- Si hay cambio visual, incluir evidencia (capturas o descripción clara del resultado).

## Security & Configuration
- Nunca subir secretos, tokens, llaves o credenciales reales.
- Documentar configuración requerida vía variables de entorno.
- Tratar archivos de configuración sensible como material restringido.

## Actualización Operativa
- Cuando el usuario lo solicite, registra decisiones prácticas en este mismo AGENTS.md o propone mejoras uno de los skills disponibles, ademas guarda comandos repetibles y reglas nuevas acordadas durante el trabajo.
- Cuando el usuario lo solicite, o cuando el usuario pide cerrar un issue, tarea o work item; registra decisiones prácticas en doc/bitacora.md, usando la `Plantilla Bitácora Operativa`

### Plantilla Bitácora Operativa    
- Fecha:
- Objetivo de la sesión:
- Cambios realizados:
- Decisiones tomadas:
- Comandos útiles:
- Pendientes: