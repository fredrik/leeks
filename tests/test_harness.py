"""The fixture harness itself: corpus albums materialise as real tagged files."""

import unicodedata
from typing import Any

from mediafile import MediaFile


def by_title(corpus: dict[str, Any], title: str) -> dict[str, Any]:
    return next(a for a in corpus["albums"] if a["title"] == title)


def test_clean_album_round_trips(corpus, materialise):
    album = by_title(corpus, "Cartography for Sleepwalkers")
    directory = materialise(album)
    files = sorted(directory.iterdir())
    assert len(files) == len(album["tracks"])
    assert {p.suffix for p in files} == {".flac"}
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


def test_multi_genre_album_writes_several_genre_tags(corpus, materialise):
    # Saltmarsh Telemetry's corpus genre is a list; every track carries the
    # whole set as real, separate genre tags (the multi-genre quirk).
    album = by_title(corpus, "Saltmarsh Telemetry")
    assert isinstance(album["genre"], list) and len(album["genre"]) > 1
    directory = materialise(album)
    for path in directory.iterdir():
        tags = MediaFile(str(path))
        assert tags.genres == album["genre"]


def test_tracks_carry_varied_durations(corpus, materialise):
    # The tones run different lengths (generate.py's DURATIONS, cycled), so a
    # materialised album holds files of genuinely different duration rather than
    # a uniform run. Cartography's five tracks draw tones 0–4: 1, 2, 4, 8, 1 s.
    album = by_title(corpus, "Cartography for Sleepwalkers")
    directory = materialise(album)
    durations = [MediaFile(str(p)).length for p in sorted(directory.iterdir())]
    expected = [1, 2, 4, 8, 1]
    assert len(durations) == len(expected)
    for actual, want in zip(durations, expected):
        assert abs(actual - want) < 0.2
    assert len({round(d) for d in durations}) > 1  # not all the same


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
    path = next(p for p in directory.iterdir() if "Lowland-Frequencies" in p.name)
    tags = MediaFile(str(path))
    assert tags.artist == "Tin Hatch Choir feat. Vesna Holloway"
    assert tags.albumartist == "Tin Hatch Choir"


def test_decomposed_title_survives_verbatim(corpus, materialise):
    # The normalisation trap: track 1 is authored in NFD (decomposed) form
    # while the album title is precomposed NFC. Both must round-trip exactly,
    # neither silently normalised toward the other.
    album = by_title(corpus, "Vägen åter till sjön")
    assert unicodedata.is_normalized("NFC", album["title"])
    track = next(t for t in album["tracks"] if t["track"] == 1)
    decomposed = track["title"]
    assert unicodedata.is_normalized("NFD", decomposed)
    assert not unicodedata.is_normalized("NFC", decomposed)

    directory = materialise(album)
    path = next(p for p in directory.iterdir() if p.name.startswith("01"))
    tags = MediaFile(str(path))
    assert tags.title == decomposed
    assert unicodedata.is_normalized("NFD", tags.title)
