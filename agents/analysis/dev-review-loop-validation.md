# Implementación del loop obligatorio de dev-apply-review

Fecha: 2026-10-06. Implementado conforme a la elección explícita del usuario: el loop vive dentro de dev-apply-review; no se creó orquestador separado ni modo opcional.

## Cambios

- dev-apply-review coordina baseline vigente, corrección mediante escritor canónico y revisión completa independiente, con máximo tres tandas por defecto. El presupuesto se consume antes de escribir y no se reinicia al reanudar. Detiene por decisión requerida, fallo, estancamiento/oscilación o agotamiento, sin declarar preparación.
- dev-review-spec calcula readiness a partir de evidencia estructurada: major/blocker impide preparación; minor exclusivo admite LISTO CON OBSERVACIONES. Perfil adversarial sin cuota mediante forwarded activation; demás lentes/directivas aplicables se preservan. No se modificó la distribución BMAD.
- Protocolo Python stdlib: hashes y manifiestos, Markdown/JSON históricos inmutables, copias vecinas de compatibilidad, archivo de entrada original, run.json, D estables por causa semántica y R locales, reconciliación con evidencia, métricas disponibles y separación aplicado/resuelto.
- dev-spec explica que apply ya itera. dev-build valida corrida entregada desde loop y contrato vigente, preservando checkpoints y otros tipos de entrada.
- Revisión incremental permanece diferida. Los reportes registran coverage full y mediciones; no hay benchmark que demuestre ahorro todavía.

## Verificaciones ejecutadas

```text
python3 -m unittest discover -s /home/clancien/.codex/skills/dev-review-spec/scripts/tests -v
```

Resultado: 26 tests satisfactorios. Cubren limpio, minor, major/blocker, checks falsos, decisiones pendientes, fallos de lente, companions obsoletos/faltantes, metadata incoherente, outputs colisionados, protección de fuentes/historial, presupuesto previo a escritura, reparación y cierre, ausencia de finding sin cierre automático, aplicado sin resolución, deferral de major inválido, IDs locales reiniciados, solapamientos, rechazo persistente/reapertura con nueva evidencia, latest mutable no aceptado en ledger, actualización externa explícita y CLI.

Dos revisores independientes inspeccionaron contratos y script. Se corrigieron los hallazgos: cambios registrados sin consumir tanda, colisión Markdown/JSON y reapertura automática de rechazos. Segunda revisión focalizada: ambos devolvieron lista vacía. Se añadió además protección contra sobrescritura de históricos mediante latest y casos de archivo legacy/vigencia antes de begin.

scan-scripts pasó sin hallazgos del script nuevo. scan-path-standards pasó en los archivos de producción de los cuatro skills, comprobados en carpetas temporales sin historial. El scan sobre árboles completos reporta únicamente .decision-log.md en raíz (ubicación exigida por Workflow Builder) y paths absolutos de reportes .analysis preexistentes; se conservaron como historia y no se consideran defectos del código operativo. git diff --check pasó.

## Límites de lo comprobado

Las pruebas validan plumbing y gates deterministas, no precisión semántica del modelo. Inventario de companions, hechos del repositorio, asignación de keys por causa raíz, checks y evidencias de resolución siguen siendo responsabilidad de los agentes. No se ejecutó un benchmark de specs reales ni se midió ahorro, y no se inició implementación de ninguna spec. El proceso de tres tandas es un default operativo, no un óptimo experimental.

Los paths instalados en .codex/skills son enlaces hacia agents/skills del workspace; los archivos canónicos fueron actualizados allí. No se hicieron commits ni se alteraron otros cambios existentes/staged del usuario.
