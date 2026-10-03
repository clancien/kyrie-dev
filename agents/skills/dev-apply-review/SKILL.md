---
name: dev-apply-review
description: Aplicar una review a una spec o story por ID o path mediante un subagente arquitecto BMAD, conservando su formato y registrando los hallazgos aplicados y rechazados. Usar cuando se solicite aplicar una revisión al documento.
---

# Aplicar review a una spec o story

## Resolver los documentos

Recibe un ID o path obligatorio de una spec o story y, opcionalmente, un ID o path de una review. Si falta la spec/story, informa que es obligatoria y detén el proceso.

Resuelve los paths proporcionados desde el directorio de trabajo. Para un ID, busca en los documentos del proyecto por nombre e identificador declarado; al resolver la spec/story, excluye informes `.review.md`. Continúa únicamente con un documento Markdown legible e inequívoco. Si no existe, no es legible o hay varias coincidencias, informa el problema y detente sin elegir por aproximación.

Resuelve la review con esta prioridad:

1. Si el usuario proporciona un ID o path de review, úsalo sin sustituirlo por otro informe.
2. Si no lo proporciona, lee la spec/story y busca una referencia explícita a su review. Resuelve los paths relativos de esa referencia desde la carpeta de la spec/story y los IDs mediante la búsqueda del proyecto.
3. Solo si no hay referencia interna, busca junto al documento un archivo cuyo nombre reemplace la extensión `.md` por `.review.md`.

Si la review indicada o referenciada no existe, no es legible o resulta ambigua, informa el problema y detente sin recurrir al nombre inferido. Si tampoco existe el archivo inferido cuando corresponde buscarlo, detente. No generes una review nueva.

## Delegar al arquitecto

Localiza el skill disponible `bmad-agent-architect` y la herramienta de subagentes. Si falta cualquiera, informa el fallo y detente; no sustituyas la delegación por una aplicación directa.

Inicia un subagente con los paths absolutos de la spec/story, la review y el `SKILL.md` del arquitecto. Indícale que lea y ejecute ese skill y que solo puede modificar la spec/story, manteniendo la review como fuente de lectura. Incluye esta tarea, sustituyendo `<REVIEW>` y `<SPEC>` por sus paths absolutos:

```text
/bmad-agent-architect

Aplica <REVIEW> sobre <SPEC>
- Pregúntame lo que requiere decisiones mías.
- Blocker y major: aplicar todos. Si rechazas uno, justifica en una línea.
- Minor: aplicar solo si no agregan alcance.
- Mantén estructura y formato BMAD.
- Agrega al final un "Changelog de review" con IDs aplicados/rechazados.
```

Pide que conserve los IDs del informe y registre también los minor rechazados por agregar alcance. El subagente debe comunicar al agente principal cualquier pregunta que requiera una decisión del usuario y esperar su respuesta antes de aplicar los cambios dependientes. Traslada esas preguntas al usuario y devuelve sus respuestas al subagente sin decidir en su nombre.

## Comprobar y comunicar el resultado

Espera la finalización del subagente y lee la spec/story actualizada. Comprueba que conserva la estructura y el formato BMAD y que contiene al final el "Changelog de review" con los IDs aplicados/rechazados y las justificaciones de una línea para los blocker o major rechazados. Si falta algún requisito, solicita al mismo subagente que lo complete dentro del alcance autorizado.

Devuelve el path del documento, los IDs aplicados/rechazados y cualquier pendiente. Si la delegación falla o quedan decisiones sin responder, informa lo completado y lo pendiente sin presentar la aplicación como terminada.
