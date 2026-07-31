"""Reusable audio conversion helpers for the multimedia skill."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise SystemExit("No se encontró ffmpeg. Instálalo y vuelve a intentarlo.") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ffmpeg falló con código {exc.returncode}") from exc


def ensure_ogg_input(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"No existe el archivo de entrada: {path}")
    if not path.is_file():
        raise SystemExit(f"La ruta de entrada no es un archivo: {path}")
    if path.suffix.lower() != ".ogg":
        raise SystemExit("Este script está pensado para archivos .ogg")


def default_output_for(input_file: Path) -> Path:
    return input_file.with_suffix(".mp3")


def convert_ogg_to_mp3(source: Path, output: Path, bitrate: str = "192k") -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
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
        "-map_metadata",
        "0",
        str(output),
    ]
    run(cmd)
