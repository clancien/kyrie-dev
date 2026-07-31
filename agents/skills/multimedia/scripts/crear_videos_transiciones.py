#!/usr/bin/env python3
"""
Genera un video .mp4 por cada imagen dentro de cada subcarpeta de
`videos/transiciones/`, usando el audio de esa misma carpeta.

Por defecto trabaja con:
- Carpeta raiz: ./videos/transiciones/
- Entrada: subcarpetas con un archivo .mp3 y varias imagenes
- Salida: un .mp4 por cada imagen en la misma subcarpeta

Cada video dura exactamente lo mismo que el archivo de audio de su carpeta
y usa una resolucion parametrizable.

Requisitos:
- ffmpeg
- ffprobe

Ejemplos:
    python3 crear_videos_transiciones.py
    python3 crear_videos_transiciones.py --width 720 --height 1280
    python3 crear_videos_transiciones.py --output-dir videos/salidas
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Iterable


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
AUDIO_EXTENSIONS = {".mp3"}
DEFAULT_INPUT_DIR = Path("videos/transiciones")
DEFAULT_OUTPUT_DIR = Path("videos/transiciones")
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
DEFAULT_FPS = 30
DEFAULT_CRF = 20
DEFAULT_PRESET = "veryfast"


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise SystemExit(
            "No se encontro ffmpeg o ffprobe. Instala ambos y vuelve a intentarlo."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffmpeg fallo con codigo {exc.returncode}: {' '.join(cmd)}") from exc


def find_images(input_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(input_dir.iterdir(), key=lambda p: p.name.lower())
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def find_audio(input_dir: Path) -> Path:
    preferred = input_dir / f"{input_dir.name}.mp3"
    if preferred.is_file():
        return preferred

    fallback = input_dir / "sonido.mp3"
    if fallback.is_file():
        return fallback

    audio_files = [
        path
        for path in sorted(input_dir.iterdir(), key=lambda p: p.name.lower())
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]
    if not audio_files:
        raise FileNotFoundError(f"No se encontro archivo de audio en {input_dir}")
    return audio_files[0]


def get_duration(path: Path) -> float:
    probe = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(probe, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def build_scale_filter(width: int, height: int) -> str:
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        "setsar=1,format=yuv420p"
    )


def iter_output_paths(images: Iterable[Path], output_dir: Path) -> Iterable[tuple[Path, Path]]:
    for image in images:
        yield image, output_dir / f"{image.stem}.mp4"


def create_video_for_image(
    image: Path,
    audio: Path,
    output: Path,
    duration: float,
    width: int,
    height: int,
    fps: int,
    crf: int,
    preset: str,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    filter_chain = build_scale_filter(width, height)

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-framerate",
        str(fps),
        "-i",
        str(image),
        "-stream_loop",
        "-1",
        "-i",
        str(audio),
        "-t",
        f"{duration:.3f}",
        "-vf",
        filter_chain,
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        str(output),
    ]
    run(cmd)


def find_transition_folders(root_dir: Path) -> list[Path]:
    folders: list[Path] = []
    for path in sorted(root_dir.rglob("*"), key=lambda p: (len(p.parts), p.as_posix().lower())):
        if not path.is_dir():
            continue
        if not find_images(path):
            continue
        if not any(
            child.is_file() and child.suffix.lower() in AUDIO_EXTENSIONS
            for child in path.iterdir()
        ):
            continue
        folders.append(path)
    return folders


def output_dir_for(folder: Path, input_root: Path, output_root: Path) -> Path:
    return output_root / folder.relative_to(input_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera un video por cada imagen en cada subcarpeta usando el audio de esa carpeta."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Carpeta raiz que contiene subcarpetas de transiciones. Default: ./videos/transiciones",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Carpeta raiz de salida. Default: ./videos/transiciones",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help="Ancho de salida. Default: 1080",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help="Alto de salida. Default: 1920",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=DEFAULT_FPS,
        help="FPS del video. Default: 30",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=DEFAULT_CRF,
        help="Calidad x264 CRF. Menor = mejor calidad. Default: 20",
    )
    parser.add_argument(
        "--preset",
        default=DEFAULT_PRESET,
        help="Preset de x264. Default: veryfast",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.input_dir.exists():
        raise SystemExit(f"No existe la carpeta de entrada: {args.input_dir}")

    folders = find_transition_folders(args.input_dir)
    if not folders:
        raise SystemExit(
            f"No se encontraron subcarpetas con imagenes y audio en {args.input_dir}"
        )

    total_videos = 0
    for folder in folders:
        audio = find_audio(folder)
        duration = get_duration(audio)
        images = find_images(folder)
        output_dir = output_dir_for(folder, args.input_dir, args.output_dir)

        print(f"Procesando {folder} con audio {audio.name} ({duration:.2f}s)")
        for image, output in iter_output_paths(images, output_dir):
            print(f"  Creando {output.name} desde {image.name}")
            create_video_for_image(
                image=image,
                audio=audio,
                output=output,
                duration=duration,
                width=args.width,
                height=args.height,
                fps=args.fps,
                crf=args.crf,
                preset=args.preset,
            )
            total_videos += 1

    print(f"Listo. Generados {total_videos} videos en {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
