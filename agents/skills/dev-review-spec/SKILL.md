---
name: dev-review-spec
description: Revisar una spec o story por ID o path mediante un subagente que ejecuta bmad-review y genera un informe de preparación sin modificar el documento ni el código. Usar cuando se solicite esta revisión.
---

# Revisión de spec o story

## Entrada obligatoria

Recibe un ID o path de una spec o story. Si no se proporciona, informa que es obligatorio y detén el proceso sin iniciar una revisión.

Para un path, resuélvelo desde el directorio de trabajo y comprueba que sea un documento Markdown legible. Para un ID, busca en los documentos del proyecto por nombre e identificador declarado; excluye informes `.review.md`. Continúa únicamente si identifica un documento inequívoco. Si no existe, no es legible o hay varias coincidencias, informa el problema y detente sin elegir por aproximación.

## Delegación

Localiza el skill `bmad-review` disponible y delega la revisión a un subagente. Si el skill o la herramienta de subagentes no están disponibles, informa el fallo y detente.

Calcula el path de salida junto al documento: reemplaza la extensión `.md` por `.review.md`. Pasa al subagente los paths absolutos del documento, del informe y del `SKILL.md` de `bmad-review`, junto con estas instrucciones:

```text
/bmad-review <path-absoluto-del-documento>

Lee y ejecuta el skill bmad-review indicado (skill:bmad-review).
NO modifiques la spec/story ni el código. El único archivo que puedes
crear o actualizar es <path-absoluto-del-informe>.
Revisa el documento usando las lentes aplicables de bmad-review.
Después de obtener sus resultados, clasifica los hallazgos y redacta
el informe en español conforme al contrato siguiente.
Devuelve el path del informe y el veredicto, o informa el fallo si no
puedes completar la revisión. No emitas un veredicto en caso de fallo.
```

Incluye en la tarea del subagente el contrato completo de informe de la siguiente sección. Espera su finalización y verifica que haya generado el informe con la tabla y el veredicto coherente con las severidades. Devuelve al usuario el path del informe y el veredicto. Si falla la revisión o falta el informe requerido, informa el fallo sin emitir un veredicto de preparación.

## Contrato del informe

El informe debe estar en español y contener esta tabla:

| ID | Severidad (blocker/major/minor) | Sección | Hallazgo | Corrección |
|---|---|---|---|---|---|

`bmad-review` no asigna severidades: clasifica sus resultados al preparar este informe, después de la revisión. Usa IDs consecutivos (`R1`, `R2`, …) y estas severidades:

- **blocker:** impide implementar correctamente o presenta una contradicción esencial.
- **major:** defecto relevante que requiere corrección.
- **minor:** mejora puntual de claridad o precisión.

La corrección es una recomendación escrita; no la apliques. No inventes hallazgos para llenar la tabla. Si no hay hallazgos, conserva únicamente el encabezado y el separador.

Cierra el informe con `Veredicto final: <veredicto>` según estas reglas:

- **NO LISTO:** existe al menos un blocker.
- **LISTO CON CAMBIOS:** hay major o minor, sin blockers.
- **LISTO:** no hay hallazgos.
