"""Shared test fixtures: the corpus loader and the album materialiser.

The two halves of the fixture corpus combine here: `corpus.toml` provides
the metadata, the tagless tones in `fixtures/audio/` provide the bytes,
and `materialise` writes a corpus album to disk as a directory of
genuinely tagged audio files — sparse fields truly absent, not empty.
"""

import shutil
import tomllib
from pathlib import Path
from typing import Any, Callable

import pytest
from mediafile import MediaFile

FIXTURES = Path(__file__).parent / "fixtures"
AUDIO = FIXTURES / "audio"
TONE_COUNT = 5
# Alternated per track, so every album exercises both formats.
FORMATS = ("flac", "mp3")


@pytest.fixture(autouse=True)
def leeks_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the library root at a throwaway directory for every test."""
    root = tmp_path / "library"
    monkeypatch.setenv("LEEKS_ROOT", str(root))
    return root


@pytest.fixture(scope="session")
def corpus() -> dict[str, Any]:
    with (FIXTURES / "corpus.toml").open("rb") as f:
        return tomllib.load(f)


def materialise_album(album: dict[str, Any], dest: Path) -> Path:
    """Write a corpus album as a directory of tagged audio files."""
    directory = dest / album["title"]
    directory.mkdir(parents=True)
    for position, track in enumerate(album["tracks"]):
        fmt = FORMATS[position % len(FORMATS)]
        tone = AUDIO / f"tone-{position % TONE_COUNT:03d}.{fmt}"
        path = directory / f"{position + 1:02d} {track['title']}.{fmt}"
        shutil.copyfile(tone, path)
        tags = MediaFile(str(path))
        tags.title = track["title"]
        tags.artist = track.get("artist", album["artist"])
        tags.albumartist = album["artist"]
        tags.album = album["title"]
        if "year" in album:
            tags.year = album["year"]
        if "genre" in album:
            tags.genre = album["genre"]
        if "tracktotal" in album:
            tags.tracktotal = album["tracktotal"]
        if "track" in track:
            tags.track = track["track"]
        tags.save()
    return directory


@pytest.fixture
def materialise(tmp_path: Path) -> Callable[[dict[str, Any]], Path]:
    """Materialise a corpus album under a per-test source directory."""

    def _materialise(album: dict[str, Any]) -> Path:
        return materialise_album(album, tmp_path / "source")

    return _materialise
