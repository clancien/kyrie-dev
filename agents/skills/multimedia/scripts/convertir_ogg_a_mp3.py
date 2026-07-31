#!/usr/bin/env python3
"""
Convierte un archivo .ogg a .mp3 usando ffmpeg.

Uso:
    python3 convertir_ogg_a_mp3.py audio.ogg
    python3 convertir_ogg_a_mp3.py audio.ogg -o audio.mp3
    python3 convertir_ogg_a_mp3.py audio.ogg --bitrate 256k
"""

from __future__ import annotations

import argparse
from pathlib import Path

from audio_conversion import convert_ogg_to_mp3, default_output_for, ensure_ogg_input


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convierte un archivo .ogg a .mp3."
    )
    parser.add_argument("archivo", type=Path, help="Ruta del archivo .ogg de entrada")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Archivo de salida (por defecto usa el mismo nombre con extensión .mp3)",
    )
    parser.add_argument(
        "--bitrate",
        default="192k",
        help="Bitrate del MP3 generado (por defecto: 192k)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_ogg_input(args.archivo)

    output = args.output or default_output_for(args.archivo)
    convert_ogg_to_mp3(args.archivo, output, args.bitrate)
    print(f"Creado: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
