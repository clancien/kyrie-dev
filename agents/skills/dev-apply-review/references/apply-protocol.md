# Protocolo de corrección focalizada y cierre simplificado

Política `apply-focused-v1`, schema 1. Independiente de `full-spec-v1`: no exige review inicial ni activa lentes completas. La review manual es fuente de hallazgos, no certificado heredado. Python 3.10+, stdlib.

`{apply}` es el path absoluto de `scripts/apply_protocol.py` de este skill. `{hashes}` es `scripts/review_protocol.py` de la carpeta instalada de `dev-review-spec`. Esa utilidad se usa **solo para snapshot**, no se activa el skill ni sus comandos de revisión/certificación. El script apply reutiliza esas primitivas de hashing desde su instalación hermana; si falta la utilidad, informa incompletitud. Usa quoting seguro en paths.

## Entrada y estado

Descubre inventario actual completo de documento, companions incluidos adoptados, y dependencias necesarias (memoria en nativas). Declara cada archivo una vez; un hash identifica bytes, no demuestra corrección o cobertura semántica.

```text
python3 {hashes} snapshot <documento> --companion <path> --dependency <path> -o <snapshot.json>
python3 {apply} init <documento> --review <review.md> --snapshot <snapshot.json> --findings <hallazgos.json> --max-rounds 3
python3 {apply} begin <run.json>
```

Repite opciones para cada archivo. `hallazgos.json` es el array extraído del informe proporcionado; agrupa IDs de la misma causa en una key estable. No inventes otra revisión para adaptarlo:

```json
[
  {
    "key": "CAP-2:rechazo-indefinido",
    "severity": "major",
    "finding": "No se define el resultado de rechazo",
    "evidence": "R1 del informe y CAP-2 actual",
    "source_ids": ["R1"]
  }
]
```

`init` archiva informe/JSON existente en `.reviews/<stem>/apply-<id>/` junto al documento, crea `run.json` y D estables. Admite informe Markdown sin metadata vigente; el agente comprueba correspondencia/fundamento antes. No declara ready ni invoca baseline. Corridas antiguas siguen históricas; para continuar requieren migración explícita de presupuesto/hallazgos, no empezar otra para evadir el límite.

`begin` verifica snapshot y consume una tanda antes de escribir; no exige una revisión completa previa. Registra la verificación de una tanda interrumpida antes de reintentar sobre contenido cambiado. No ejecutes escritores o comandos de estado concurrentes.

## Registrar la verificación

Toma snapshot después de los cambios y **antes** de verificar; asegura su vigencia al registrar. `scope` contiene paths absolutos examinados, y la evidencia cita secciones dentro de ellos. En focused incluye archivos/secciones cambiadas y dependencias afectadas; en global incluye todo el inventario actual.

```json
{
  "status": "complete",
  "coverage": "focused",
  "scope": ["/proyecto/spec.md"],
  "findings": [],
  "checked_defects": {
    "D1": {
      "state": "resolved",
      "reason": "La rama de rechazo quedó definida",
      "evidence": "CAP-2, Given/When/Then de rechazo, contrastado con requisito autorizado"
    }
  },
  "pending_decisions": [],
  "failures": []
}
```

```text
python3 {apply} record <run.json> --result <resultado.json> --snapshot <snapshot.json>
python3 {apply} verify <run.json>
```

`findings` usa el mismo schema de entrada, con keys existentes o nuevas. Refutaciones verificadas van en `checked_defects`, no simultáneamente como hallazgos vigentes. Disposiciones: `open`, `applied`, `resolved`, `rejected`, `deferred`; rechazo requiere refutación/no aplicabilidad y evidencia. Solo minor admite deferred. Mayor/bloqueante no se vuelve resuelto por cambiar su key o no aparecer: el ledger lo conserva hasta disposición fundamentada. Cada nueva observación vigente reabre su D; agrupa repeticiones con la key existente y no reabras refutaciones sin evidencia nueva.

Focused requiere una tanda consumida, nunca produce ready y conserva D no examinados. Global completo requiere todo el inventario y disposición actual de **todos** los D previos, incluidos resueltos/rechazados; puede ejecutarse con cero tandas si no hay correcciones. No necesita lentes, booleanos editoriales ni el schema de full-spec-v1.

La única puerta negativa de contenido son major/blocker válidos abiertos. `pending_decisions` se usa para decisiones indispensables ligadas a esos defectos; una preferencia minor no bloquea. El script calcula ready únicamente tras cierre global completo sin major/blocker abiertos. Minor abiertos/diferidos generan observaciones. Global con major/blocker lleva NO LISTO; focused no emite veredicto final.

Si falla el verificador usa `status: incomplete` y `failures` con motivo; no declares un cierre completo. Los fallos técnicos impiden certificar que se completó el trabajo, sin inventar defectos de producto. `record` guarda JSON/Markdown inmutables `check-NNN.focused.*` o `check-NNN.global.*` y actualiza el estado. No toca copias vecinas ni informes manuales.

## Reanudación y paradas

```text
python3 {apply} refresh <run.json> --snapshot <snapshot-actual.json> --reason <cambio-externo-y-evidencia>
python3 {apply} stop <run.json> --status stalled --reason <evidencia>
```

`refresh` conserva presupuesto y D, invalida ready y registra cambios externos; no se usa para escrituras propias sin consumir una tanda. Después reexamina el impacto y realiza cierre global simplificado. Una tanda propia pendiente se registra primero, incluso incompleta.

Stop admite `needs_user`, `incomplete_review`, `stalled`, `budget_exhausted`, nunca ready. Reanuda solo la corrida indicada. Dos tandas sin mejora relevante u oscilación se evalúan semánticamente y justifican stop; el script cuenta tandas, no juzga progreso. `verify` comprueba snapshot y que ready tenga cierre global vigente; el agente confirma además inventario actual y fundamento de disposiciones.

No presentes resultados del cierre simplificado como certificación `full-spec-v1`. Conserva el valor histórico del informe manual y registra tiempo/tokens/costo únicamente cuando estén disponibles, sin afirmar ahorro por el número de rondas.
