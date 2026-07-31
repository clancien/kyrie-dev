#!/usr/bin/env python3
"""
Transcribe a single audio or video file with the openai-whisper CLI.

Examples:
    python3 transcript.py audio.mp3
    python3 transcript.py video.mp4 --language es --output transcripcion.txt
    python3 transcript.py audio.mp3 --format srt --output-dir salidas
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


DEFAULT_WHISPER_BIN = Path("/home/clancien/.local/share/pipx/venvs/openai-whisper/bin/whisper")
DEFAULT_MODEL = "large-v3-turbo"
OUTPUT_FORMATS = {"txt", "srt", "vtt", "json", "tsv"}
TASKS = {"transcribe", "translate"}


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise SystemExit(
            "No se encontro whisper. Instala openai-whisper con pipx o agrega whisper al PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"whisper fallo con codigo {exc.returncode}: {' '.join(cmd)}") from exc


def resolve_whisper_bin() -> Path:
    on_path = shutil.which("whisper")
    if on_path:
        return Path(on_path)
    if DEFAULT_WHISPER_BIN.exists():
        return DEFAULT_WHISPER_BIN
    raise SystemExit(
        "No se encontro el binario whisper. Instala openai-whisper con pipx o revisa el PATH."
    )


def default_output_for(source: Path, output_format: str) -> Path:
    return source.with_suffix(f".{output_format}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe a single file with openai-whisper.")
    parser.add_argument("input", type=Path, help="Archivo de audio o video de entrada")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Archivo de salida final. Si no se indica, se usa el mismo nombre base con la extension del formato.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directorio de salida. No se puede usar junto con --output.",
    )
    parser.add_argument(
        "--format",
        choices=sorted(OUTPUT_FORMATS),
        default="txt",
        help="Formato de salida de whisper. Default: txt",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Idioma de entrada. Si no se indica, whisper lo detecta automaticamente.",
    )
    parser.add_argument(
        "--task",
        choices=sorted(TASKS),
        default="transcribe",
        help="Tarea de whisper. Default: transcribe",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Modelo de whisper. Default: {DEFAULT_MODEL}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.input.exists():
        raise SystemExit(f"No existe el archivo de entrada: {args.input}")
    if not args.input.is_file():
        raise SystemExit(f"La ruta de entrada no es un archivo: {args.input}")
    if args.output and args.output_dir:
        raise SystemExit("Usa --output o --output-dir, pero no ambos.")

    whisper_bin = resolve_whisper_bin()
    expected_output = default_output_for(args.input, args.format)

    if args.output is not None:
        final_output = args.output
    elif args.output_dir is not None:
        final_output = args.output_dir / expected_output.name
    else:
        final_output = expected_output

    final_output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="multimedia_whisper_") as temp_dir:
        temp_path = Path(temp_dir)
        cmd = [
            str(whisper_bin),
            str(args.input),
            "--model",
            args.model,
            "--task",
            args.task,
            "--output_format",
            args.format,
            "--output_dir",
            str(temp_path),
        ]
        if args.language:
            cmd.extend(["--language", args.language])

        run(cmd)

        generated = temp_path / expected_output.name
        if not generated.exists():
            raise SystemExit(f"Whisper no genero la salida esperada: {generated}")

        if final_output.exists():
            final_output.unlink()
        shutil.move(str(generated), str(final_output))

    print(f"Creado: {final_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
