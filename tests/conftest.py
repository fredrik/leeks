"""Shared test fixtures, built on the corpus materialiser.

The loader and materialiser live in fixtures/materialise.py — also a
command-line tool for building scratch albums — and the fixtures here
wrap them with per-test temporary directories.
"""

from pathlib import Path
from typing import Any, Callable

import pytest
from fixtures.materialise import corpus as load_corpus
from fixtures.materialise import materialise_album


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
