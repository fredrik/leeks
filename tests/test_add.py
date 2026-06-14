"""The add pipeline, end to end against the fixture corpus."""

import hashlib

import pytest
from sqlalchemy import select

from leeks import db, library, orm
from test_harness import by_title


def rows(session, model):
    return session.scalars(select(model)).all()


def test_add_clean_album(corpus, materialise, leeks_root):
    album = by_title(corpus, "Cartography for Sleepwalkers")
    directory = materialise(album)
    originals = {
        p: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()
    }

    added = library.add(directory)

    assert added.title == album["title"]
    assert added.artist == album["artist"]
    assert added.year == album["year"]
    assert added.tracks == len(album["tracks"])
    # ADR 0010: <Album Artist>/<Year> <Album Title>/<NN> <Title>.<ext>
    assert added.destination == (
        leeks_root / "Tin Hatch Choir" / "2019 Cartography for Sleepwalkers"
    )
    assert (added.destination / "01 Inventory of Small Storms.flac").exists()

    with db.session() as session:
        (album_row,) = rows(session, orm.Album)
        assert (album_row.title, album_row.year) == (album["title"], album["year"])

        tracks = rows(session, orm.Track)
        assert [(t.title, t.track) for t in tracks] == [
            (t["title"], t["track"]) for t in album["tracks"]
        ]

        (artist,) = rows(session, orm.Artist)
        assert artist.name == album["artist"]
        assert album_row.artist_id == artist.id
        # Track artist links are overrides only; nothing overrides here.
        assert all(t.artist_id is None for t in tracks)

        (genre,) = rows(session, orm.Genre)
        assert genre.name == album["genre"]

        files = rows(session, orm.File)
        assert len(files) == len(album["tracks"])
        for file in files:
            copy = added.destination / file.path.rsplit("/", 1)[1]
            assert copy.exists()
            # The copy is byte-identical to the original it came from.
            assert (
                file.sha256 == originals[directory / file.source_path.rsplit("/", 1)[1]]
            )
            assert file.format in ("FLAC", "MP3")
            assert file.samplerate == 8000
            assert file.size > 0

        # 5 album claims + (title, track) per track.
        claims = rows(session, orm.SourceValue)
        assert len(claims) == 5 + 2 * len(album["tracks"])

    # Originals untouched.
    for path, digest in originals.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_add_multi_genre_album(corpus, materialise):
    # A set-valued genre lands as one Genre row, one junction row, and one
    # claim per genre — all from the single file_tags source (ADR 0022).
    album = by_title(corpus, "Genrezvous Telemetry")
    library.add(materialise(album))
    with db.session() as session:
        assert {g.name for g in rows(session, orm.Genre)} == set(album["genre"])
        assert len(rows(session, orm.AlbumGenre)) == len(album["genre"])
        genre_claims = [c for c in rows(session, orm.SourceValue) if c.field == "genre"]
        assert {c.value for c in genre_claims} == set(album["genre"])


def test_add_sparse_album(corpus, materialise, leeks_root):
    album = by_title(corpus, "Tape Hiss Archipelago")
    added = library.add(materialise(album))
    assert added.year is None
    # No year: the component and its separator vanish. No track number: bare title.
    assert added.destination == leeks_root / "Polder Arcade" / "Tape Hiss Archipelago"
    assert (added.destination / "Pylon Hum.flac").exists()
    assert (added.destination / "01 Arcade Rain.flac").exists()
    with db.session() as session:
        (album_row,) = rows(session, orm.Album)
        assert album_row.year is None
        assert rows(session, orm.Genre) == []
        numbers = [t.track for t in rows(session, orm.Track)]
        assert numbers == [1, 4, None, None]
        album_claims = {
            c.field for c in rows(session, orm.SourceValue) if c.entity_type == "album"
        }
        # No year, genre, or tracktotal claims: those tags are absent.
        assert album_claims == {"title", "artist"}


def test_add_feat_credit(corpus, materialise):
    album = by_title(corpus, "Salt Meridian")
    library.add(materialise(album))
    with db.session() as session:
        names = {a.name for a in rows(session, orm.Artist)}
        assert names == {"Tin Hatch Choir", "Tin Hatch Choir feat. Vesna Holloway"}
        (overridden,) = [t for t in rows(session, orm.Track) if t.artist_id]
        assert overridden.title == "Lowland Frequencies"
        featured = session.get(orm.Artist, overridden.artist_id)
        assert featured is not None
        assert featured.name == "Tin Hatch Choir feat. Vesna Holloway"


