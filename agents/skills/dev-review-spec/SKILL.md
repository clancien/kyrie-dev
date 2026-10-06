---
name: dev-review-spec
description: Revisar una spec o story por ID o path con bmad-review y generar un informe de preparación en español, sin modificar el documento ni el código. Usar cuando se solicite esta revisión.
---

# Revisar una spec o story

## Resolver la entrada

Requiere un ID o path de un documento Markdown legible. Resuelve paths desde el directorio de trabajo; para IDs, busca por nombre e identificador declarado y excluye `.review.md`. Si falta, no existe o resulta ambiguo, informa el problema y detente sin elegir por aproximación.

Resuelve y lee los companions de una spec nativa desde su carpeta: también forman parte del contrato. Si alguno no se puede leer, informa revisión incompleta sin veredicto. El informe se guarda junto al documento, reemplazando `.md` por `.review.md`.

## Ejecutar la revisión

Localiza, lee y ejecuta `bmad-review` mediante `skill:bmad-review` sobre el contrato resuelto. Si falta el skill, detente. Coordina desde el principal por defecto; delega la coordinación si el usuario lo pide o conviene separar una revisión extensa. Sin subagentes, usa la alternativa secuencial de `bmad-review`.

Revisa documento y companions como una unidad. Cada lente debe recibirlos completos; si el flujo admite un único archivo, prepara un temporal con sus contenidos y encabezados de origen. Conserva las lentes aplicables o seleccionadas explícitamente; planifica dependencias y tandas según capacidad, sin omitirlas. Evita transferir conclusiones del autor a los revisores.

La spec/story, companions y código son de lectura. El único archivo persistente que puedes crear o actualizar es el informe; se permiten archivos temporales de revisión. Aplica este límite también a hooks y configuración del flujo. No apliques las correcciones propuestas.

Al delegar, pasa directorio del proyecto, paths absolutos de skill, contrato e informe, las reglas siguientes y límites de escritura. Espera un retorno con path, cobertura y veredicto, o fallo sin veredicto.

## Contrato del informe

Escribe en español. Identifica documento, companions y lentes ejecutadas; explica exclusiones por aplicabilidad o selección explícita. Un fallo de una lente requerida deja la revisión incompleta: registra lo obtenido y el fallo sin veredicto final.

Después de obtener los resultados, comprueba su fundamento y clasifícalos: `bmad-review` no asigna severidades. Conserva la procedencia de cada lente y los solapamientos conforme al flujo. No inventes hallazgos para llenar la tabla:

| ID | Severidad (blocker/major/minor) | Sección | Hallazgo | Corrección |
|---|---|---|---|---|

Usa IDs consecutivos `R1`, `R2`, … dentro de cada informe:

- **blocker:** impide implementar correctamente o presenta una contradicción esencial.
- **major:** defecto relevante que requiere corrección.
- **minor:** mejora puntual de claridad o precisión.

La corrección es una recomendación. Sin hallazgos, conserva solo encabezado y separador de la tabla. Cierra una revisión completa con `Veredicto final: <veredicto>`:

- **NO LISTO:** al menos un blocker.
- **LISTO CON CAMBIOS:** major o minor, sin blockers. Los minor por sí solos no impiden implementar.
- **LISTO:** ningún hallazgo.

## Verificar y entregar

Verifica el informe: cobertura, tabla, IDs y veredicto acorde a severidades. Comprueba los archivos modificados: los subagentes comparten filesystem. Corrige faltantes directamente o con el mismo hijo; un fallo o informe incompleto no es una revisión terminada.

Devuelve el enlace al informe, cobertura y veredicto, o los pendientes y el fallo sin emitir un veredicto de preparación.
