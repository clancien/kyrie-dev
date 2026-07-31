#!/usr/bin/env python3
"""
Unified dispatcher for the multimedia skill scripts.

Examples:
    python3 multimedia_api.py crear-video-con-fotos --profile madre
    python3 multimedia_api.py montaje --input-dir videos/montaje --output salida.mp4
    python3 multimedia_api.py transcript audio.mp3 --format srt
    python3 multimedia_api.py convertir-ogg-a-mp3 audio.ogg
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_MAP = {
    "crear-video-con-fotos": "crear_video_con_fotos.py",
    "crear-videos-transiciones": "crear_videos_transiciones.py",
    "montaje": "montaje.py",
    "crop-9-16": "crop_9_16.py",
    "recortar-audio": "recortar_audio.py",
    "extraer-audio": "extraer_audio_montaje.py",
    "convertir-ogg-a-mp3": "convertir_ogg_a_mp3.py",
    "batch-whisper-srt": "batch_whisper_to_srt.py",
    "transcript": "transcript.py",
}


def script_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def run_script(target: Path, args: list[str]) -> int:
    if not target.exists():
        raise SystemExit(f"No existe el script objetivo: {target}")

    result = subprocess.run([sys.executable, str(target), *args])
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dispatcher unificado para los scripts multimedia.",
        epilog=(
            "Comandos disponibles: "
            + ", ".join(f"{command} -> {script}" for command, script in SCRIPT_MAP.items())
        ),
    )
    parser.add_argument("command", choices=sorted(SCRIPT_MAP.keys()), help="Script o flujo a ejecutar")
    return parser


def main() -> int:
    parser = build_parser()
    args, remainder = parser.parse_known_args()
    target = script_path(SCRIPT_MAP[args.command])
    return run_script(target, remainder)


if __name__ == "__main__":
    raise SystemExit(main())
