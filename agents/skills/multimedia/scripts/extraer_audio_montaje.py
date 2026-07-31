#!/usr/bin/env python3
"""
Extrae un archivo MP3 por cada video dentro de `videos/montaje`.

Por defecto:
- lee todos los archivos de video soportados en `videos/montaje`
- crea un `.mp3` con el mismo nombre base para cada video
- escribe los audios en la misma carpeta

Requiere:
- ffmpeg
- ffprobe

Uso:
    python3 extraer_audio_montaje.py
    python3 extraer_audio_montaje.py --output-dir videos/montaje/audios
    python3 extraer_audio_montaje.py --force
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"No se encontró {cmd[0]}. Instala ffmpeg/ffprobe y vuelve a intentarlo."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffmpeg falló con código {exc.returncode}") from exc


def has_audio(path: Path) -> bool:
    probe = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        str(path),
    ]
    result = subprocess.run(probe, capture_output=True, text=True)
    return result.returncode == 0 and bool(result.stdout.strip())


def video_files(input_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(input_dir.iterdir(), key=lambda item: item.name.lower())
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def default_output_dir(input_dir: Path) -> Path:
    return input_dir


def extract_audio(source: Path, target: Path, bitrate: str) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-c:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        "-ar",
        "44100",
        "-ac",
        "2",
        str(target),
    ]
    run(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extrae el audio de todos los videos de una carpeta a archivos .mp3."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("videos/montaje"),
        help="Carpeta con los videos de entrada (por defecto: videos/montaje)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Carpeta de salida para los MP3 (por defecto: la misma que input-dir)",
    )
    parser.add_argument(
        "--bitrate",
        default="192k",
        help="Bitrate del MP3 generado (por defecto: 192k)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescribe los MP3 existentes",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra qué haría sin ejecutar ffmpeg",
    )
    args = parser.parse_args()

    if not args.input_dir.exists():
        raise SystemExit(f"No existe la carpeta de entrada: {args.input_dir}")
    if not args.input_dir.is_dir():
        raise SystemExit(f"La ruta de entrada no es una carpeta: {args.input_dir}")

    output_dir = args.output_dir or default_output_dir(args.input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    videos = video_files(args.input_dir)
    if not videos:
        raise SystemExit(f"No se encontraron videos compatibles en {args.input_dir}")

    created = 0
    skipped = 0

    for video in videos:
        target = output_dir / f"{video.stem}.mp3"

        if target.exists() and not args.force:
            print(f"Existe, omitiendo: {target}")
            skipped += 1
            continue

        if not has_audio(video):
            print(f"Sin audio, omitiendo: {video.name}")
            skipped += 1
            continue

        if args.dry_run:
            print(f"Generaría: {target} <- {video.name}")
            created += 1
            continue

        extract_audio(video, target, args.bitrate)
        print(f"Creado: {target}")
        created += 1

    print(f"Listo. Creados: {created}, omitidos: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
