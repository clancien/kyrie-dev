#!/usr/bin/env python3
"""
Create a video montage from existing video files in a folder.

The script:
1. Scans an input directory for supported video files.
2. Normalizes each clip to the same resolution, frame rate, and codec.
3. Adds transitions between clips and exports a single output video.

Requirements:
- ffmpeg
- ffprobe
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import tempfile
import shutil
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import List


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


def run(cmd: List[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Required command not found: {cmd[0]}. Install ffmpeg/ffprobe and try again."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Command failed with exit code {exc.returncode}: {' '.join(cmd)}") from exc


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


def probe_media(path: Path) -> dict:
    probe = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(probe, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def parse_fps(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None


def bytes_to_mb(value: int) -> float:
    return value / (1024 * 1024)


def subtitle_path_for(source: Path) -> Path:
    return source.with_suffix(".srt")


def escape_ffmpeg_filter_path(path: Path) -> str:
    # ffmpeg filter arguments need escaped path separators and quotes.
    escaped = (
        path.as_posix()
        .replace(chr(92), chr(92) + chr(92))
        .replace(":", chr(92) + ":")
        .replace("'", chr(92) + "'")
    )
    return f"'{escaped}'"


def subtitle_alignment(position: str) -> int:
    return {
        "top": 8,
        "middle": 5,
        "bottom": 2,
    }[position]


def subtitle_color_to_ass(value: str) -> str:
    color = value.strip().lstrip("#")
    if len(color) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in color):
        raise SystemExit("Subtitle colors must use 6-digit hex format like #FFFFFF.")
    red = color[0:2]
    green = color[2:4]
    blue = color[4:6]
    return f"&H00{blue}{green}{red}&"


def build_subtitle_force_style(
    subtitle_size: int,
    subtitle_color: str,
    subtitle_outline_size: int,
    subtitle_outline_color: str,
    subtitle_position: str,
) -> str:
    parts = [
        f"FontSize={subtitle_size}",
        f"PrimaryColour={subtitle_color_to_ass(subtitle_color)}",
        f"OutlineColour={subtitle_color_to_ass(subtitle_outline_color)}",
        f"Outline={subtitle_outline_size}",
        "BorderStyle=1",
        f"Alignment={subtitle_alignment(subtitle_position)}",
        "MarginV=24",
    ]
    return ",".join(parts)



def describe_media(path: Path) -> dict:
    data = probe_media(path)
    streams = data.get("streams", [])
    fmt = data.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    return {
        "path": path,
        "size_bytes": path.stat().st_size,
        "duration": float(fmt.get("duration", 0.0) or 0.0),
        "bit_rate": int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
        "video_codec": video_stream.get("codec_name") if video_stream else None,
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "width": video_stream.get("width") if video_stream else None,
        "height": video_stream.get("height") if video_stream else None,
        "fps": parse_fps(video_stream.get("avg_frame_rate")) if video_stream else None,
        "has_audio": audio_stream is not None,
    }


def video_files(input_dir: Path) -> List[Path]:
    files = [
        p
        for p in sorted(input_dir.iterdir(), key=lambda item: item.name.lower())
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return files


def normalize_clip(
    source: Path,
    target: Path,
    width: int,
    height: int,
    fps: int,
    subtitle_size: int,
    subtitle_color: str,
    subtitle_outline_size: int,
    subtitle_outline_color: str,
    subtitle_position: str,
) -> None:
    subtitle_path = subtitle_path_for(source)
    scale_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        "setsar=1"
    )
    vf_filters = [scale_filter]
    if subtitle_path.exists():
        force_style = build_subtitle_force_style(
            subtitle_size,
            subtitle_color,
            subtitle_outline_size,
            subtitle_outline_color,
            subtitle_position,
        )
        vf_filters.append(
            f"subtitles={escape_ffmpeg_filter_path(subtitle_path)}:force_style='{force_style}'"
        )

    base_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vf",
        ",".join(vf_filters),
        "-r",
        str(fps),
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
    ]

    if has_audio(source):
        cmd = base_cmd + [
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(target),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-shortest",
            "-vf",
            ",".join(vf_filters),
            "-r",
            str(fps),
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
            str(target),
        ]

    run(cmd)


def build_montage(
    input_dir: Path,
    output_file: Path,
    shuffle: bool,
    width: int,
    height: int,
    fps: int,
    transition: float,
    subtitle_size: int,
    subtitle_color: str,
    subtitle_outline_size: int,
    subtitle_outline_color: str,
    subtitle_position: str,
) -> dict:
    clips = video_files(input_dir)
    if not clips:
        raise SystemExit(f"No video files found in: {input_dir}")

    if shuffle:
        random.shuffle(clips)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="montaje_") as temp_dir:
        temp_path = Path(temp_dir)
        normalized_paths: List[Path] = []
        durations: List[float] = []
        source_descriptions: List[dict] = []

        for index, clip in enumerate(clips, start=1):
            normalized = temp_path / f"clip_{index:03d}.mp4"
            subtitle_path = subtitle_path_for(clip)
            has_subtitles = subtitle_path.exists()
            print(f"[{index}/{len(clips)}] Normalizing {clip.name}")
            if has_subtitles:
                print(f"    Using subtitles from {subtitle_path.name}")
            normalize_clip(
                clip,
                normalized,
                width,
                height,
                fps,
                subtitle_size,
                subtitle_color,
                subtitle_outline_size,
                subtitle_outline_color,
                subtitle_position,
            )
            normalized_paths.append(normalized)
            durations.append(get_duration(clip))
            source_description = describe_media(clip)
            source_description["subtitle_path"] = subtitle_path if has_subtitles else None
            source_description["has_subtitles"] = has_subtitles
            source_descriptions.append(source_description)

        if len(normalized_paths) == 1:
            print(f"Writing single clip to {output_file}")
            shutil.copyfile(normalized_paths[0], output_file)
            output_description = describe_media(output_file)
            return {
                "output": output_description,
                "sources": source_descriptions,
                "settings": {
                    "input_dir": input_dir,
                    "output_file": output_file,
                    "shuffle": shuffle,
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "transition": transition,
                    "subtitle_size": subtitle_size,
                    "subtitle_color": subtitle_color,
                    "subtitle_outline_size": subtitle_outline_size,
                    "subtitle_outline_color": subtitle_outline_color,
                    "subtitle_position": subtitle_position,
                },
            }

        effective_transitions: List[float] = []
        for index in range(len(durations) - 1):
            effective = min(transition, durations[index] / 2.0, durations[index + 1] / 2.0)
            if effective <= 0:
                raise SystemExit("Transition duration is too small for one of the clips.")
            effective_transitions.append(effective)

        filter_parts: List[str] = []
        for index in range(len(normalized_paths)):
            filter_parts.append(f"[{index}:v]setpts=PTS-STARTPTS[v{index}]")
            filter_parts.append(f"[{index}:a]asetpts=PTS-STARTPTS[a{index}]")

        current_video = "v0"
        current_audio = "a0"
        current_duration = durations[0]

        for index in range(1, len(normalized_paths)):
            fade = effective_transitions[index - 1]
            offset = current_duration - fade
            next_video = f"v{index}"
            next_audio = f"a{index}"
            out_video = f"vx{index}"
            out_audio = f"ax{index}"

            filter_parts.append(
                f"[{current_video}][{next_video}]xfade=transition=fade:duration={fade:.3f}:offset={offset:.3f}[{out_video}]"
            )
            filter_parts.append(
                f"[{current_audio}][{next_audio}]acrossfade=d={fade:.3f}[{out_audio}]"
            )

            current_video = out_video
            current_audio = out_audio
            current_duration = current_duration + durations[index] - fade

        filter_complex = ";".join(filter_parts)

        print(f"Creating montage with transitions into {output_file}")
        run(
            [
                "ffmpeg",
                "-y",
                *sum((["-i", str(path)] for path in normalized_paths), []),
                "-filter_complex",
                filter_complex,
                "-map",
                f"[{current_video}]",
                "-map",
                f"[{current_audio}]",
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
                "-movflags",
                "+faststart",
                str(output_file),
            ]
        )

        output_description = describe_media(output_file)
        return {
            "output": output_description,
            "sources": source_descriptions,
            "settings": {
                "input_dir": input_dir,
                "output_file": output_file,
                "shuffle": shuffle,
                "width": width,
                "height": height,
                "fps": fps,
                "transition": transition,
                "subtitle_size": subtitle_size,
                "subtitle_color": subtitle_color,
                "subtitle_outline_size": subtitle_outline_size,
                "subtitle_outline_color": subtitle_outline_color,
                "subtitle_position": subtitle_position,
            },
        }


def write_report(report_data: dict, report_file: Path) -> None:
    output = report_data["output"]
    sources = report_data["sources"]
    settings = report_data["settings"]

    lines: List[str] = []
    lines.append("Montaje de videos")
    lines.append(f"Generado: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("Salida")
    lines.append(f"Archivo: {output['path']}")
    lines.append(f"Tamaño: {bytes_to_mb(output['size_bytes']):.2f} MB ({output['size_bytes']} bytes)")
    lines.append(f"Duración: {output['duration']:.2f} s")
    if output["bit_rate"]:
        lines.append(f"Bitrate: {output['bit_rate']} bps")
    if output["video_codec"]:
        lines.append(f"Codec de video: {output['video_codec']}")
    if output["audio_codec"]:
        lines.append(f"Codec de audio: {output['audio_codec']}")
    if output["width"] and output["height"]:
        lines.append(f"Resolución: {output['width']}x{output['height']}")
    if output["fps"]:
        lines.append(f"FPS: {output['fps']:.3f}")

    lines.append("")
    lines.append("Ajustes")
    lines.append(f"Directorio de entrada: {settings['input_dir']}")
    lines.append(f"Orden: {'aleatorio' if settings['shuffle'] else 'alfabético'}")
    lines.append(f"Resolución objetivo: {settings['width']}x{settings['height']}")
    lines.append(f"FPS objetivo: {settings['fps']}")
    lines.append(f"Transición: {settings['transition']} s")
    lines.append(f"Tamaño de subtítulos: {settings['subtitle_size']}")
    lines.append(f"Color de subtítulos: {settings['subtitle_color']}")
    lines.append(f"Contorno de subtítulos: {settings['subtitle_outline_size']} px")
    lines.append(f"Posición de subtítulos: {settings['subtitle_position']}")
    lines.append("Calidad de codificación: libx264 CRF 20, audio AAC 192k")

    lines.append("")
    lines.append(f"Videos procesados: {len(sources)}")
    total_source_duration = sum(item["duration"] for item in sources)
    lines.append(f"Duración total de entrada: {total_source_duration:.2f} s")
    lines.append("")
    lines.append("Detalle de videos")
    for index, item in enumerate(sources, start=1):
        lines.append(f"{index}. {item['path'].name}")
        lines.append(f"   Tamaño: {bytes_to_mb(item['size_bytes']):.2f} MB ({item['size_bytes']} bytes)")
        lines.append(f"   Duración: {item['duration']:.2f} s")
        if item["width"] and item["height"]:
            lines.append(f"   Resolución: {item['width']}x{item['height']}")
        if item["fps"]:
            lines.append(f"   FPS: {item['fps']:.3f}")
        if item["video_codec"]:
            lines.append(f"   Codec de video: {item['video_codec']}")
        if item["audio_codec"]:
            lines.append(f"   Codec de audio: {item['audio_codec']}")
        lines.append(f"   Audio: {'sí' if item['has_audio'] else 'no'}")
        lines.append(f"   Subtítulos: {'sí' if item.get('has_subtitles') else 'no'}")
        if item.get("subtitle_path"):
            lines.append(f"   Archivo de subtítulos: {item['subtitle_path'].name}")

    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a montage video from files in a folder."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=Path("videos/montaje"),
        help="Folder containing the source videos. Default: ./videos/montaje",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("montaje.mp4"),
        help="Output montage file. Default: ./montaje.mp4",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Randomize the order of the source videos.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1080,
        help="Target video width. Default: 1080",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1920,
        help="Target video height. Default: 1920",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Target frame rate. Default: 30",
    )
    parser.add_argument(
        "--transition",
        type=float,
        default=1.0,
        help="Transition duration in seconds. Default: 1.0",
    )
    parser.add_argument(
        "--subtitle-size",
        type=int,
        default=12,
        help="Subtitle font size when burning .srt files. Default: 12",
    )
    parser.add_argument(
        "--subtitle-color",
        default="#FFFFFF",
        help="Subtitle text color in hex RGB. Default: #FFFFFF",
    )
    parser.add_argument(
        "--subtitle-outline-size",
        type=int,
        default=2,
        help="Subtitle outline thickness in pixels. Default: 2",
    )
    parser.add_argument(
        "--subtitle-outline-color",
        default="#000000",
        help="Subtitle outline color in hex RGB. Default: #000000",
    )
    parser.add_argument(
        "--subtitle-position",
        choices=("top", "middle", "bottom"),
        default="bottom",
        help="Subtitle vertical position. Default: bottom",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_data = build_montage(
        input_dir=args.input_dir,
        output_file=args.output,
        shuffle=args.shuffle,
        width=args.width,
        height=args.height,
        fps=args.fps,
        transition=args.transition,
        subtitle_size=args.subtitle_size,
        subtitle_color=args.subtitle_color,
        subtitle_outline_size=args.subtitle_outline_size,
        subtitle_outline_color=args.subtitle_outline_color,
        subtitle_position=args.subtitle_position,
    )
    report_file = args.output.with_suffix(".txt")
    write_report(report_data, report_file)
    print(f"Metadata report written to {report_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
