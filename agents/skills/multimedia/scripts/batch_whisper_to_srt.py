#!/usr/bin/env python3
"""
Batch-generate .srt files for audio files in videos/montaje.

Rules:
 - Only process .mp3 files.
 - The language is inferred from the filename suffix before .mp3:
   *.es.mp3 -> Spanish
   *.fr.mp3 -> French
 - Files with any other suffix are ignored.
 - For accepted files, call the Whisper CLI and write an .srt file
   with the same base name as the original audio file.

Example:
  videos/montaje/clip.es.mp3 -> videos/montaje/clip.es.srt
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SUPPORTED_LANGUAGES = {"es", "fr"}
WHISPER_BIN = Path("/home/clancien/.local/share/pipx/venvs/openai-whisper/bin/whisper")


def infer_language(audio_path: Path) -> str | None:
    stem_parts = audio_path.stem.split(".")
    if len(stem_parts) < 2:
        return None
    language = stem_parts[-1].lower()
    return language if language in SUPPORTED_LANGUAGES else None


def main() -> int:
    base_dir = Path("videos/montaje")

    if not base_dir.exists():
        print(f"Directory not found: {base_dir}", file=sys.stderr)
        return 1

    if not WHISPER_BIN.exists():
        print(f"Whisper binary not found: {WHISPER_BIN}", file=sys.stderr)
        return 1

    mp3_files = sorted(base_dir.glob("*.mp3"))
    if not mp3_files:
        print(f"No .mp3 files found in {base_dir}", file=sys.stderr)
        return 0

    for audio_path in mp3_files:
        language = infer_language(audio_path)
        if language is None:
            print(f"Skipping: {audio_path.name}", file=sys.stderr)
            continue

        output_path = audio_path.with_suffix(".srt")
        if output_path.exists():
            print(f"Skipping existing subtitle: {output_path.name}", file=sys.stderr)
            continue

        cmd = [
            str(WHISPER_BIN),
            str(audio_path),
            "--model",
            "large-v3-turbo",
            "--language",
            language,
            "--output_format",
            "srt",
            "--output_dir",
            str(base_dir),
        ]

        print(f"Processing: {audio_path.name} -> {output_path.name}", file=sys.stderr)
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Failed: {audio_path.name}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
