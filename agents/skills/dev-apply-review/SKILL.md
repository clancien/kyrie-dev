---
name: dev-apply-review
description: Aplicar una review existente con correcciones y verificaciones focalizadas, y cerrar con una revisión global simplificada sin invocar dev-review-spec. Usar cuando se solicite dev-apply-review o aplicar una revisión a una spec o story.
---

# Aplicar una review y verificar las correcciones

## Entrada y límites

Requiere una spec/story Markdown legible e inequívoca por ID o path. Resuelve paths desde cwd e IDs por nombre/identificador; excluye informes, snapshots e historial. Si falta, no existe o es ambiguo, informa el problema y detente.

Resuelve la review: primero la indicada por el usuario; luego la referenciada en el documento (paths relativos desde su carpeta); solo sin referencia explícita, el vecino `.review.md`. Una referencia explícita inválida detiene el proceso, sin fallback. Sin informe previo detente.

La revisión inicial ya se hizo manualmente. **No ejecutes revisión completa inicial, `dev-review-spec`, `bmad-review` ni sus lentes durante este flujo.** Lee el informe existente, comprueba correspondencia y fundamento contra el documento actual, y extrae sus hallazgos. Esa comprobación de entrada no es una nueva review ni exige convertir un informe legacy a `full-spec-v1`.

Lee [references/apply-protocol.md](references/apply-protocol.md). Usa `scripts/apply_protocol.py` para estado/presupuesto y la utilidad de hashing indicada allí. Descubre companions y dependencias desde el contrato actual; incluye memoria de specs nativas. Falta de archivos o herramientas implica `incomplete_review`, no revisión completa automática ni readiness inventada.

## Escritor y coordinación

- **Spec nativa:** lee y ejecuta la actualización de `bmad-spec` en la carpeta existente. Registra cambios en `.memlog.md` con su script y deriva kernel y companions propios; conserva IDs. Sin memoria o propiedad clara, detente antes de escribir. No parches `SPEC.md` ni edites companions adoptados.
- **Story/spec operativa:** respeta contrato, estructura y campos protegidos; edita solo el documento resuelto o usa su escritor canónico. Cambiar intención congelada requiere decisión del usuario.

Un solo escritor modifica producto; el principal coordina y registra estado. Delega editor y verificador con contextos separados si hay capacidad; sin subagentes verifica secuencialmente y declara la limitación. Consulta al arquitecto solo si hay decisiones técnicas relevantes, sin iniciar otros flujos.

La review de entrada queda de lectura. En specs nativas, las escrituras de producto se limitan a memoria, kernel y companions propios necesarios; no cambies fuentes, código, configuración ni `stories.yaml`. Comunica stories desalineadas como pendientes para su consumidor. Changelog en memoria/respuesta, fuera del kernel y `companions:`; en documentos operativos, sección final "Changelog de review". El historial de verificación queda fuera del contrato.

Respeta la salida nativa del escritor, incluido JSON headless; el coordinador lee artefactos antes de resumir. Al delegar, pasa directorio, paths absolutos, decisiones, alcance y límites de escritura. Los hijos no invocan este loop ni revisiones completas. Retransmite preguntas y respuestas del usuario antes del trabajo dependiente.

## Iniciar y corregir

Por defecto hay **tres tandas de corrección**, consumidas antes de escribir, incluyendo reintentos y correcciones del cierre. Solo el usuario cambia el límite; no lo amplíes para obtener verde. Verificaciones y cierre no consumen tandas; una entrada sin defectos relevantes puede llegar al cierre con cero tandas.

1. Archiva el informe existente y toma snapshot actual; inicia el protocolo con los hallazgos extraídos, sin baseline completa. Agrupa observaciones por causa raíz con keys estables y conserva los R de origen; el script asigna D estables.
2. Corrige blocker/major fundamentados dentro del alcance. Minor solo si no amplían alcance ni requieren tandas de pulido. Registra refutaciones con evidencia; rechazar una solución no resuelve un defecto válido ni autoriza rebajar su severidad.
3. Si falta una decisión indispensable, pregunta y conserva `needs_user`; clasifica la ambigüedad que impediría implementar como major/blocker con consecuencia concreta. Continúa solo correcciones independientes autorizadas. Preferencias opcionales/minor no impiden el cierre.
4. Ejecuta `begin` antes de cada tanda y usa el escritor canónico. Agrupa cambios relacionados. Una tanda interrumpida sigue consumida; registra su verificación/incompletitud antes de reintentar sobre archivos cambiados.
5. Ejecuta la verificación focalizada siguiente. Si persisten major/blocker y hay progreso, repite dentro del presupuesto. Si ya no quedan, pasa al cierre global. No prolongues por minor.

