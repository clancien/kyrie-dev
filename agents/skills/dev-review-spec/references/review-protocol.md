# Protocolo de revisión completa y corridas full-spec históricas

Política `full-spec-v1`, schema 1. Este protocolo rige la revisión completa manual de `dev-review-spec` y conserva los comandos de corridas full-spec anteriores. El loop actual de `dev-apply-review` usa su propio `references/apply-protocol.md` (`apply-focused-v1`): no requiere baseline completa ni ejecuta estas rondas. Los comandos usan Python 3.10+ y stdlib. `{protocol}` es el path absoluto de `scripts/review_protocol.py` de la carpeta instalada de `dev-review-spec`; no se resuelve desde cwd. `python3 {protocol} --help` documenta la interfaz. Paths y argumentos se pasan con quoting seguro. Si la utilidad no puede ejecutarse, entrega incompletitud; no simules hashes ni presupuesto verificado.

## Snapshot y reporte

El lector descubre el inventario actual de companions desde el contrato, incluyendo adoptados, y las dependencias de intención necesarias. El script no interpreta frontmatter ni significado: un manifiesto que omite un companion no demuestra cobertura. Nativas requieren memoria legible; stories siguen sus fuentes y campos protegidos. Cada archivo se declara una sola vez, con prioridad documento > companion > dependencia.

```text
python3 {protocol} snapshot <documento> --companion <companion> --dependency <fuente-o-memoria> -o <snapshot.json>
python3 {protocol} report <resultados.json> --snapshot <snapshot.json> -o <round-NNN.review.md> --latest <vecino.review.md>
python3 {protocol} verify <round-NNN.review.json>
```

Repite opciones de companions/dependencias; omite las que no apliquen. Snapshot temporal se toma **antes** de revisar. `report` verifica que todos esos bytes sigan vigentes, renderiza Markdown y JSON en el path histórico exclusivo y publica copias vecinas solo si la revisión está completa. Archivos históricos nunca se sobreescriben. Verificar hashes no sustituye comprobar inventario, aceptación ni verdad de hallazgos.

`resultados.json` mínimo:

```json
{
  "status": "complete",
  "coverage": "full",
  "required_lenses": ["adversarial", "edge-case-hunter"],
  "executed_lenses": ["adversarial", "edge-case-hunter"],
  "checks": {
    "requirements_preserved": true,
    "acceptance_observable": true,
    "references_resolved": true,
    "decisions_resolved": true
  },
  "pending_decisions": [],
  "failures": [],
  "exclusions": [],
  "excluded_findings": [],
  "findings": [
    {
      "id": "R1",
      "severity": "major",
      "section": "CAP-2 / aceptación",
      "finding": "El resultado de un rechazo no está definido",
      "correction": "Especificar el estado y respuesta de rechazo",
      "evidence": "CAP-2 define éxito, pero no su rama de rechazo",
      "consequence": "Dos implementaciones pueden devolver respuestas incompatibles",
      "lenses": ["edge-case-hunter"]
    }
  ]
}
```

Las listas de lentes son las realmente seleccionadas/ejecutadas, no siempre las del ejemplo. Cada check es un juicio contrastado con las fuentes; no asumir `true` porque la lista de findings está vacía. Check falso impide readiness, aunque no haya tabla de defectos. Registra localización, explicación y corrección de ese faltante en findings o pending_decisions para guiar la tanda; no crear trabajo sin evidencia. Descartes: `excluded_findings` contiene objetos `finding`, `reason`, `evidence`; `exclusions` documenta lentes omitidas por aplicabilidad/selección.

Si falla una lente requerida, usa `status: incomplete` y `failures` con razones; conserva hallazgos obtenidos, sin veredicto final. Una lista de findings vacía es válida. El script calcula `ready_for_dev` y `verdict`; no acepta elegirlos. Complete requiere todas las lentes requeridas ejecutadas, sin failures. Readiness requiere todos los checks, ausencia de decisiones abiertas y cero blocker/major.

## Corrida, identidad y reconciliación

```text
python3 {protocol} init <documento> --review <entrada.review.md> --max-rounds 3
python3 {protocol} adopt <entrada.review.json> -o <run-folder>/round-000.review.md
python3 {protocol} record <run.json> --review <round-000.review.json> --reconcile <reconcile.json>
python3 {protocol} begin <run.json>
```

`init` genera carpeta única `.reviews/<stem>/<run-id>/` junto al documento y archiva entrada y JSON vecino si existe. No afirma correspondencia ni readiness de esa entrada. `adopt` reutiliza solo un informe vigente completo de esta política, con mismos requisitos de cobertura. Si es legacy, obsoleto, parcial o no corresponde, conserva la entrada y ejecuta baseline completa nueva. Ni legacy ni informe de otro documento autorizan cambios.

