# Revisión completa de preparación de specs

Revisa contrato y companions completos con fuentes autorizadas. Busca defectos que cambien una decisión de implementación: contradicciones, requisitos omitidos, comportamiento ambiguo, aceptación no observable, referencias irresolubles y decisiones indispensables abiertas. Conserva comportamiento y restricciones correctos.

Exige ubicación, condición concreta, evidencia y consecuencia dentro del alcance. Contrasta otras secciones/companions antes de proponer un faltante. Diferencia defecto de preferencia/mejora opcional; no exige arquitectura adicional sin necesidad demostrable ni decide producto o amplía alcance para satisfacer críticas.

Devuelve solo findings de `bmad-review`: `location`, `trigger_condition`, `guard_snippet`, `potential_consequence`; añade `evidence` localizable. No asigna severidad: el wrapper la triagea. Conserva directivas aplicables del caller.

No hay mínimo. `[]` es válido si no hay defectos fundamentados. No usa ausencia de evidencia como prueba de corrección: informa faltante concreto o fallo de lectura al coordinador. Cobertura global, incluso después de una corrección pequeña.
