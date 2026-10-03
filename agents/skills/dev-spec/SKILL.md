---
name: dev-spec
description: Clarificar un requerimiento mediante conversación y delegar a un subagente BMAD la creación de una spec, recomendando implementación completa o por stories. Usar cuando se solicite preparar una funcionalidad con este flujo; no implementa código.
---

# Preparar una spec de funcionalidad

## Recopilar el requerimiento

Recibe un requerimiento en texto o un documento legible. Si falta, solicita al usuario que describa la funcionalidad y espera antes de delegar. Si se indica un documento inexistente o ambiguo, pide corregir la referencia.

Inspecciona las instrucciones y el contexto del proyecto para descubrir stack, integraciones y convenciones. No preguntes por hechos verificables en el repositorio. Conversa hasta reunir:

- Nombre corto de la funcionalidad y slug descriptivo en minúsculas con guiones.
- Problema que resuelve, objetivo de negocio y personas destinatarias.
- Requerimientos concretos, reglas de negocio y casos límite relevantes.
- Restricciones de stack, integraciones y requisitos no funcionales: rendimiento, seguridad, idiomas, etc.
- Límites de alcance y resultados observables para comprobar el éxito.

Agrupa las preguntas pendientes en cada intercambio. Resuelve las ambigüedades que cambien el comportamiento antes de delegar; no inventes decisiones de producto. Marca las inferencias no confirmadas como `[SUPUESTO]` y distingue una restricción desconocida de una que no aplica. No impongas el stack de los ejemplos.

## Seleccionar agentes y delegar

Selecciona solo los agentes necesarios y explica brevemente por qué:

- `bmad-agent-analyst`: clarificación de requisitos, reglas de negocio y casos límite.
- `bmad-agent-architect`: modelo de datos, contratos de API y decisiones técnicas con sus trade-offs.
- `bmad-agent-ux-designer`: cuando haya UI, flujos y estados de vacío, error y carga.

Localiza el `SKILL.md` disponible de `bmad-spec` y de cada agente seleccionado. Si falta una dependencia o la herramienta de subagentes, informa el impedimento y detente sin sustituir la delegación por redacción directa.

Inicia un subagente con el directorio absoluto del proyecto, las rutas absolutas de esos skills y el contexto recopilado. Indícale que lea y siga los skills; los nombres con `/` expresan la tarea y no sustituyen esa lectura. Ejecutará `bmad-spec` con los roles seleccionados como apoyo, sin implementar código ni iniciar otros flujos de entrega.

Sustituye los campos de esta plantilla por la información reunida y conserva en «Agentes» únicamente las líneas seleccionadas:

```text
/bmad-spec

Proyecto: <directorio-absoluto-del-proyecto>
Skills: <rutas-absolutas-de-los-SKILL.md>
Feature: <nombre corto de la funcionalidad>
Slug: <slug-de-la-funcionalidad>
Objetivo de negocio: <qué problema resuelve y para quién>

Requerimientos:
- <req 1>
- <req 2>

Restricciones:
- Stack: <stack descubierto o acordado>
- Integraciones: <APIs, auth, etc.>
- No funcionales: <rendimiento, seguridad, i18n, etc.>

Contexto y límites:
- <convenciones, fuentes relevantes, exclusiones y resultados esperados>
- <supuestos identificados, si existen>

Agentes:
- /bmad-agent-analyst: clarifica requerimientos y edge cases antes de redactar.
- /bmad-agent-architect: modelo de datos, contratos de API, decisiones técnicas con trade-off.
- /bmad-agent-ux-designer: flujos de UI y estados de vacío, error y carga.

Reglas:
- Si necesitas decisiones adicionales del usuario, envía todas tus preguntas
  en un solo bloque al agente principal antes de escribir la spec y espera
  sus respuestas. No decidas en nombre del usuario.
- Marca cada supuesto como [SUPUESTO], además de registrarlo conforme a BMAD.
- Incluye criterios de aceptación en Given/When/Then, observables y testeables.
- Incluye una sección explícita "Fuera de alcance" en el campo Non-goals.
- Conserva el kernel, IDs, memoria y documentos de apoyo del formato BMAD.
  Si la aceptación detallada requiere un companion, referéncialo desde SPEC.md.
- Recomienda una sola corrida o implementación por stories y justifica la
  decisión. Una sola corrida corresponde a un cambio cohesivo verificable
  conjuntamente; stories, a entregas independientes o dependencias por etapas.
- No implementes código ni crees stories automáticamente.

Output: carpeta nativa de bmad-spec según la configuración del proyecto,
con SPEC.md, .memlog.md y los documentos de apoyo necesarios.
Devuelve la ruta absoluta efectiva de SPEC.md, archivos generados,
supuestos, pendientes y recomendación con un plan breve de implementación.
```

Respeta la configuración de salida de `bmad-spec`; no fuerces `docs/specs/<feature>.md` ni modifiques la configuración BMAD. Proporciona el slug para evitar que una invocación programática carezca de identificador.

Traslada al usuario las preguntas del subagente y devuelve sus respuestas al mismo subagente. No continúes trabajo dependiente de respuestas aún pendientes.

## Verificar la entrega

Espera la finalización y lee `SPEC.md`, `.memlog.md` y los documentos de apoyo referenciados. Comprueba que:

- Las rutas devueltas existen, son legibles y los companions se resuelven desde la spec.
- El requerimiento y las restricciones recopiladas están preservados en el kernel o sus companions.
- Hay aceptación en Given/When/Then, supuestos marcados si existen y "Fuera de alcance" explícito.
- Se conserva el formato BMAD y hay una recomendación justificada con un plan breve.

Si falta un requisito, solicita al mismo subagente que lo complete dentro del alcance acordado y verifica de nuevo. Si falla la delegación o no puede completar la entrega, informa lo generado y lo pendiente sin presentar la spec como terminada. Identifica expresamente las decisiones pendientes que impiden implementar; una spec creada no implica que esté lista para construir.

## Entregar el plan y los prompts de continuación

Responde en español con un enlace a la ruta real de `SPEC.md`, supuestos y pendientes relevantes, y un plan breve acorde a la modalidad recomendada. Entrega estos prompts sustituyendo `<PATH-DE-LA-SPEC>` por la ruta real, entre comillas si contiene espacios:

```text
/dev-review-spec <PATH-DE-LA-SPEC>
/dev-apply-review <PATH-DE-LA-SPEC>
/bmad-create-epics-and-stories <PATH-DE-LA-SPEC>
```

Explica que `dev-apply-review` se usa después de generar el informe de review y que `bmad-create-epics-and-stories` corresponde al camino por stories. Son comandos para continuar, no tareas que debas ejecutar en este flujo.

Para implementación en una sola corrida, agrega:

```text
/dev-build <PATH-DE-LA-SPEC>
```

Para implementación por stories, agrega:

```text
/dev-build <PATH-DE-CADA-STORY>
```

Indica que se ejecuta una vez por story, en el orden de dependencias del plan. Si aún no existen, conserva el placeholder explícito y aclara que las rutas se obtendrán al crearlas. Si existen y se han verificado, entrega un comando con la ruta real de cada story; no inventes nombres ni rutas.
