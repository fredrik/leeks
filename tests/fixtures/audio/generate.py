"""Generate tiny tagless audio fixtures for the test suite.

Synthesizes short sine-wave tones with ffmpeg, in both FLAC and MP3.
The files carry no metadata tags; tagging is applied later from a
separate metadata corpus. Each file gets a distinct tone frequency and
a distinct duration so no two files are byte-identical and the corpus
exercises a spread of track lengths.

Durations double from 1 to 8 seconds — still small, but varied enough
that duration-bearing output (e.g. `leek show`) shows real differences
rather than a column of identical times.

Usage:
    python generate.py --count 5 --output-dir tests/fixtures/audio
"""

import argparse
import subprocess
import sys
from pathlib import Path

SAMPLE_RATE = 8000  # Hz; tiny files — these exist to be parsed, not heard.
DURATIONS = (1, 2, 4, 8)  # seconds, cycled across tone indices; doubling 1–8.
BASE_FREQUENCY = 220  # Hz; each file steps up from here.
FREQUENCY_STEP = 110  # Hz between consecutive files.


def generate(index: int, fmt: str, output_dir: Path) -> Path:
    frequency = BASE_FREQUENCY + index * FREQUENCY_STEP
    duration = DURATIONS[index % len(DURATIONS)]
    path = output_dir / f"tone-{index:03d}.{fmt}"
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={frequency}:duration={duration}:sample_rate={SAMPLE_RATE}",
        "-ac",
        "1",
        "-map_metadata",
        "-1",  # strip all metadata
        "-fflags",
        "+bitexact",  # no encoder tag / timestamps in the container
        "-flags:a",
        "+bitexact",
        str(path),
    ]
    subprocess.run(command, check=True, capture_output=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate tiny tagless audio fixtures for the test suite."
    )
    parser.add_argument(
        "--count", type=int, default=5, help="files per format (default: 5)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent,
        help="where to write the files",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index in range(args.count):
        for fmt in ("flac", "mp3"):
            path = generate(index, fmt, args.output_dir)
            print(path)


if __name__ == "__main__":
    sys.exit(main())
