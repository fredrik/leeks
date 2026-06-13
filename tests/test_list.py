"""The list query: the merged view in shelf order, narrowed by terms."""

from typing import Any

from leeks import library
from test_harness import by_title


def add_corpus(corpus, materialise):
    for album in corpus["albums"]:
        library.add(materialise(album))


def shelf_key(album: "library.Listed") -> tuple[Any, ...]:
    """The shelf-order sort the SQL ORDER BY must reproduce (ADR 0011).

    SQLite's NOCASE folds only ASCII A–Z, so a faithful reference folds
    the same and lets non-ASCII fall through to its code point — Åsa
    after the ASCII artists, as on the real shelf.
    """

    def fold(text: str) -> str:
        return "".join(c.lower() if "A" <= c <= "Z" else c for c in text)

    return (
        fold(album.artist or "Unknown Artist"),
        album.year is None,
        album.year or 0,
        fold(album.title),
    )


def test_an_empty_library_lists_nothing():
    assert library.list_albums() == []


def test_the_whole_corpus_comes_back_in_shelf_order(corpus, materialise):
    add_corpus(corpus, materialise)
    listed = library.list_albums()
    # Every corpus album is on the shelf...
    assert {(album.artist, album.title) for album in listed} == {
        (album["artist"], album["title"]) for album in corpus["albums"]
    }
    # ...and the query's order is the shelf order, whatever the corpus grows.
    assert listed == sorted(listed, key=shelf_key)


def test_listed_albums_carry_year_and_track_count(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    [cartography] = library.list_albums()
    assert cartography.year == 2019
    assert cartography.tracks == 5


def test_missing_years_shelve_last_within_an_artist(shelve):
    shelve("Undated", artist="Quiet Pines")
    shelve("Later", artist="Quiet Pines", year=2003)
    shelve("Early", artist="Quiet Pines", year=1999)
    assert [album.title for album in library.list_albums()] == [
        "Early",
        "Later",
        "Undated",
    ]


def test_shelf_order_folds_artist_case(shelve):
    shelve("Second", artist="alpha gamma")
    shelve("First", artist="Alpha Beta")
    assert [album.title for album in library.list_albums()] == ["First", "Second"]


def test_terms_reach_artist_title_and_year(corpus, materialise):
    add_corpus(corpus, materialise)
    by_artist = library.list_albums(["HATCH"])
    assert {album.title for album in by_artist} == {
        "Cartography for Sleepwalkers",
        "Salt Meridian",
    }
    by_year = library.list_albums(["2017"])
    assert [album.title for album in by_year] == ["Paper Lung Atlas"]
    by_title_term = library.list_albums(["archipelago"])
    assert [album.title for album in by_title_term] == ["Tape Hiss Archipelago"]


def test_terms_and_together(corpus, materialise):
    add_corpus(corpus, materialise)
    assert [album.title for album in library.list_albums(["tin", "salt"])] == [
        "Salt Meridian"
    ]
    assert library.list_albums(["tin", "archipelago"]) == []


def test_a_term_is_text_not_a_pattern(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    assert library.list_albums(["%"]) == []
    assert library.list_albums(["_"]) == []


def test_an_artistless_album_sits_in_the_unknown_bucket(shelve):
    shelve("Mystery Tape")
    shelve("Marsh Songs", artist="Tully Marsh")
    shelve("Visions", artist="Wren Adler")
    listed = library.list_albums()
    # T(ully) < U(nknown Artist) < W(ren).
    assert [album.title for album in listed] == [
        "Marsh Songs",
        "Mystery Tape",
        "Visions",
    ]
    assert listed[1].artist is None
    # Terms match data, never the display fallback.
    assert library.list_albums(["unknown"]) == []
