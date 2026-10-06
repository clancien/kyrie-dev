# Validación de los skills dev-*

Fecha: 2026-10-02. Alcance: cuatro SKILL.md y metadata UI de dev-spec. Se aplicaron los hallazgos del análisis de delegación y se condensó la redacción, conservando entradas, decisiones, límites y resultados. Las instrucciones BMAD de terceros y la configuración del proyecto no se modificaron.

## Cumplimiento comprobado

| Contrato | Resultado |
|---|---|
| Entrada obligatoria; resolución por path/ID; documentos legibles e inequívocos | Conservado en los cuatro flujos; dev-spec admite requerimiento en texto. |
| Dependencias reales leídas; salida nativa y configuración BMAD respetadas | Explícito; retorno headless del escritor separado del resumen del wrapper. |
| Coordinador externo opcional; delegaciones internas y fallback específicos | Corregido; cupos y tandas sin omitir controles ni prometer autonomía universal. |
| Preguntas sobre decisiones, sin inventar producto ni repetir hechos verificables | Conservado; retransmisión principal/hijo antes del trabajo dependiente. |
| Spec con kernel, memoria, IDs, companions, aceptación y exclusiones | Conservado; comprobación del contexto y artefactos completos. |
| Plan/modalidad en respuesta y prompts verificados, sin crear stories o implementar | Conservado; metadata operativa fuera del kernel y companions. |
| Review sobre documento y companions; escritura limitada al informe | Corregido; temporales permitidos, contrato completo en cada lente. |
| Tabla, IDs, severidades y reglas de veredicto | Conservado; cobertura explícita y sin veredicto ante fallos/incompletitud. |
| Prioridad de review explícita, referencia interna, vecino inferido | Conservado; referencia explícita inválida no permite fallback. |
| Actualización mediante escritor canónico; memoria append-only y derivación | Corregido; fuente/review/companions adoptados protegidos. |
| Aplicación por severidad, rechazo fundamentado y pendientes reales | Conservado y aclarado; rechazar una propuesta no resuelve un defecto válido. |
| Changelog según formato y ausencia de readiness automática | Corregido; memoria/respuesta para kernel, sección final para operativo. |
| Build diferencia contrato fuente de spec operativa y preserva companions | Corregido; paths efectivos y trazabilidad en entrega. |
| Evidencia de pruebas/revisión, comandos ejecutados vs propuestos, diferidos y commit | Ampliado; done solo al completar la ruta y sus controles. |
| Límites de modificación y comprobación real de archivos | Explícito; delegación no se trata como aislamiento del filesystem. |
| Metadata de descubrimiento coherente y política de invocación intacta | Actualizada descripción UI de dev-spec; conservados nombre y prompt. |

## Verificaciones

- `skill-creator/scripts/quick_validate.py`: los cuatro skills válidos.
- `git diff --check`: sin errores de whitespace.
- Revisión independiente contra bmad-spec, bmad-review y rutas/configuración de bmad-build: se corrigió la ubicación de recomendación/plan y se confirmó ausencia de defectos fundamentados pendientes en la versión final.
- Segunda revisión de preservación: confirmó separación entre JSON headless y resumen del wrapper; cambios aplicados.
- Simulación estática de escenarios: spec UI con intención suficiente; companion ausente; lente requerida fallida; review explícita ausente con vecino existente; actualización nativa con companion adoptado y decisión pendiente; kernel sin status; operativo ready-for-dev sin subagentes. Las rutas resultantes respetan límites, decisiones y escalaciones.

## Límite de la conclusión

Los 16 contratos anteriores se verificaron documentalmente. No se ejecutaron workflows completos, implementaciones, hooks personalizados ni servicios externos. Validación estructural y simulación estática no garantizan comportamiento perfecto en toda ejecución futura; no hay resultados de benchmark de calidad, tiempo o costo.
