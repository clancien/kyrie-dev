# Manual Completo de Uso de BMad

Esta guía cubre el uso de BMad bajo la especificación **BMad Method v2**, aplicando la convención moderna de **Contexto Consolidado** (`docs/planning-artifacts/`) y el motor unificado de ejecución **`bmad-build`**.

---

## 1. Conceptos Fundamentales

El BMad Method (Build-Measure-Adapt Development) estructura la colaboración con LLMs dividiendo el ciclo de desarrollo en dos grandes fases:

* **Fase de Planificación:** Define la visión técnica, modelos de datos, arquitectura y desglose de épicas en artefactos consolidados.
* **Fase de Construcción (`bmad-build`):** Ejecuta de forma autónoma pero verificada el desarrollo del código, integrando exploración de codebase, implementación, testing y auto-review en un solo ciclo.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FASE DE PLANIFICACIÓN                           │
│  PRD (bmad-spec) ──► Arquitectura (bmad-architecture) ──► Epics/Stories│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Genera
                                   ▼
                   ┌───────────────────────────────┐
                   │  docs/sprint-status.yaml      │
                   └───────────────┬───────────────┘
                                   │ Lee / Escribe
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FASE DE EJECUCIÓN                               │
│                      /bmad-build <story-id>                            │
│  (Exploración de Codebase ──► Código/Tests ──► Verification/Review)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Iniciar un Proyecto en Blanco (Greenfield)

### Paso 1: Instalación e Inicialización

1. Instala el CLI de BMad en la raíz de tu proyecto vacío:

```bash
npm install -g @bmad/cli
# O bien mediante npx en el proyecto
npx bmad init
```

2. Ejecuta la inicialización para desplegar el árbol de agentes, reglas del sistema y carpetas predeterminadas:

```bash
/bmad-init
```

Estructura de carpetas generada:

```text
mi-proyecto/
├── .bmad/                       # Configuración y prompts de agentes BMad
├── docs/
│   └── planning-artifacts/      # Ámbitos y contratos del proyecto
│       ├── prd.md
│       ├── architecture.md
│       └── epics.md             # Archivo unificado de Épicas e Historias
│   └── sprint-status.yaml       # Fuente única de verdad del Sprint
└── src/                         # Código fuente
```

---

### Paso 2: Especificación de Requerimientos (`bmad-spec`)

Invoca al agente de producto para definir los límites del proyecto:

```bash
/bmad-spec
```

* **Qué hace:** Entrevista al desarrollador o analiza las notas iniciales para definir funcionalidades, requerimientos no funcionales, casos de borde y reglas de negocio.
* **Resultado:** Crea o actualiza `docs/planning-artifacts/prd.md`.

---

### Paso 3: Diseño de Arquitectura (`bmad-architecture`)

Define el diseño técnico sobre el cual el código será escrito:

```bash
/bmad-architecture
```

* **Qué hace:** Diseña los modelos de datos, contratos de APIs, dependencias, integraciones de terceros y convenciones de carpetas y código.
* **Resultado:** Crea `docs/planning-artifacts/architecture.md`.

---

### Paso 4: Desglose en Épicas e Historias (`bmad-plan`)

A partir del PRD y la Arquitectura, fragmenta el trabajo en unidades ejecutables:

```bash
/bmad-plan
```

* **Resultado:** 
  1. Genera el documento unificado `docs/planning-artifacts/epics.md`.
  2. Inicializa la fuente única de verdad `docs/sprint-status.yaml`.

---

### Ejemplo de Artefactos Generados

#### `docs/planning-artifacts/epics.md`

```markdown
# Épicas e Historias del Proyecto

## Epic 1: Autenticación y Usuarios

### Story 1-1: Esquema de Usuarios en BD
**Contexto:** Crear la tabla de usuarios con soporte para credenciales encriptadas.
**Criterios de Aceptación:**
- [ ] Migración de BD en `src/db/migrations` funcional.
- [ ] Modelo de TypeScript `User` exportado con tipos requeridos.
- [ ] Tests unitarios del modelo pasando.

### Story 1-2: Endpoint de Login JWT
**Contexto:** Exponer `/api/auth/login` validando contraseñas con bcrypt y retornando JWT.
**Criterios de Aceptación:**
- [ ] Route POST `/api/auth/login` validado con Zod.
- [ ] Generación de JWT con firma segura.
- [ ] Tests de integración con supertest.
```

