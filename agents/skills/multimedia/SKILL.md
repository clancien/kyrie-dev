---
name: multimedia
description: Manipular video y audio con ffmpeg y los scripts del proyecto para crear videos con fotos y música, montar clips, recortar video a 9:16, recortar audio MP3, extraer audio y generar SRT por lote. Usar cuando Codex deba crear, convertir, montar, subtitular o recortar material multimedia en este repositorio.
---

# Multimedia

## Overview

Usar este skill para resolver tareas repetitivas de edición multimedia con los scripts Python ya existentes del proyecto. Mantener el trabajo sobre archivos locales y ejecutar el dispatcher unificado o el script más específico según el objetivo.

## Quick Routing

- Crear video vertical con fotos y música: usar `crear_video_con_fotos.py`
- Generar un video por imagen dentro de carpetas de transiciones: usar `crear_videos_transiciones.py`
- Construir un montaje de varios videos con transiciones y subtítulos quemados: usar `montaje.py`
- Convertir un video a formato vertical `9:16`: usar `crop_9_16.py`
- Recortar un fragmento de audio MP3: usar `recortar_audio.py`
- Convertir un archivo `.ogg` a `.mp3`: usar `convertir_ogg_a_mp3.py`
- Extraer MP3 desde una carpeta de videos: usar `extraer_audio_montaje.py`
- Generar archivos `.srt` por lote desde audio `.mp3`: usar `batch_whisper_to_srt.py`
- Transcribir un archivo único a texto u otro formato de whisper: usar `transcript.py`

## Core Workflow

1. Identificar el tipo de material de entrada: fotos, videos, audio o una mezcla.
2. Elegir el script más específico antes de improvisar un flujo nuevo.
3. Ejecutar desde la raíz del proyecto o pasar rutas explícitas con los flags disponibles.
4. Verificar que `ffmpeg` y, cuando aplique, `ffprobe` estén instalados.
5. Para transcripción, verificar que el binario `whisper` de `openai-whisper` esté disponible.
6. Mantener nombres y carpetas consistentes con los defaults del proyecto cuando sea posible.

## Script Notes

### `multimedia_api.py`

- Usar como punto de entrada unificado cuando se quiera un solo comando para los flujos del skill.
- Delegar en los scripts especializados con subcomandos como `crear-video-con-fotos`, `montaje`, `crop-9-16`, `recortar-audio`, `convertir-ogg-a-mp3`, `batch-whisper-srt` y `transcript`.

### `crear_video_con_fotos.py`

- Crear un video vertical a partir de imágenes ordenadas alfabéticamente y un archivo `musica.mp3`.
- Ajustar `--input-dir`, `--music`, `--output`, `--duration`, `--audio-start`, `--width`, `--height` y `--fps` cuando haga falta.

### `crear_videos_transiciones.py`

- Recorrer subcarpetas con imágenes y audio.
- Generar un `.mp4` por imagen, con duración igual al audio de la carpeta.
- Usar `--input-dir` y `--output-dir` para trabajar fuera de `videos/transiciones`.

### `montaje.py`

- Concatenar clips de una carpeta, normalizarlos a la misma resolución y frame rate, e insertar transiciones.
- Aplicar subtítulos `.srt` con el mismo nombre base del video cuando existan.
- Usar `--shuffle`, `--transition`, `--width`, `--height`, `--fps` y opciones de subtítulos cuando se necesite ajustar la salida.

### `crop_9_16.py`

- Elegir `--mode crop` para llenar el marco recortando al centro.
- Elegir `--mode extend` para conservar todo el video y rellenar con bordes negros.
- Validar que la salida respete exactamente la relación `9:16`.

### `recortar_audio.py`

- Recortar un MP3 desde un segundo de inicio y una duración exacta.
- Usar `-o/--output` solo cuando el nombre automático no sea suficiente.

### `convertir_ogg_a_mp3.py`

- Convertir un archivo `.ogg` a `.mp3` usando `ffmpeg`.
- Usar `-o/--output` para definir el destino o dejar que el script genere el mismo nombre base con extensión `.mp3`.
- Ajustar `--bitrate` cuando se necesite un tamaño o calidad distinta.

### `extraer_audio_montaje.py`

- Extraer audio de los videos compatibles de una carpeta a MP3.
- Usar `--force` para sobrescribir archivos existentes y `--dry-run` para inspeccionar sin escribir.

### `batch_whisper_to_srt.py`

- Procesar solo archivos `.mp3`.
- Reconocer idioma por sufijo del nombre, por ejemplo `*.es.mp3` o `*.fr.mp3`.
- Generar `.srt` en la misma carpeta, sin volver a crear subtítulos ya existentes.

### `transcript.py`

- Transcribir un archivo único de audio o video usando el binario `whisper` de `openai-whisper`.
- Por defecto generar una transcripción `txt`, con salida configurable a `srt`, `vtt`, `json` o `tsv`.
- Permitir definir idioma, modelo y ruta de salida.

## Rules

- No inventar una pipeline nueva si el script existente ya cubre el caso.
- No asumir subcarpetas salvo que el script lo indique explícitamente.
- Mantener salidas pequeñas y predecibles: `mp4`, `mp3` y `srt`.
- Si falta un requisito de sistema, informar el comando exacto que se necesita instalar antes de continuar.
- Para transcripción, usar `openai-whisper` y no otro backend salvo que el script indique lo contrario.
- Si se necesita una interfaz única, usar `multimedia_api.py` como dispatcher y delegar en los scripts especializados.

## Bundled Resources

- `scripts/crear_video_con_fotos.py`
- `scripts/crear_videos_transiciones.py`
- `scripts/montaje.py`
- `scripts/crop_9_16.py`
- `scripts/recortar_audio.py`
- `scripts/convertir_ogg_a_mp3.py`
- `scripts/extraer_audio_montaje.py`
- `scripts/batch_whisper_to_srt.py`
- `scripts/transcript.py`
- `scripts/multimedia_api.py`
- `references/whisper-ubuntu.md`
