"""Materialise the fixture corpus as real tagged audio files.

The test suite imports materialise_album from here; the command line
builds scratch albums to play with:

    uv run python tests/fixtures/materialise.py /tmp/leeks-scratch
    uv run python tests/fixtures/materialise.py /tmp/leeks-scratch --album "Salt Meridian"

Sparse corpus fields are genuinely absent from the written files.
"""

import argparse
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

from mediafile import MediaFile

FIXTURES = Path(__file__).parent
AUDIO = FIXTURES / "audio"
TONE_COUNT = 5


def corpus() -> dict[str, Any]:
    with (FIXTURES / "corpus.toml").open("rb") as handle:
        return tomllib.load(handle)


def _dashed(text: str) -> str:
    # Dashes, not spaces, in materialised paths: kinder to shells.
    return text.replace(" ", "-")


def materialise_album(album: dict[str, Any], dest: Path) -> Path:
    """Write a corpus album as a directory of tagged audio files."""
    # One format per album, set by the corpus entry's optional "format" key (default flac).
    fmt = album.get("format", "flac")
    directory = dest / _dashed(album["title"])
    directory.mkdir(parents=True)
    for position, track in enumerate(album["tracks"]):
        tone = AUDIO / f"tone-{position % TONE_COUNT:03d}.{fmt}"
        path = directory / f"{position + 1:02d}-{_dashed(track['title'])}.{fmt}"
        shutil.copyfile(tone, path)
        tags = MediaFile(str(path))
        tags.title = track["title"]
        tags.artist = track.get("artist", album["artist"])
        tags.albumartist = album["artist"]
        tags.album = album["title"]
        if "year" in album:
            tags.year = album["year"]
        if "genre" in album:
            # A list materialises as several genre tags (ADR 0022); a bare
            # string as one. mediafile writes the format-native multi-value.
            genre = album["genre"]
            tags.genres = genre if isinstance(genre, list) else [genre]
        if "tracktotal" in album:
            tags.tracktotal = album["tracktotal"]
        if "track" in track:
            tags.track = track["track"]
        tags.save()
    return directory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialise the fixture corpus as tagged audio files."
    )
    parser.add_argument("dest", type=Path, help="directory to materialise into")
    parser.add_argument(
        "--album", help="materialise only the album with this title (default: all)"
    )
    args = parser.parse_args()

    albums = corpus()["albums"]
    if args.album is not None:
        albums = [a for a in albums if a["title"] == args.album]
        if not albums:
            parser.error(f"no corpus album titled {args.album!r}")
    try:
        for album in albums:
            print(materialise_album(album, args.dest))
    except FileExistsError as collision:
        sys.exit(f"already materialised: {collision.filename}")


if __name__ == "__main__":
    main()
