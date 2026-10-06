---
name: dev-apply-review
description: Aplicar un informe de review a una spec o story por ID o path, respetar su fuente canónica y registrar hallazgos aplicados, rechazados y pendientes. Usar cuando se solicite aplicar una revisión al documento.
---

# Aplicar una review

## Resolver documentos

Requiere un ID o path de una spec/story Markdown legible. Resuelve paths desde el directorio de trabajo e IDs por nombre e identificador declarado; excluye `.review.md` al buscar la spec/story. Si falta, no existe o hay varias coincidencias, informa el problema y detente sin aproximaciones.

Resuelve el informe en este orden:

1. ID o path proporcionado por el usuario.
2. Referencia explícita en la spec/story; paths relativos desde su carpeta e IDs mediante búsqueda del proyecto.
3. Solo sin referencia interna, archivo vecino que reemplaza `.md` por `.review.md`.

Una referencia explícita inexistente, ilegible o ambigua detiene el proceso; no la sustituyas por el nombre inferido. Si tampoco existe el informe inferido, detente. No generes otra review.

## Elegir el escritor y la coordinación

Comprueba que el informe corresponde al documento y determina su formato por contenido y contexto:

- **Spec nativa de `bmad-spec`:** localiza y lee ese skill; ejecuta su actualización en la carpeta existente. Registra decisiones y cambios en `.memlog.md` mediante su script y deriva `SPEC.md` y companions propios. Conserva IDs y memoria; no parches el kernel ni edites companions adoptados. Si falta la memoria o no se puede determinar la propiedad, informa el impedimento antes de escribir.
- **Story o spec operativa:** respeta su contrato, estructura y campos protegidos. Edita solo el documento resuelto; un cambio de intención congelada requiere la decisión del usuario. Si hay otro escritor canónico, úsalo en lugar de una edición manual.

Ejecuta directamente por defecto; delega para separar edición/comprobación o si se solicita. Consulta `bmad-agent-architect` cuando haya decisiones técnicas. Lee los skills necesarios; sin escritor requerido, detente; sin subagentes, continúa directamente.

La review es de lectura. Para una spec nativa, las escrituras se limitan a su memoria, kernel y companions propios necesarios; no cambies fuentes, configuración, código ni `stories.yaml`. Si una actualización deja stories desalineadas, comunícalo como pendiente. Registra el changelog de esta operación en memoria como evento y entrégalo en la respuesta; no lo agregues al kernel ni a `companions:` como metadata de proceso. En stories/specs operativas, agrega al final "Changelog de review" sin alterar campos protegidos.

Respeta la salida nativa del escritor, incluido el JSON headless de `bmad-spec`; el wrapper prepara su resumen después de leer los artefactos. Al delegar, pasa directorio del proyecto, paths absolutos de documento, review y skills, contexto, formato y límites de escritura. El hijo lee los skills y retorna archivos, IDs y pendientes; retransmite sus preguntas al usuario y sus respuestas al hijo antes del trabajo dependiente.

## Aplicar los hallazgos

Conserva los IDs del informe:

- **Blocker y major:** aplica todos los fundamentados y dentro del alcance autorizado. Si uno requiere decisiones del usuario, pregunta y déjalo pendiente hasta obtener respuesta. Justifica cualquier rechazo en una línea.
- **Minor:** aplica solo si no amplía el alcance; registra también los rechazados por agregar alcance.

Para cada ID registra disposición y motivo: aplicado, rechazado por falso positivo/no aplicabilidad, o pendiente por defecto válido sin resolver. Un defecto válido no se vuelve resuelto por rechazar su propuesta de corrección. No decidas cambios de producto por el usuario.

## Comprobar y entregar

Contrasta cada ID con el cambio efectivo, disposición y alcance. Verifica estructura, referencias, requisitos y changelog; en specs nativas, registro en memoria y derivación por `bmad-spec`. Comprueba archivos modificados: los subagentes comparten filesystem.

Corrige faltantes con el escritor correspondiente o el mismo hijo y verifica otra vez. Devuelve en español enlaces, archivos e IDs aplicados/rechazados/pendientes con motivos; destaca blockers válidos y decisiones pendientes. Si falla, comunica lo completado sin declararlo terminado.

La aplicación no actualiza el veredicto del informe anterior. Recomienda `/dev-review-spec <path-real>` para obtener un nuevo veredicto; no declares readiness solo por el changelog ni inicies esa revisión automáticamente.
