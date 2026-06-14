"""show_albums: one album in depth — tracks, file measurements, and claims.

The depth read behind `leek show` (ADR 0020). Where list_albums returns the
merged shelf, show_albums hydrates each match with its tracks, the
measurements of the files realising them (ADR 0007), and the claim layer
beneath (ADR 0008).
"""

from leeks import library
from test_harness import by_title


def test_show_albums_hydrates_tracks_files_and_claims(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    [album] = library.show_albums(["sleepwalkers"])

    assert album.artist == "Tin Hatch Choir"
    assert album.year == 2019
    assert album.title == "Cartography for Sleepwalkers"
    assert album.genres == ["Indie Rock"]
    assert [track.number for track in album.tracks] == [1, 2, 3, 4, 5]
    assert album.tracks[1].title == "Glass Harbour"

    # Every track is realised by one file carrying measurements (ADR 0007).
    file = album.tracks[0].files[0]
    assert file.format in {"FLAC", "MP3"}
    assert file.duration is not None
    assert file.size > 0
    assert len(file.sha256) == 64

    # Claims record what file_tags said, and only that (ADR 0008).
    assert {claim.field for claim in album.claims} >= {"title", "artist", "year"}
    assert all(claim.source == "file_tags" for claim in album.claims)
    assert "title" in {claim.field for claim in album.tracks[0].claims}


def test_show_albums_id_term_selects_one(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    salt = next(a for a in library.list_albums() if a.title == "Salt Meridian")

    [shown] = library.show_albums([f"id:{salt.id}"])
    assert shown.title == "Salt Meridian"


def test_show_albums_returns_every_match_in_shelf_order(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))  # Tin Hatch, 2022
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))  # 2019

    shown = library.show_albums(["tin hatch"])
    # Same artist, so the shelf orders by year ascending (ADR 0011).
    assert [album.title for album in shown] == [
        "Cartography for Sleepwalkers",
        "Salt Meridian",
    ]


def test_show_albums_no_match_is_empty(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    assert library.show_albums(["polka"]) == []


def test_show_albums_orders_tracks_with_unnumbered_last(corpus, materialise):
    library.add(materialise(by_title(corpus, "Tape Hiss Archipelago")))
    [album] = library.show_albums(["archipelago"])
    # Numbered tracks in order, then the unnumbered ones (ADR 0013).
    assert [track.number for track in album.tracks] == [1, 4, None, None]


def test_show_tracks_hydrates_album_and_measurements(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    [card] = library.show_tracks(["storms"])
    assert card.title == "Inventory of Small Storms"
    assert card.album == "Cartography for Sleepwalkers"
    assert card.year == 2019
    assert card.number == 1
    assert card.artist == "Tin Hatch Choir"
    assert card.files[0].format in {"FLAC", "MP3"}
    assert "title" in {claim.field for claim in card.claims}


def test_show_tracks_id_selects_one(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    target = next(c for c in library.show_tracks() if c.title == "Glass Harbour")
    [one] = library.show_tracks([f"id:{target.id}"])
    assert one.title == "Glass Harbour"


def test_show_tracks_carries_an_overriding_credit(corpus, materialise):
    # The effective artist is the track's own feat. credit (ADR 0013).
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    [card] = library.show_tracks(["lowland"])
    assert card.artist == "Tin Hatch Choir feat. Vesna Holloway"


def test_show_artists_lists_albums_and_guests(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    by_name = {artist.name: artist for artist in library.show_artists(["tin hatch"])}
    # The album artist: both albums on its shelf, in year order, no guest spots.
    choir = by_name["Tin Hatch Choir"]
    assert [(ref.title, ref.year) for ref in choir.albums] == [
        ("Cartography for Sleepwalkers", 2019),
        ("Salt Meridian", 2022),
    ]
    assert choir.guests == []
    # The raw feat. credit: no album of its own, one guest spot (ADR 0009).
    feat = by_name["Tin Hatch Choir feat. Vesna Holloway"]
    assert feat.albums == []
    assert [(g.album, g.title) for g in feat.guests] == [
        ("Salt Meridian", "Lowland Frequencies")
    ]


def test_show_artists_id_selects_one(corpus, materialise):
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    target = next(a for a in library.show_artists() if a.name == "Tin Hatch Choir")
    [one] = library.show_artists([f"id:{target.id}"])
    assert one.name == "Tin Hatch Choir"