Cada `begin` verifica review vigente y consume una tanda **antes** de que el escritor modifique archivos. No resetea el límite al reanudar; un intento fallido sigue contado. Una revisión tras los cambios no consume otra tanda. Antes de reintentar una escritura con contrato cambiado, necesita una review completa vigente de ese contrato. No ejecutar varios escritores/comandos de estado concurrentes.

`record` rechaza snapshot cambiado sin intento consumido pendiente. Para cambios externos observados registra primero `stop ... --status incomplete_review --reason <cambio-externo>`, revisa completamente la entrada actual y registra con `record ... --refresh-reason <origen-y-evidencia-del-cambio-externo>`. Conserva tandas y evento; nunca se usa para una corrección propia no contabilizada ni para ampliar presupuesto. Retriage del mismo snapshot no requiere tanda. Registra solo JSON histórico, nunca la copia vecina mutable.

Después de cada revisión usa `record` con reconciliación del coordinador/verificador:

```json
{
  "keys": {"R1": "CAP-2:resultado-de-rechazo-indefinido"},
  "dispositions": {},
  "metrics": {"duration_seconds": 42.5, "tokens": null, "cost": null},
  "observations": "Revisión completa; aceptación y estados comparten secciones"
}
```

Asigna una key estable por causa raíz/requisito, no por número de línea o frase. Distintas observaciones de la misma causa pueden compartir key. El script asigna D1… en orden y conserva `(review_id, Rn, lentes, evidencia)`; R1 de otra ronda no se confunde. Lee el ledger antes de asignar keys nuevas; matching semántico es juicio del coordinador.

Para cerrar un D que dejó de aparecer, el verificador debe contrastar la corrección y preservación, no solo la ausencia en tabla:

```json
{
  "keys": {},
  "dispositions": {
    "D1": {
      "state": "resolved",
      "reason": "El contrato define la rama pendiente",
      "evidence": "CAP-2 Given/When/Then de rechazo, contrastado con el requisito autorizado"
    }
  },
  "metrics": {"duration_seconds": 39, "tokens": null, "cost": null}
}
```

Estados de defecto: `open`, `applied`, `resolved`, `rejected`, `deferred`. `applied` no cierra. `rejected` requiere evidencia de falso positivo/no aplicabilidad; rechazar una solución a un defecto válido lo mantiene open. Solo minor admite deferred. Un D resolved observado otra vez se reabre. Un D rejected conserva su rechazo salvo que el verificador aporte `reopen_rejected: {"D1": {"reason": "premisa cambiada", "evidence": "referencia a evidencia nueva"}}` en reconciliación. No ignorar un defecto nuevamente fundamentado ni reabrir falsas alarmas por redacción repetida. El script no baja severidades automáticamente.

Si un hallazgo actual se refuta después de renderizar, devuelve la evidencia al triage para emitir un reporte corregido nuevo sobre el mismo snapshot (misma cobertura, sin otra tanda de escritura). El informe final y el ledger deben coincidir: rechazar un major en ledger no vuelve positivo el reporte que todavía lo declara major. Conserva ambas versiones y el motivo. Una corrección de metadata no es permiso para omitir revisión o modificar producto fuera del presupuesto.

`record` guarda paths, hashes, coverage, diferencia de archivos entre snapshots y métricas disponibles, y deriva estado. Defectos anteriores no desaparecen porque el informe nuevo esté limpio. Con tres tandas consumidas y requisitos abiertos devuelve budget_exhausted. Checks/decisiones/fallos también impiden ready. Independencia del juicio, inventario completo y fundamento no pueden demostrarse solo mediante schema; son obligaciones de los skills.

```text
python3 {protocol} stop <run.json> --status stalled --reason <evidencia-de-no-progreso-u-oscilacion>
python3 {protocol} stop <run.json> --status incomplete_review --reason <fallo-o-cambio-concurrente>
```

Stop admite además needs_user y budget_exhausted; nunca ready. La falta de progreso se evalúa por defecto/decisión y evidencia, no por cantidad de comentarios. Antes de entregar ready, `verify` comprueba de nuevo la última review e inventario actual; si hay cambio, registra stop/incomplete_review y requiere revisión nueva. El estado técnico no se incorpora al kernel ni a companions.

## Mediciones y alcance

`full-spec-v1` certifica únicamente revisiones completas. No etiquetes verificaciones focalizadas de apply como informes full-spec ni reutilices su cierre simplificado como este certificado. El cambio explícito del usuario habilita `apply-focused-v1` en el skill de aplicación, conservando esta revisión manual. Tiempo/tokens/costo solo se registran si están disponibles; un ahorro no se demuestra por ejecutar menos rondas.
