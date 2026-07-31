#!/usr/bin/env python3
"""
Create a 30-second video from photos in a folder and background music.

Profiles:
- abuelos: ./videos/abuelos/ ... ./videos/abuelos/abuelos_30s.mp4
- madre:   ./videos/madre/ ...   ./videos/madre/madre_30s.mp4

Requirements:
- ffmpeg

Usage:
    python3 crear_video_con_fotos.py
    python3 crear_video_con_fotos.py --profile madre
    python3 crear_video_con_fotos.py --profile madre --audio-start 12.5
    python3 crear_video_con_fotos.py --input-dir videos/madre --music videos/madre/musica.mp3 --output salida.mp4
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
DEFAULT_DURATION = 30.0
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
DEFAULT_FPS = 30
DEFAULT_AUDIO_START = 0.0

PROFILES: Dict[str, Dict[str, Path]] = {
    "abuelos": {
        "input_dir": Path("videos/abuelos"),
        "music": Path("videos/abuelos/musica.mp3"),
        "output": Path("videos/abuelos/abuelos_30s.mp4"),
        "fallback_dir": Path("video/abuelos"),
        "fallback_music": Path("video/abuelos/musica.mp3"),
        "temp_prefix": "abuelos_",
    },
    "madre": {
        "input_dir": Path("videos/madre"),
        "music": Path("videos/madre/musica.mp3"),
        "output": Path("videos/madre/madre_30s.mp4"),
        "fallback_dir": Path("video/madre"),
        "fallback_music": Path("video/madre/musica.mp3"),
        "temp_prefix": "madre_",
    },
}


def run(cmd: List[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Required command not found: {cmd[0]}. Install ffmpeg and try again."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Command failed with exit code {exc.returncode}: {' '.join(cmd)}") from exc


def resolve_path(primary: Path, fallback: Path) -> Path:
    if primary.exists():
        return primary
    if fallback.exists():
        return fallback
    raise SystemExit(f"Could not find either {primary} or {fallback}")


def find_images(input_dir: Path) -> List[Path]:
    return [
        path
        for path in sorted(input_dir.iterdir(), key=lambda p: p.name.lower())
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
        and path.name.lower() != "musica.mp3"
    ]


def build_filter(inputs: int, width: int, height: int, fps: int) -> str:
    parts: List[str] = []
    for index in range(inputs):
        parts.append(
            f"[{index}:v]"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1,format=yuv420p[v{index}]"
        )
    concat_inputs = "".join(f"[v{index}]" for index in range(inputs))
    parts.append(f"{concat_inputs}concat=n={inputs}:v=1:a=0,fps={fps}[video]")
    return ";".join(parts)


def create_video(
    input_dir: Path,
    music_file: Path,
    output_file: Path,
    duration: float,
    width: int,
    height: int,
    fps: int,
    audio_start: float,
    temp_prefix: str,
) -> None:
    images = find_images(input_dir)
    if not images:
        raise SystemExit(f"No image files found in {input_dir}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    seconds_per_image = duration / len(images)
    if seconds_per_image < 0.5:
        raise SystemExit(
            f"Too many photos for a {duration:.0f}s video. "
            f"Found {len(images)} images, which would give {seconds_per_image:.2f}s per image."
        )

    with tempfile.TemporaryDirectory(prefix=temp_prefix) as temp_dir:
        temp_path = Path(temp_dir)
        prepared_inputs: List[Path] = []

        for index, image in enumerate(images, start=1):
            prepared = temp_path / f"image_{index:03d}.mp4"
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(image),
                    "-t",
                    f"{seconds_per_image:.3f}",
                    "-r",
                    str(fps),
                    "-vf",
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
                    f"setsar=1,format=yuv420p",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "20",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(prepared),
                ]
            )
            prepared_inputs.append(prepared)

        audio_tmp = temp_path / "audio.mp3"
        run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{audio_start:.3f}",
                "-i",
                str(music_file),
                "-vn",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                "-ar",
                "44100",
                "-ac",
                "2",
                str(audio_tmp),
            ]
        )

        filter_complex = build_filter(len(prepared_inputs), width, height, fps)
        ffmpeg_cmd: List[str] = ["ffmpeg", "-y"]
        for prepared in prepared_inputs:
            ffmpeg_cmd.extend(["-i", str(prepared)])
        ffmpeg_cmd.extend(["-stream_loop", "-1", "-i", str(audio_tmp)])
        ffmpeg_cmd.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                "[video]",
                "-map",
                f"{len(prepared_inputs)}:a:0",
                "-t",
                f"{duration:.3f}",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
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
                str(output_file),
            ]
        )
        run(ffmpeg_cmd)


def parse_args(default_profile: str = "abuelos") -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a 30-second video from photos and music."
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        default=default_profile,
        help=f"Preset with default input, music and output paths. Default: {default_profile}",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Folder with the photos. Defaults to the selected profile.",
    )
    parser.add_argument(
        "--music",
        type=Path,
        default=None,
        help="Background music file. Defaults to the selected profile.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output video file. Defaults to the selected profile.",
    )
    parser.add_argument(
        "--duration",
        "--duracion",
        type=float,
        default=DEFAULT_DURATION,
        help="Total duration in seconds. Default: 30",
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Video width. Default: 1080")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="Video height. Default: 1920")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help="Frames per second. Default: 30")
    parser.add_argument(
        "--audio-start",
        type=float,
        default=DEFAULT_AUDIO_START,
        help="Second inside the music file where audio should start. Default: 0",
    )

    args = parser.parse_args()
    defaults = PROFILES[args.profile]
    args.input_dir = args.input_dir or defaults["input_dir"]
    args.music = args.music or defaults["music"]
    args.output = args.output or defaults["output"]
    return args


def main(default_profile: str = "abuelos", duration: float | None = None) -> None:
    args = parse_args(default_profile=default_profile)
    defaults = PROFILES[args.profile]
    if duration is not None:
        args.duration = duration

    input_dir = resolve_path(args.input_dir, defaults["fallback_dir"])
    music_file = resolve_path(args.music, defaults["fallback_music"])

    create_video(
        input_dir=input_dir,
        music_file=music_file,
        output_file=args.output,
        duration=args.duration,
        width=args.width,
        height=args.height,
        fps=args.fps,
        audio_start=args.audio_start,
        temp_prefix=defaults["temp_prefix"],
    )

    print(f"Created: {args.output}")


if __name__ == "__main__":
    main()