## Verificación focalizada por tanda

Revisa los hallazgos corregidos, todas las secciones/archivos modificados y las dependencias afectadas. Usa diff, snapshots e intención autorizada para delimitar impacto. Incluye cambios indirectos de derivación en otros companions; amplía el ámbito cuando una regla, API, modelo o flujo compartido los afecte. No repitas lentes ni releas todo el contrato por rutina.

Un verificador contrasta cada ID afectado con el cambio real y evidencia localizable: resuelto, rechazado por falso positivo/no aplicabilidad, aplicado pero no verificado, abierto o minor diferido. Comprueba preservación y regresiones en ese ámbito. "Aplicado" y ausencia en una tabla no cierran D; las disposiciones verificadas sí. Un hallazgo nuevamente fundamentado reabre D.

Registra `coverage: focused`, ámbito, hallazgos, disposiciones y snapshot. Una verificación focalizada limpia **no declara ready**. Defectos no examinados conservan su estado. Si no se puede completar la verificación, guarda checkpoint incompleto sin inventar aprobación.

## Cierre global simplificado

Después del último cambio, lee **toda la versión final** del documento, companions actuales y dependencias de intención necesarias. Usa una sola comprobación global, preferentemente con verificador distinto del editor; no ejecutes `dev-review-spec`, `bmad-review`, fan-out de lentes ni cuotas de hallazgos.

Comprueba coherencia de comportamiento, requisitos preservados, aceptación, referencias, decisiones y campos protegidos. Recontrasta todos los D previos con evidencia, incluso los ya resueltos o rechazados. No rehagas correcciones de estilo ni exijas perfección editorial.

**Bloquea por contenido solo con major/blocker válidos abiertos.** Una carencia de aceptación, referencia o decisión indispensable bloquea únicamente si implica un defecto relevante concreto, registrado como major/blocker con localización y consecuencia. Minor y mejoras opcionales se informan sin bloquear ni provocar otra tanda.

Registra `coverage: global` sobre el inventario completo actual. Sin major/blocker abiertos, entrega `ready` y `LISTO` o `LISTO CON OBSERVACIONES`. Si aparecen defectos relevantes, vuelve a corregir y verificar focalizadamente dentro del presupuesto, y realiza un nuevo cierre tras el último cambio. Fallos técnicos, contenido ilegible o cambios concurrentes dejan el cierre incompleto; no son un veredicto negativo de contenido ni permiten declarar ready.

## Paradas y entrega

Estados: `active`, `ready`, `needs_user`, `incomplete_review`, `stalled`, `budget_exhausted`. Detén por límite, oscilación o dos tandas sin mejora verificable de defectos relevantes. Registra causas y evidencia, no solo conteos. Reanuda solo una corrida identificada, conservando D, historial y presupuesto. Cambios externos invalidan cierre y exigen reexaminar el impacto más un nuevo cierre simplificado, nunca una baseline completa automática; usa `refresh` con motivo. No migres/resetées silenciosamente corridas de política antigua.

Ejecuta `verify` antes de comunicar ready y comprueba archivos realmente escritos. Entrega en español estado/razón, documento, informe de entrada, verificación final y corrida, tandas usadas/límite, D/R y sus disposiciones, decisiones y próximo paso. Identifica el cierre como **simplificado**, no como una certificación completa de `dev-review-spec`; no declares ahorros medidos sin evidencia.

No cambies el veredicto ni las copias vecinas de la review manual. Guarda verificaciones en el historial propio de apply. `ready` permite proponer `/dev-build <path-real>` sin iniciarlo automáticamente. Una parada entrega checkpoint reanudable.
