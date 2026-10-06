# Análisis refinado de los skills dev-*

Fecha: 2026-10-02. Alcance: análisis estático de las instrucciones locales y sus dependencias BMAD. No se ejecutaron los flujos de entrega ni comparaciones de costo, latencia o calidad. No se modificaron los SKILL.md.

## Conclusión

Los cuatro wrappers requieren subagentes por su contrato actual. Técnicamente un coordinador externo no es indispensable en todas las tareas. Hacerlo opcional es una propuesta de diseño: mientras las instrucciones no cambien, las ejecuciones deben respetar la delegación exigida.

La decisión debe depender de la separación de responsabilidades, el contexto necesario y la capacidad disponible. No existe evidencia aquí para declarar que ejecutar directamente sea siempre superior. Una persona BMAD aporta instrucciones y perspectiva; varias personas en un único agente no equivalen a varios revisores independientes.

## Prioridades anteriores a cambiar la delegación

1. **Integridad canónica — defecto confirmado.** `dev-apply-review/SKILL.md:26` permite modificar solo spec/story y exige un changelog. Para el SPEC.md nativo, `bmad-spec/SKILL.md:55-57,77` requiere registrar cambios en .memlog.md y rederivar el contrato mediante bmad-spec. Debe distinguirse ese formato de una story o spec operativa. Para una spec nativa, permitir las escrituras requeridas a memoria y companions propios, manteniendo el informe de lectura.
2. **Identidad de documentos — omisión de trazabilidad.** `bmad-build/step-01-clarify-and-route.md:23-24` reanuda documentos con status reconocido. El kernel de bmad-spec carece de ese status, por lo que entra como intención y build genera su propia spec operativa. El comando dev-build sobre SPEC.md es válido; no implica marcar ese mismo archivo done. Devolver fuente, spec operativa efectiva y estado.
3. **Companions — riesgo de integración, no pérdida observada.** Exigir que los companions del kernel se lean y que sus restricciones y aceptación se preserven en la spec operativa. La adaptación debe hacer explícito lo que el contrato downstream de bmad-spec exige.
4. **Resultado visible y readiness.** Conservar en la respuesta exterior de build el cambio, pruebas ejecutadas, revisión, diferidos y commit si existe. Al aplicar feedback, distinguir hallazgo refutado de defecto válido pendiente; actualizar readiness exige comprobar el documento resultante. Minor implica LISTO CON CAMBIOS por política actual: no equivale a impedimento para implementar.

## Recomendación por skill

| Skill | Coordinación propuesta | Valor de conservar un coordinador hijo |
|---|---|---|
| dev-spec | Principal conversa y resuelve decisiones; redacción directa o delegada según contexto. | Separar autoría de la comprobación final del principal, especialmente para specs extensas. Mantener la validación existente. |
| dev-review-spec | Principal ejecuta bmad-review y conserva resolución, informe, IDs, severidades y veredicto. | Mantener selección de lentes y resultados fuera de la conversación principal cuando esa separación sea útil. |
| dev-apply-review | Actualizar mediante el escritor correspondiente al formato; modalidad directa o delegada. | Separar edición de comprobación si el principal contrasta IDs con cambios efectivos y alcance. |
| dev-build | Principal coordina bmad-build; delegación interna permanece. Coordinador hijo opcional para una ejecución extensa. | Evitar que diff, investigación, pruebas y triage ocupen toda la conversación principal. |

La coordinación directa de build conserva la separación esencial: el handoff interno requiere implementador sin conversación previa; los revisores también reciben contexto delimitado. El coordinador audita diff, aceptación y pruebas. No es necesario duplicar esas verificaciones solo por retirar la capa externa.

## Capacidad, contexto y límites

- En esta sesión hay cuatro cupos. Si solo están activos principal y coordinador hijo, quedan dos para revisores; sin ese hijo quedan tres. Esto describe capacidad, no velocidad medida. Otros agentes activos reducen esos cupos.
- Programar tandas cuando falte capacidad; no omitir lentes ni controles para compensar una delegación anidada.
- Delegación no garantiza contexto limpio: definir explícitamente qué historial, artefactos y hechos recibe cada agente. Una revisión independiente debe evitar heredar conclusiones del autor innecesariamente.
- Los agentes comparten filesystem. La instrucción de escribir solo ciertos archivos no es aislamiento de permisos; comprobar cambios reales al finalizar.
- El fallback debe respetar cada dependencia: bmad-review permite lentes secuenciales; build permite implementación directa, pero algunas capas de revisión requieren escalamiento humano si no hay subagentes. No prometer un fallback autónomo universal.

## Cómo evaluar antes de fijar un default universal

Comparar ejecución directa y delegada sobre los mismos requisitos y estados iniciales independientes. Incluir una spec pequeña, una extensa con companions, una actualización de feedback y una implementación con revisión. Registrar cumplimiento de requisitos, preservación de memoria/companions, decisiones inventadas, trabajo fuera de alcance, rondas de corrección, evidencia de pruebas, tiempo y consumo reportado por la plataforma. Repetir para evitar decidir a partir de una sola corrida. Esta evaluación se propone; no se ha ejecutado.

## Procedencia

Enrutamiento con bmad-help; primera auditoría con bmad-workflow-builder y revisión arquitectónica; segunda pasada con Winston buscando contraargumentos y un agente centrado en contratos de implementación. Los informes de la primera pasada están en cada `dev-*/.analysis/2026-10-02-delegation/quality-report.md`. Sus calificaciones Good/Fair/Poor son juicios cualitativos del scanner, no resultados de un benchmark.
