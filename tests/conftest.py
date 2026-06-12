"""Shared test fixtures, built on the corpus materialiser.

The loader and materialiser live in fixtures/materialise.py — also a
command-line tool for building scratch albums — and the fixtures here
wrap them with per-test temporary directories.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import pytest
from fixtures.materialise import corpus as load_corpus
from fixtures.materialise import materialise_album
from sqlalchemy import select

from leeks import db
from leeks.orm import Album, Artist, Track


@pytest.fixture(autouse=True)
def leeks_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the library root at a throwaway directory for every test."""
    root = tmp_path / "library"
    monkeypatch.setenv("LEEKS_ROOT", str(root))
    return root


@pytest.fixture(scope="session")
def corpus() -> dict[str, Any]:
    return load_corpus()


@pytest.fixture
def materialise(tmp_path: Path) -> Callable[[dict[str, Any]], Path]:
    """Materialise a corpus album under a per-test source directory."""

    def _materialise(album: dict[str, Any]) -> Path:
        return materialise_album(album, tmp_path / "source")

    return _materialise


@pytest.fixture
def shelve() -> Callable[..., None]:
    """Plant an album row directly, bypassing the add pipeline.

    For shapes the corpus cannot materialise — an album with no artist
    claim, or year mixes within one artist — where only the merged view
    matters, not the claims behind it.
    """

    def _shelve(
        title: str, artist: str | None = None, year: int | None = None, tracks: int = 1
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        with db.session() as session:
            artist_id = None
            if artist is not None:
                row = session.scalar(select(Artist).where(Artist.name == artist))
                if row is None:
                    row = Artist(name=artist)
                    session.add(row)
                    session.flush()
                artist_id = row.id
            album = Album(title=title, artist_id=artist_id, year=year, added=now)
            session.add(album)
            session.flush()
            for number in range(tracks):
                session.add(
                    Track(album_id=album.id, title=f"Track {number + 1}", added=now)
                )
            session.commit()

    return _shelve
