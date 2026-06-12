"""The fixture harness itself: corpus albums materialise as real tagged files."""

from typing import Any

from mediafile import MediaFile


def by_title(corpus: dict[str, Any], title: str) -> dict[str, Any]:
    return next(a for a in corpus["albums"] if a["title"] == title)


def test_clean_album_round_trips(corpus, materialise):
    album = by_title(corpus, "Cartography for Sleepwalkers")
    directory = materialise(album)
    files = sorted(directory.iterdir())
    assert len(files) == len(album["tracks"])
    assert {p.suffix for p in files} == {".flac", ".mp3"}
    for track, path in zip(album["tracks"], files):
        tags = MediaFile(str(path))
        assert tags.title == track["title"]
        assert tags.artist == album["artist"]
        assert tags.albumartist == album["artist"]
        assert tags.album == album["title"]
        assert tags.year == album["year"]
        assert tags.genre == album["genre"]
        assert tags.track == track["track"]
        assert tags.tracktotal == album["tracktotal"]


def test_sparse_fields_are_truly_absent(corpus, materialise):
    album = by_title(corpus, "Tape Hiss Archipelago")
    directory = materialise(album)
    unnumbered = [t["title"] for t in album["tracks"] if "track" not in t]
    assert unnumbered  # the corpus quirk this test exists for
    for path in directory.iterdir():
        tags = MediaFile(str(path))
        assert tags.year is None
        assert tags.genre is None
        if tags.title in unnumbered:
            assert tags.track is None


def test_feat_credit_is_verbatim(corpus, materialise):
    album = by_title(corpus, "Salt Meridian")
    directory = materialise(album)
    path = next(p for p in directory.iterdir() if "Lowland Frequencies" in p.name)
    tags = MediaFile(str(path))
    assert tags.artist == "Tin Hatch Choir feat. Vesna Holloway"
    assert tags.albumartist == "Tin Hatch Choir"