def test_add_duplicate_titles_stay_distinct(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Paper Lung Atlas")))
    with db.session() as session:
        harbours = session.scalars(
            select(orm.Track).where(orm.Track.title == "Glass Harbour")
        ).all()
        assert len(harbours) == 2
        assert harbours[0].album_id != harbours[1].album_id


def test_artist_case_variants_fold_to_first_seen(tmp_path, leeks_root):
    from fixtures.materialise import materialise_album

    one = {
        "title": "Cave Songs",
        "artist": "Tin Hatch Choir",
        "tracks": [{"title": "A"}],
    }
    two = {
        "title": "Attic Songs",
        "artist": "TIN HATCH CHOIR",
        "tracks": [{"title": "B"}],
    }
    library.add(materialise_album(one, tmp_path / "s1"))
    added = library.add(materialise_album(two, tmp_path / "s2"))
    with db.session() as session:
        (artist,) = rows(session, orm.Artist)
        assert artist.name == "Tin Hatch Choir"  # first-seen spelling displays
        # The claim stays verbatim: file_tags really did say TIN HATCH CHOIR.
        claims = {
            (c.entity_type, c.field): c.value
            for c in rows(session, orm.SourceValue)
            if c.field == "artist"
        }
        assert "TIN HATCH CHOIR" in claims.values()
    # The shelf reuses the first-seen spelling, so case variants share a directory.
    assert added.destination == leeks_root / "Tin Hatch Choir" / "Attic Songs"


def test_artists_are_not_duplicated_across_albums(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    with db.session() as session:
        names = [a.name for a in rows(session, orm.Artist)]
        assert names.count("Tin Hatch Choir") == 1


def test_copy_name_collisions_are_suffixed(materialise):
    # Two unnumbered tracks with the same title must both land.
    album = {
        "title": "Echoes of Echoes",
        "artist": "Polder Arcade",
        "tracks": [{"title": "Echo"}, {"title": "Filler"}, {"title": "Echo"}],
    }
    added = library.add(materialise(album))
    names = sorted(p.name for p in added.destination.iterdir())
    assert names == ["Echo-2.flac", "Echo.flac", "Filler.flac"]


def test_album_dir_collisions_fold_case(tmp_path, leeks_root):
    from fixtures.materialise import materialise_album

    one = {"title": "Salt Mine", "artist": "Polder Arcade", "tracks": [{"title": "A"}]}
    two = {"title": "SALT MINE", "artist": "Polder Arcade", "tracks": [{"title": "B"}]}
    library.add(materialise_album(one, tmp_path / "s1"))
    added = library.add(materialise_album(two, tmp_path / "s2"))
    # Case-folded collision: a library copied to a case-insensitive
    # filesystem must not merge two album directories (ADR 0010).
    assert added.destination == leeks_root / "Polder Arcade" / "SALT MINE-2"


def test_unknown_artist_bucket(tmp_path, leeks_root):
    import shutil

    from fixtures.materialise import AUDIO
    from mediafile import MediaFile

    source = tmp_path / "src" / "mystery"
    source.mkdir(parents=True)
    path = source / "track.flac"
    shutil.copyfile(AUDIO / "tone-000.flac", path)
    media = MediaFile(str(path))
    media.album = "Mystery Tape"
    media.title = "Side A"
    media.save()

    added = library.add(source)
    assert added.artist is None
    assert added.destination == leeks_root / "Unknown Artist" / "Mystery Tape"
    assert (added.destination / "Side A.flac").exists()


def test_copy_failure_rolls_everything_back(
    corpus, materialise, leeks_root, monkeypatch
):
    directory = materialise(by_title(corpus, "Salt Meridian"))
    before = {
        p: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()
    }

    def explode(path):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr("leeks.tags.measure", explode)
    with pytest.raises(RuntimeError, match="disk on fire"):
        library.add(directory)

    with db.session() as session:
        for model in (orm.Album, orm.Track, orm.File, orm.SourceValue):
            assert rows(session, model) == []
    # Nothing left on disk but the database — the artist shelf included.
    assert [p.name for p in leeks_root.iterdir()] == ["leeks.db"]
    for path, digest in before.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_readd_is_refused(corpus, materialise):
    album = by_title(corpus, "Paper Lung Atlas")
    directory = materialise(album)
    library.add(directory)
    with db.session() as session:
        before = {m: len(rows(session, m)) for m in (orm.Album, orm.Track, orm.File)}
    with pytest.raises(library.AlreadyAdded, match="already added"):
        library.add(directory)
    with db.session() as session:
        after = {m: len(rows(session, m)) for m in (orm.Album, orm.Track, orm.File)}
    assert after == before
