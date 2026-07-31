#!/usr/bin/env python3
"""
Recorta un video al centro y lo exporta en formato 9:16.

Por defecto genera salida 1080x1920, que es un tamaño estándar para
reels, shorts y TikTok.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def build_filter(width: int, height: int, mode: str) -> str:
    if mode == "crop":
        # Escala para cubrir el marco y luego recorta al centro.
        return (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1"
        )

    # Escala para que todo el video entre y completa con bordes negros.
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    )


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise SystemExit("No se encontró ffmpeg. Instálalo y vuelve a intentarlo.") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffmpeg falló con código {exc.returncode}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recorta un video al formato 9:16 con salida exacta."
    )
    parser.add_argument("input", type=Path, help="Video de entrada")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("salida_9x16.mp4"),
        help="Archivo de salida (por defecto: salida_9x16.mp4)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1080,
        help="Ancho de salida (por defecto: 1080)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1920,
        help="Alto de salida (por defecto: 1920)",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=18,
        help="Calidad x264 CRF (menor es mejor; por defecto: 18)",
    )
    parser.add_argument(
        "--preset",
        default="medium",
        help="Preset de x264 (por defecto: medium)",
    )
    parser.add_argument(
        "--mode",
        choices=("crop", "extend"),
        default="crop",
        help="Modo de ajuste: crop recorta al centro; extend agrega bordes negros.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"No existe el archivo de entrada: {args.input}")

    if args.width * 16 != args.height * 9:
        raise SystemExit("La salida debe respetar exactamente la relación 9:16.")

    filter_chain = build_filter(args.width, args.height, args.mode)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(args.input),
        "-vf",
        filter_chain,
        "-c:v",
        "libx264",
        "-crf",
        str(args.crf),
        "-preset",
        args.preset,
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(args.output),
    ]

    run(cmd)
    print(f"Creado: {args.output} ({args.width}x{args.height}, mode={args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