#### `docs/sprint-status.yaml`

```yaml
epic-1-auth:
  title: "Autenticación y Usuarios"
  status: "in-progress"
  stories:
    1-1-user-schema:
      title: "Esquema de Usuarios en BD"
      status: "ready-for-dev"
    1-2-user-auth-login:
      title: "Endpoint de Login JWT"
      status: "backlog"
```

---

## 3. Iniciar un Proyecto Existente sin BMad (Brownfield)

Cuando se integra BMad a un repositorio con código preexistente, el objetivo principal es **indexar la arquitectura existente sin reescribir la aplicación**.

1. **Inicializar BMad en el Repositorio:**
   ```bash
   cd mi-proyecto-existente
   npx bmad init
   ```

2. **Indexación Automática de la Arquitectura:**
   Ejecuta el comando de ingeniería inversa para analizar el codebase:
   ```bash
   /bmad-architecture --brownfield
   ```
   El agente escaneará la estructura del código (`package.json`, carpetas, esquemas de BD, imports principales) y documentará el estado actual en `docs/planning-artifacts/architecture.md`.

3. **Crear Especificación Incremental:**
   En lugar de documentar todo el sistema pasado en un PRD gigante, documenta el nuevo feature o módulo mediante:
   ```bash
   /bmad-spec --delta
   ```
   Esto generará un PRD enfocado en el delta (las nuevas capacidades a agregar sobre la base existente).

4. **Generar Épicas e Inicializar Sprint:**
   Genera el plan de historias conectándolo con las convenciones descubiertas en el paso de arquitectura:
   ```bash
   /bmad-plan
   ```
   Verifica que `docs/sprint-status.yaml` contenga las historias listas para ser tomadas por `bmad-build`.

---

## 4. Ejecución del Desarrollo: Motor `bmad-build`

El comando **`bmad-build`** es el estándar moderno unificado para la implementación de software. Reemplaza el antiguo flujo fragmentado de `create-story -> dev-story`.

```
                  ┌─────────────────────────────┐
                  │    /bmad-build <story-id>   │
                  └──────────────┬──────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │  Clasificación de Complejidad │
                 └───────┬───────────────┬───────┘
                         │               │
            Ruta Light   │               │   Ruta Plan
      (Cambios directos) │               │ (Cambios complejos)
                         ▼               ▼
                 ┌───────────────┐ ┌───────────────┐
                 │ Edición Directa│ │ Generar Plan  │
                 └───────┬───────┘ └───────┬───────┘
                         │                 │ Aprobar
                         │                 ▼
                         │          ┌───────────────┐
                         │          │ Ejecutar Plan │
                         │          └───────┬───────┘
                         │                  │
                         └───────┬──────────┘
                                 │
                                 ▼
                   ┌──────────────────────────┐
                   │ Verification & Auto-Review│
                   └─────────────┬────────────┘
                                 │
                                 ▼
                   ┌──────────────────────────┐
                   │ Actualiza sprint-status  │
                   └──────────────────────────┘
```

### Invocación Estándar (Basada en Historia)

Para ejecutar una historia planificada en `sprint-status.yaml`:

```bash
/bmad-build 1-1-user-schema
```

#### Fases Internas de Ejecución:

1. **Lectura de Contexto:** `bmad-build` lee `sprint-status.yaml`, extrae los detalles técnicos y Criterios de Aceptación desde `docs/planning-artifacts/epics.md` y consulta las convenciones en `architecture.md`.
2. **Actualización de Estado:** Cambia automáticamente el estado de la historia a `in-progress` en `sprint-status.yaml`.
3. **Exploración de Codebase:** Escanea el proyecto en busca de archivos relacionados para garantizar consistencia estilística y funcional.
4. **Desarrollo:**
   * **Light Path:** Si el cambio implica pocas líneas o es directo, edita directamente archivos y crea tests.
   * **Plan Path:** Si detecta riesgo arquitectónico o múltiples archivos afectados, muestra un plan de pasos corto en consola y solicita confirmación antes de escribir código.
