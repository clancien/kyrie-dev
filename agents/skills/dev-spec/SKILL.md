---
name: dev-spec
description: Preparar una spec BMAD desde un requerimiento, aclarar decisiones pendientes y recomendar implementación completa o por stories. Usar cuando se solicite preparar una funcionalidad con este flujo; no implementa código.
---

# Preparar una spec

## Reunir el contexto

Recibe un requerimiento en texto o un documento legible e inequívoco. Si falta o la referencia no se resuelve, pide corregir la entrada antes de redactar.

Inspecciona las instrucciones y los hechos del proyecto necesarios para reunir:

- Nombre y slug en minúsculas con guiones.
- Problema, objetivo de negocio y destinatarios.
- Requerimientos, reglas de negocio y casos límite.
- Stack, integraciones, convenciones y requisitos no funcionales.
- Alcance, exclusiones y resultados observables de éxito.

Con información suficiente, pasa a redactar. Pregunta en bloques solo por decisiones pendientes; no preguntes hechos verificables en el repositorio ni inventes decisiones de producto. Resuelve ambigüedades de comportamiento antes del trabajo dependiente. Marca inferencias no confirmadas como `[SUPUESTO]`; distingue restricciones desconocidas de las que no aplican.

## Ejecutar bmad-spec

Localiza y lee `bmad-spec`. Selecciona solo las perspectivas necesarias: `bmad-agent-analyst` para requisitos, `bmad-agent-architect` para decisiones técnicas y `bmad-agent-ux-designer` para UI y sus estados. Explica la selección y lee esos skills; si falta una dependencia necesaria, informa el impedimento y detente. Varios roles dentro de un agente no son revisiones independientes.

Ejecuta directamente o delega para separar autoría y comprobación en specs extensas; respeta la modalidad solicitada. Sin subagentes, continúa directamente. Al delegar, pasa directorio del proyecto, paths absolutos de skills y fuentes, hechos y decisiones. El hijo debe leer y seguir los skills; evita duplicar investigaciones resueltas.

Ejecuta `bmad-spec` con nombre, slug, objetivo, requerimientos, restricciones y límites. Exige:

- Carpeta nativa según la configuración; no fuerces paths ni cambies la configuración BMAD.
- Kernel, IDs estables, `.memlog.md` canónica y companions conforme a BMAD. Los cambios se registran en memoria y se derivan mediante `bmad-spec`; no parches `SPEC.md` manualmente.
- Aceptación observable en Given/When/Then; si requiere un companion, referéncialo desde `SPEC.md`.
- `[SUPUESTO]` donde corresponda y "Fuera de alcance" explícito en Non-goals.

No implementes código ni crees stories. Si delegas, el hijo envía decisiones pendientes al principal y espera las respuestas del usuario antes del trabajo dependiente. Respeta la salida nativa de `bmad-spec`, incluido su JSON headless; el coordinador lee los artefactos y prepara la entrega del wrapper. Recomienda una corrida para un cambio cohesivo verificable conjuntamente, o stories para entregas independientes/dependencias por etapas; justifica y añade un plan breve en la respuesta, no en el kernel ni en `companions:`. El retorno delegado resume paths, supuestos, pendientes y recomendación, sin copiar los documentos.

## Comprobar la entrega

Lee `SPEC.md`, `.memlog.md` y los companions referenciados. Comprueba que existen, sus referencias se resuelven y preservan los requerimientos, restricciones y decisiones; que mantienen el formato e IDs BMAD; y que incluyen aceptación, supuestos y exclusiones acordados. Respeta la propiedad de companions adoptados: se referencian, no se editan como documentos propios.

Contrasta artefactos y cambios reales con el contexto y alcance, no solo con el resumen del autor. Corrige faltantes mediante `bmad-spec` o con el mismo hijo y verifica de nuevo. Si falla, comunica lo generado y las decisiones pendientes que impiden implementar; crear una spec no demuestra readiness.

## Entregar y continuar

Responde en español con el enlace real a `SPEC.md`, supuestos, pendientes y plan. Entrega prompts con paths verificados, entre comillas si contienen espacios:

```text
/dev-review-spec <PATH-DE-LA-SPEC>
/dev-apply-review <PATH-DE-LA-SPEC>
```

Son pasos para continuar, no ejecuciones de este flujo; `dev-apply-review` requiere el informe previo y ejecuta automáticamente el loop acotado de aplicación y revisiones completas hasta readiness o una parada explícita. No es necesario repetir manualmente review/apply. Major pendientes impiden readiness; minor opcionales pueden acompañar `LISTO CON OBSERVACIONES`.

- Una corrida: `/dev-build <PATH-DE-LA-SPEC>`.
- Por stories: `/bmad-create-epics-and-stories <PATH-DE-LA-SPEC>` y `/dev-build <PATH-DE-CADA-STORY>`, una vez por story en orden de dependencias. Si aún no existen, conserva el placeholder y explica que las rutas se obtienen al crearlas; no inventes nombres.

Aclara que build puede generar una spec operativa distinta tomando `SPEC.md` y sus companions como contrato fuente.
