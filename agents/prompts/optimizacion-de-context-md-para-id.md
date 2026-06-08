# Optimización de archivos de contexto para Agentes LLM

## Objetivo
Refactorizar AGENTS.md, CLAUDE.md y doc/project-context.md para máxima adherencia, mínimo consumo de tokens, mejor signal-to-noise ratio.

Analiza cada línea como si tuviera costo económico y cognitivo.

---

## Criterio de Corte

### ✅ Conservar SOLO si:
- Cambia comportamiento del agente (workflows, restricciones, convenciones)
- Evita romper arquitectura crítica
- No es inferible del código

### ❌ Eliminar si:
- Es obvio para un LLM moderno
- Es documentación, README, o explicaciones teóricas
- Repite información en otra línea
- No afecta ninguna decisión del agente

---

## Transformaciones Requeridas

| De | A | Ejemplo |
|----|---|---------|
| Párrafos largos | Bullets compactos | "Always validate..." → "• Validate inputs at boundaries only" |
| Reglas absolutas | Condicionales | "Never use X" → "Use X only if Y" (cuando sea aplicable) |
| Listas numéricas | Bullets sin número | Reduce parsing visual |
| Instrucciones vagas | Acotadas o eliminadas | "Be careful with..." → específica o fuera |
| Repetición | Una sola fuente | Merge o link |

---

## Prohibido Agregar
- Buenas prácticas genéricas ("write clean code")
- Teoría, justificaciones, consejos vagos
- Contenido estilo wiki/README

---

## Output (Orden)

### 1. Diagnóstico
- Redundancias y ruido detectado
- Instrucciones contradictorias o peligrosas
- Candidatos a modularización

### 2. Archivos de contexto Optimizados
Versión completa lista para usar.

### 3. Recomendaciones Estructurales
- Qué mover a doc/
- Modularización por carpetas (frontend/backend/etc.)
- Referencias externas
