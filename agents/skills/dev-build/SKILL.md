---
name: dev-build
description: Implementar una spec o story por ID o path mediante un subagente desarrollador que ejecuta bmad-build. Usar cuando se solicite construir o implementar ese documento con este flujo.
---

# Implementar una spec o story

## Entrada obligatoria

Recibe un ID o path de una spec o story. Si no se proporciona, informa que es obligatorio y detén el proceso sin iniciar la implementación ni llamar a un subagente.

Resuelve los paths desde el directorio de trabajo. Para un ID, busca en los documentos del proyecto por nombre e identificador declarado. Continúa únicamente con un documento legible e inequívoco. Si no existe, no es legible o hay varias coincidencias, informa el problema y detente sin elegir por aproximación.

## Delegación

Localiza los skills disponibles `bmad-build` y `bmad-agent-dev`. Si falta alguno o no está disponible la herramienta de subagentes, informa el fallo y detente.

Inicia un subagente con el directorio del proyecto y los paths absolutos del documento y de ambos `SKILL.md`. Pídele que lea y siga esos skills, adoptando el agente desarrollador y ejecutando esta tarea con el documento resuelto:

```text
/bmad-build <path-absoluto-de-la-spec-o-story>

Agente: /bmad-agent-dev

Al terminar: estado por story (done / blocked) y comandos para verificar.
```

Por ejemplo, para `docs/specs/<feature>.md`, pasa su path absoluto a `/bmad-build`; no sustituyas el documento solicitado por el ejemplo.

Solicita al subagente que responda en español, indique el motivo de cada `blocked` y distinga los comandos ejecutados y sus resultados de los comandos propuestos para verificar. Si necesita una decisión del usuario, debe comunicarla al agente principal y esperar la respuesta antes de continuar el trabajo dependiente.

## Resultado

Espera la finalización del subagente y devuelve el estado de cada story (`done` o `blocked`) y los comandos para verificar, indicando desde qué directorio ejecutarlos. Si faltan estos datos, solicítalos al mismo subagente. No presentes una implementación fallida o incompleta como `done`.