5. **Auto-Review y Verificación:** Ejecuta la suite de pruebas (linter, unit tests, compilación de tipos) usando herramientas como *Edge Cases Hunter* y *Verification Gap Finder*.
6. **Cierre:** Al verificar que todos los criterios de aceptación fueron cumplidos y los tests pasaron, actualiza el estado de la historia en `sprint-status.yaml` a `done` (o `review`).

---

### Invocación por "Siguiente Historia" (Next Story)

Para ejecutar automáticamente la primera historia en estado `ready-for-dev` según la prioridad registrada en `sprint-status.yaml`:

```bash
/bmad-build
```

---

### Invocación Ad-Hoc / Quick Fix (Sin Historia Previa)

Para realizar ajustes rápidos o refactorizaciones fuera del plan de sprint:

```bash
/bmad-build fix: corregir error de tipeo en validación de email
```

* **Comportamiento:** Se ejecuta bajo la *Ruta Light* sin modificar `sprint-status.yaml` ni requerir la creación previa de un documento de historia.

---

## 5. Flujos Alternativos: Gestión Dinámica de Épicas y Stories

El desarrollo real es adaptativo. A continuación se presentan los tres flujos para modificar la planificación sobre la marcha sin romper la estructura de BMad.

| Tipo de Cambio | Método Recomendado | Impacto en `sprint-status.yaml` |
| :--- | :--- | :--- |
| **Puntual / Fix rápido** | Ejecutar `/bmad-build <intención>` directa | Sin impacto (no modifica el archivo) |
| **Nueva Story en Épica** | Edición manual directa en `epics.md` | Se agrega el nodo de la historia con estado `ready-for-dev` |
| **Nueva Épica o Re-scope** | Invocación asistida con agente `/bmad-plan` | Se agregan nuevos nodos de Épica e Historias |

---

### Modificación Manual Directa (Recomendada para historias individuales)

Para agregar una historia a una Épica existente durante la ejecución de un sprint:

1. Abre `docs/planning-artifacts/epics.md` y agrega la nueva sección al final de la Épica correspondiente:

```markdown
### Story 1-3: Refresh Tokens de Sesión
**Contexto:** Extender seguridad emitiendo refresh tokens en HTTP-Only Cookies.
**Criterios de Aceptación:**
- [ ] Endpoint `/api/auth/refresh` implementado.
- [ ] Cookies seguras configuradas en la respuesta.
```

2. Registra la entrada en `docs/sprint-status.yaml`:

```yaml
epic-1-auth:
  title: "Autenticación y Usuarios"
  status: "in-progress"
  stories:
    1-1-user-schema: { status: "done" }
    1-2-user-auth-login: { status: "done" }
    1-3-refresh-tokens: { status: "ready-for-dev" } # <--- Nueva Historia
```

3. Ejecuta directamente el desarrollo:

```bash
/bmad-build 1-3-refresh-tokens
```

---

### Modificación Asistida por Agente (Para cambios grandes de alcance)

Si el cliente solicita un módulo nuevo completo o una reestructuración de funcionalidades:

1. **Actualiza la Arquitectura (si aplica):**
   ```bash
   /bmad-architecture
   ```
   *(Ingresa los nuevos detalles sobre los modelos o servicios necesarios)*.

2. **Regenera/Sincroniza el Plan de Épicas:**
   ```bash
   /bmad-plan --append
   ```
   * **Qué hace:** Preserva las historias marcadas como `done` en `sprint-status.yaml`, lee las nuevas especificaciones y añade las nuevas Épicas e Historias al final de `docs/planning-artifacts/epics.md` actualizando el YAML automáticamente.
