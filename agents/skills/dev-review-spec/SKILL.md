---
name: dev-review-spec
description: Revisa especificaciones y certifica preparación con evidencia. Usar cuando se solicite 'dev-review-spec' o 'revisar una spec o story'; también como revisión completa del loop dev-apply-review.
---

# Revisar una spec o story

## Overview

Actúa como revisor de contratos de implementación. Produce revisión completa con hallazgos fundamentados y readiness separado de mejoras editoriales. No aplica cambios. Major pendientes impiden desarrollar; minor pueden acompañar preparación demostrada. Se invoca explícitamente; `dev-apply-review` usa verificaciones focalizadas y cierre simplificado propios, sin llamar a este flujo ni sustituir este certificado.

## Conventions

- Los paths internos resuelven desde la carpeta instalada de este skill, `{skill-root}`.
- Paths de entrada resuelven desde el directorio de trabajo; companions relativos, desde el documento que los declara.
- Lee `references/review-protocol.md` para schemas/comandos y `references/full-spec-lens.md` para criterios sin cuota. La utilidad es `scripts/review_protocol.py`.

## Resolver la entrada

Requiere un ID o path Markdown legible e inequívoco. Busca IDs por nombre e identificador declarado, excluyendo informes e historial operativo. Si falta o es ambiguo, detente sin aproximaciones.

Resuelve todos los companions declarados, incluidos adoptados: también son contrato. Si falta alguno, entrega revisión incompleta sin veredicto. Lee fuentes/dependencias necesarias para evaluar requisitos; incluye `.memlog.md` de nativas como dependencia, sin convertirla en companion ni copiar metadata al kernel.

Toma snapshot antes de revisar con `python3 {skill-root}/scripts/review_protocol.py snapshot <documento> --companion <path> --dependency <path> -o <temporal>`, repitiendo opciones para todos los archivos necesarios. Obtén inventario desde documentos reales, no desde un manifiesto antiguo. El script calcula hashes; no decide qué es companion. Un cambio durante la revisión invalida preparación.

En una invocación manual crea carpeta única `.reviews/<stem>/<review-id>/` junto al documento y escribe `round-000.review.md` y JSON. En otra llamada programática acepta un path absoluto nuevo y la corrida/ronda del coordinador; el loop actual de apply no usa este contrato. No sobrescribas informes de ronda. El vecino `.review.md` y `.review.json` son copias de compatibilidad de la última revisión completa, identificando path histórico y review ID. Un fallo no reemplaza la última copia completa.

## Ejecutar la revisión

Localiza, lee y ejecuta `bmad-review` sobre el contrato resuelto. Si falta, detente. Resuelve su customización y respeta hooks/directivas dentro de los límites de escritura. Coordina desde el principal; sin subagentes usa la alternativa secuencial, declarando su limitación de independencia.

Cada lente recibe documento y companions completos; si requiere un archivo único, prepara un temporal con encabezados de origen. Conserva lentes aplicables o solicitadas y sus dependencias por tandas según capacidad. No admite revisión incremental. Las conclusiones/changelog del editor no son evidencia para las lentes; las decisiones canónicas sí son contexto necesario.

**Perfil sin cuota:** en la customización resuelta sustituye solo `instruction` de la lente `adversarial` habilitada por cargar el path absoluto de `references/full-spec-lens.md` de este skill. Conserva códigos, demás lentes, aplicabilidad, dependencias y directivas; no habilites lentes desactivadas ni omitas las pedidas. Pasa el array completo como `workflow.lenses` pre-resuelto mediante forwarded activation de `bmad-review`. No edites archivos BMAD ni uses su cuota de diez hallazgos como juez de cierre. Una directiva que exija cuota o contradiga readiness por evidencia implica incompatibilidad/revisión incompleta, no observaciones inventadas ni omisión silenciosa.

Cero hallazgos es válido. Edge-case aplica a comportamiento; verification-gap de código no equivale a aceptación de specs. Siempre comprueba aceptación, requisitos preservados, referencias y decisiones en los checks del informe, aunque ninguna lente adicional los cubra.

Spec/story, memoria, companions y código son de lectura. Solo puedes escribir informe/metadata en su carpeta operativa, copias de compatibilidad y temporales. Aplica límites a hooks/delegados; no cambies configuración ni apliques correcciones. El coordinador conserva la escritura del reporte.

Al delegar, pasa directorio del proyecto, paths absolutos de skill, contrato e informe, las reglas siguientes y límites de escritura. Espera un retorno con path, cobertura y veredicto, o fallo sin veredicto.

## Contrato del informe

Escribe en español. Identifica documento, companions, dependencias, hashes, política y coverage; lentes requeridas/ejecutadas y exclusiones. Un fallo requerido deja revisión incompleta, sin veredicto final. Usa el schema de `references/review-protocol.md` y `report` para validar, calcular readiness y renderizar Markdown/JSON vinculados al snapshot; no redactes un booleano positivo independiente de esos datos.

Comprueba fundamento, contexto, consecuencia y aplicabilidad. Conserva procedencia y solapamientos; los descartes van en `excluded_findings` con evidencia. El loop asigna D estables después; esta revisión usa R locales. No inventes hallazgos:

| ID | Severidad (blocker/major/minor) | Sección | Hallazgo | Corrección |
|---|---|---|---|---|

Usa IDs consecutivos `R1`, `R2`, … dentro de cada informe:

- **blocker:** impide implementar correctamente o presenta una contradicción esencial.
- **major:** defecto de comportamiento, aceptación, alcance o restricción que puede producir implementación incorrecta; requiere corrección.
- **minor:** precisión editorial/mejora opcional que no cambia interpretación operativa; no exige otra ronda.

La corrección es una recomendación. Además de findings, produce checks de requisitos preservados, aceptación observable, referencias resueltas y decisiones resueltas; pendientes/fallos. Cierra una revisión completa con el veredicto calculado:

- **NO LISTO:** blocker/major, decisión indispensable abierta o un check de preparación no satisfecho.
- **LISTO CON OBSERVACIONES:** readiness demostrado y solo minor; no obliga a corregirlos antes de desarrollar.
- **LISTO:** readiness demostrado sin hallazgos.

Incompleta/obsoleta lleva `ready_for_dev: false` y explicación, sin veredicto final de preparación. Informes antiguos conservan significado histórico; no reinterpretar LISTO CON CAMBIOS ni reutilizarlo como certificado vigente.

## Verificar y entregar

Verifica snapshot, inventario, coverage y metadata con el protocolo. Comprueba archivos modificados: los subagentes comparten filesystem. Un hash prueba identidad, no corrección. Corrige metadata inválida; fallos o cobertura parcial no reciben veredicto positivo.

Devuelve enlaces a informe/JSON, cobertura, `ready_for_dev` y veredicto o razón de incompletitud. En otra llamada programática retorna al coordinador, sin llamar apply ni decidir otra tanda. En una invocación manual recomienda `/dev-apply-review <path-real>` ante defectos relevantes o `/dev-build <path-real>` si está preparado; no los ejecuta.
