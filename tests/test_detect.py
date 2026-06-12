"""Single-album detection: accept one album, refuse anything else by name."""

import shutil

import pytest

from leeks.detect import NotOneAlbum, detect
from test_harness import by_title


def test_one_album_is_accepted(corpus, materialise):
    album = by_title(corpus, "Cartography for Sleepwalkers")
    audio = detect(materialise(album))
    assert len(audio) == len(album["tracks"])


def test_sparse_album_is_accepted(corpus, materialise):
    # Bad metadata never blocks: sparse is still one album.
    album = by_title(corpus, "Tape Hiss Archipelago")
    audio = detect(materialise(album))
    assert len(audio) == len(album["tracks"])


def test_mixed_album_tags_are_refused_by_name(corpus, materialise):
    target = materialise(by_title(corpus, "Cartography for Sleepwalkers"))
    other = materialise(by_title(corpus, "Paper Lung Atlas"))
    for stray in other.iterdir():
        shutil.move(stray, target / stray.name)
    with pytest.raises(NotOneAlbum) as refusal:
        detect(target)
    assert "2 albums" in str(refusal.value)
    assert "Cartography for Sleepwalkers" in str(refusal.value)
    assert "Paper Lung Atlas" in str(refusal.value)
    assert "leek import" in str(refusal.value)


def test_nested_audio_is_refused(corpus, materialise):
    first = materialise(by_title(corpus, "Salt Meridian"))
    materialise(by_title(corpus, "Paper Lung Atlas"))
    parent = first.parent  # the source dir now holds two album directories
    with pytest.raises(NotOneAlbum) as refusal:
        detect(parent)
    assert "subdirectories" in str(refusal.value)
    assert "leek import" in str(refusal.value)


def test_empty_directory_is_refused(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(NotOneAlbum, match="no audio"):
        detect(empty)


def test_non_audio_clutter_alone_is_refused(tmp_path):
    clutter = tmp_path / "scans"
    clutter.mkdir()
    (clutter / "cover.jpg").write_bytes(b"not audio")
    (clutter / "rip.log").write_text("EAC extraction log")
    with pytest.raises(NotOneAlbum, match="no audio"):
        detect(clutter)
