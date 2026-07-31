#!/usr/bin/env python3
"""
Recorta un archivo MP3 usando un inicio y una duración en segundos.

Ejemplos:
    python3 recortar_audio.py audio.mp3 12 30
    python3 recortar_audio.py audio.mp3 12.5 18.25 -o salida.mp3
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise SystemExit("No se encontró ffmpeg. Instálalo y vuelve a intentarlo.") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffmpeg falló con código {exc.returncode}") from exc


def default_output_for(input_file: Path, start: float, duration: float) -> Path:
    start_label = str(start).replace(".", "p")
    duration_label = str(duration).replace(".", "p")
    return input_file.with_name(
        f"{input_file.stem}_recortado_{start_label}s_{duration_label}s.mp3"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recorta un audio MP3 a partir de un segundo de inicio y una duración."
    )
    parser.add_argument("archivo", type=Path, help="Ruta del archivo MP3 de entrada")
    parser.add_argument("inicio", type=float, help="Segundo de inicio del recorte")
    parser.add_argument("duracion", type=float, help="Duración del recorte en segundos")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Archivo de salida (por defecto se genera uno al lado del original)",
    )
    args = parser.parse_args()

    if not args.archivo.exists():
        raise SystemExit(f"No existe el archivo de entrada: {args.archivo}")
    if args.archivo.suffix.lower() != ".mp3":
        raise SystemExit("Este script está pensado para archivos .mp3")
    if args.inicio < 0:
        raise SystemExit("El inicio no puede ser negativo")
    if args.duracion <= 0:
        raise SystemExit("La duración debe ser mayor que cero")

    output = args.output or default_output_for(args.archivo, args.inicio, args.duracion)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(args.inicio),
        "-i",
        str(args.archivo),
        "-t",
        str(args.duracion),
        "-vn",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "192k",
        str(output),
    ]

    run(cmd)
    print(f"Creado: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
