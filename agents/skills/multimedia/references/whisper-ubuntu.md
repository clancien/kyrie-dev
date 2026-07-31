# Whisper en Ubuntu

Este skill usa el binario `whisper` del paquete `openai-whisper`.

## Instalación

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv pipx
pipx ensurepath
pipx install openai-whisper
```

## Verificación

```bash
whisper --help
which whisper
```

Si `whisper` no está en `PATH`, usar el binario instalado por `pipx`:

```bash
~/.local/share/pipx/venvs/openai-whisper/bin/whisper --help
```

## Nota operativa

- `batch_whisper_to_srt.py` y `transcript.py` dependen de ese binario.
- El modelo por defecto usado por el skill es `large-v3-turbo`.
