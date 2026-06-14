"""The list query: the merged view in shelf order, narrowed by terms."""

from typing import Any

import pytest

from leeks import library
from test_harness import by_title


def add_corpus(corpus, materialise):
    for album in corpus["albums"]:
        library.add(materialise(album))


def shelf_key(album: "library.Listed") -> tuple[Any, ...]:
    """The shelf-order sort the SQL ORDER BY must reproduce (ADR 0011).

    The library sorts in Swedish order at the connection (ADR 0026), so a
    faithful reference uses the same sort key — Åsa shelves last, after Z, not
    among the A's.
    """
    from leeks.db import sort_key

    return (
        sort_key(album.artist or "Unknown Artist"),
        album.year is None,
        album.year or 0,
        sort_key(album.title),
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


def test_listed_albums_carry_their_year(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    [cartography] = library.list_albums()
    assert cartography.year == 2019


def test_listed_albums_carry_their_genres(corpus, materialise):
    # The shelf carries the merged genre set, folded-name ordered, same as the
    # depth read (ADR 0022); an untagged album carries an empty set.
    library.add(materialise(by_title(corpus, "Genrezvous Telemetry")))
    library.add(materialise(by_title(corpus, "Tape Hiss Archipelago")))
    listed = {album.title: album for album in library.list_albums()}
    assert listed["Genrezvous Telemetry"].genres == [
        "Ambient",
        "Dub Techno",
        "Field Recording",
    ]
    assert listed["Tape Hiss Archipelago"].genres == []


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


def test_shelf_order_sorts_swedish(shelve):
    # Å is a letter of its own, sorting after Z — Åsa shelves last (ADR 0026).
    shelve("Ringer", artist="Bo")
    shelve("Snön", artist="Åsa")
    shelve("Alm", artist="Alm")
    shelve("Wave", artist="Öje")
    assert [album.title for album in library.list_albums()] == [
        "Alm",
        "Ringer",
        "Snön",  # Åsa
        "Wave",  # Öje — ö sorts after å
    ]


def test_terms_fold_case_and_accents(corpus, materialise):
    # The åäö specimen: case-insensitive, accent-insensitive, NFD-insensitive.
    library.add(materialise(by_title(corpus, "Vägen åter till sjön")))
    for term in ["åsa", "Åsa", "asa", "vinterhök", "vinterhok"]:
        assert [album.artist for album in library.list_albums([term])] == [
            "Åsa Vinterhök"
        ], term


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


# --- leek list --tracks: the tree walk (ADR 0013) ---


def test_an_empty_library_lists_no_tracks():
    assert library.list_tracks() == []


def test_tracks_walk_the_library_tree(corpus, materialise):
    add_corpus(corpus, materialise)
    tracks = library.list_tracks()
    # Every corpus track is on the walk...
    assert len(tracks) == sum(len(album["tracks"]) for album in corpus["albums"])
    # ...grouped by album, in exactly the shelf order list_albums defines:
    # the listing walks the tree, and the two never disagree (ADR 0010/0013).
    walked: list[int] = []
    for track in tracks:
        if not walked or walked[-1] != track.album_id:
            walked.append(track.album_id)
    assert walked == [album.id for album in library.list_albums()]


def test_tracks_within_an_album_order_by_number_then_assembly(corpus, materialise):
    # Tape Hiss Archipelago: two numbered tracks, two unnumbered. Numbered
    # first in number order; the unnumbered pair in assembly order — source
    # filename, so Sodium (02) before Pylon (03), the tie-break Track.id
    # carries from tags.assemble.
    library.add(materialise(by_title(corpus, "Tape Hiss Archipelago")))
    assert [track.title for track in library.list_tracks()] == [
        "Arcade Rain",
        "Dust on the Faders",
        "Sodium Light Study",
        "Pylon Hum",
    ]


def test_a_track_shows_its_overriding_credit(corpus, materialise):
    # Lowland Frequencies is credited "Tin Hatch Choir feat. Vesna Holloway"
    # on the track: that override is the effective artist shown (ADR 0013,
    # option A), while the row still sorts under the album artist's shelf.
    # Its siblings, with no override, fall back to the album artist.
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    tracks = library.list_tracks()
    [lowland] = [t for t in tracks if t.title == "Lowland Frequencies"]
    assert lowland.artist == "Tin Hatch Choir feat. Vesna Holloway"
    others = [t for t in tracks if t.title != "Lowland Frequencies"]
    assert all(t.artist == "Tin Hatch Choir" for t in others)


def test_a_duplicate_track_title_lists_both(corpus, materialise):
    # "Glass Harbour" is two different songs on two albums (corpus quirk).
    add_corpus(corpus, materialise)
    harbours = [t for t in library.list_tracks() if t.title == "Glass Harbour"]
    assert len(harbours) == 2
    assert {t.album for t in harbours} == {
        "Cartography for Sleepwalkers",
        "Paper Lung Atlas",
    }
    assert harbours[0].id != harbours[1].id


def test_track_terms_match_the_title(corpus, materialise):
    add_corpus(corpus, materialise)
    harbours = library.list_tracks(["harbour"])
    assert {t.title for t in harbours} == {"Glass Harbour"}
    assert len(harbours) == 2  # case-insensitive, both songs


def test_track_terms_reach_up_to_the_album(corpus, materialise):
    # Bare track terms reach up the tree (ADR 0029): "tin hatch" matches the
    # album artist, so every track of the two Tin Hatch Choir albums comes
    # back — including ones whose own title holds no "tin hatch".
    add_corpus(corpus, materialise)
    reached = library.list_tracks(["tin hatch"])
    assert {t.album for t in reached} == {
        "Cartography for Sleepwalkers",
        "Salt Meridian",
    }
    assert "Meridian Line" in {t.title for t in reached}  # matched via the album


def test_track_terms_reach_the_album_title(corpus, materialise):
    # The OK Computer case: a bare term on the album title returns its tracks.
    add_corpus(corpus, materialise)
    tracks = library.list_tracks(["cartography"])
    assert {t.album for t in tracks} == {"Cartography for Sleepwalkers"}
    assert len(tracks) == 5  # all of the album, none reached by title alone


def test_a_track_term_is_text_not_a_pattern(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    assert library.list_tracks(["%"]) == []
    assert library.list_tracks(["_"]) == []


# --- leek list --artists: every artist row, in name order (ADR 0013) ---


def name_key(name: str) -> str:
    """Sorted like the library's SORT collation: Swedish order (ADR 0026)."""
    from leeks.db import sort_key

    return sort_key(name)


def test_an_empty_library_lists_no_artists():
    assert library.list_artists() == []


def test_artists_are_every_row_in_name_order(corpus, materialise):
    add_corpus(corpus, materialise)
    names = [artist.name for artist in library.list_artists()]
    # Every distinct credit the corpus tags — album artists and the raw
    # track-level feat. credits both — is an artist row (ADR 0013).
    expected = {album["artist"] for album in corpus["albums"]}
    expected |= {
        track["artist"]
        for album in corpus["albums"]
        for track in album["tracks"]
        if "artist" in track
    }
    assert set(names) == expected
    assert "Tin Hatch Choir feat. Vesna Holloway" in expected  # the wart, present
    # Swedish name order, whatever the corpus grows (Åsa Vinterhök last).
    assert names == sorted(names, key=name_key)


def test_an_artistless_album_contributes_no_artist_row(shelve):
    # Unknown Artist is a shelf fallback, not an artist entity (ADR 0011);
    # an album with no artist claim adds no row to --artists.
    shelve("Mystery Tape")
    assert library.list_artists() == []


def test_artist_terms_match_the_name(corpus, materialise):
    add_corpus(corpus, materialise)
    assert {a.name for a in library.list_artists(["hatch"])} == {
        "Tin Hatch Choir",
        "Tin Hatch Choir feat. Vesna Holloway",
    }
    # A substring reaches into the raw credit string too.
    assert {a.name for a in library.list_artists(["holloway"])} == {
        "Vesna Holloway",
        "Tin Hatch Choir feat. Vesna Holloway",
    }


# --- field-qualified terms: [field:]value (ADR 0029) ---


def test_qualified_terms_name_one_field(corpus, materialise):
    add_corpus(corpus, materialise)
    assert [a.title for a in library.list_albums(["year:2017"])] == ["Paper Lung Atlas"]
    assert [a.title for a in library.list_albums(["artist:holloway"])] == [
        "Paper Lung Atlas"
    ]
    assert {a.title for a in library.list_albums(["title:meridian"])} == {
        "Salt Meridian"
    }
    # A qualified term stays on its field: "hatch" is an artist, not a title.
    assert library.list_albums(["title:hatch"]) == []


def test_track_qualified_terms_name_one_field(corpus, materialise):
    add_corpus(corpus, materialise)
    # album: names the host album; the four Salt Meridian tracks come back.
    salt = library.list_tracks(["album:salt meridian"])
    assert {t.album for t in salt} == {"Salt Meridian"}
    assert len(salt) == 4


def test_a_track_number_is_queryable_but_not_bare(corpus, materialise):
    add_corpus(corpus, materialise)
    # number: matches the track number explicitly (it is qualified-only — a
    # bare term never fans across it, ADR 0029).
    threes = library.list_tracks(["number:3"])
    assert threes
    assert all(str(t.number) == "3" for t in threes)


def test_id_selects_one_row_exactly(corpus, materialise):
    add_corpus(corpus, materialise)
    target = library.list_albums(["year:2017"])[0]
    assert [a.id for a in library.list_albums([f"id:{target.id}"])] == [target.id]


def test_an_unknown_field_is_a_loud_error(corpus, materialise):
    add_corpus(corpus, materialise)
    with pytest.raises(library.QueryError):
        library.list_albums(["bogus:anything"])


def test_a_non_numeric_id_is_a_loud_error(corpus, materialise):
    add_corpus(corpus, materialise)
    with pytest.raises(library.QueryError):
        library.list_albums(["id:abc"])


# --- genre: a set-valued field, filtered by membership (ADR 0023/0029) ---


def test_genre_filters_albums_by_membership(corpus, materialise):
    add_corpus(corpus, materialise)
    # Substring and folded: "folk" matches both "Folk" and "Nordic Folk".
    assert {a.title for a in library.list_albums(["genre:folk"])} == {
        "Paper Lung Atlas",
        "Vägen åter till sjön",
    }
    # A multi-genre album matches on any one of its genres (the set, ADR 0022).
    assert {a.title for a in library.list_albums(["genre:techno"])} == {
        "Genrezvous Telemetry"
    }


def test_genre_and_genres_are_the_same_filter(corpus, materialise):
    # The singular is an alias; genres is the canonical name (ADR 0029).
    add_corpus(corpus, materialise)
    assert [a.title for a in library.list_albums(["genres:rock"])] == [
        "Cartography for Sleepwalkers"
    ]
    assert [a.title for a in library.list_albums(["genre:rock"])] == [
        a.title for a in library.list_albums(["genres:rock"])
    ]


def test_genre_ands_with_other_terms(corpus, materialise):
    add_corpus(corpus, materialise)
    # "folk" alone matches two albums; ANDed with the artist, just the one.
    assert [a.title for a in library.list_albums(["genre:folk", "holloway"])] == [
        "Paper Lung Atlas"
    ]
