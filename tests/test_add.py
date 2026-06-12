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
    assert added.destination == leeks_root / f"album-{added.album_id}"

    with db.session() as session:
        (album_row,) = rows(session, orm.Album)
        assert (album_row.title, album_row.year) == (album["title"], album["year"])

        tracks = rows(session, orm.Track)
        assert [(t.title, t.track) for t in tracks] == [
            (t["title"], t["track"]) for t in album["tracks"]
        ]

        (artist,) = rows(session, orm.Artist)
        assert artist.name == album["artist"]
        (credit,) = rows(session, orm.ArtistCredit)
        assert (credit.album_id, credit.role) == (album_row.id, "albumartist")

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


def test_add_sparse_album(corpus, materialise):
    album = by_title(corpus, "Tape Hiss Archipelago")
    added = library.add(materialise(album))
    assert added.year is None
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
        (track_credit,) = [
            c for c in rows(session, orm.ArtistCredit) if c.track_id is not None
        ]
        track = session.get(orm.Track, track_credit.track_id)
        assert track is not None and track.title == "Lowland Frequencies"
        assert track_credit.artist.name == "Tin Hatch Choir feat. Vesna Holloway"


def test_add_duplicate_titles_stay_distinct(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Paper Lung Atlas")))
    with db.session() as session:
        harbours = session.scalars(
            select(orm.Track).where(orm.Track.title == "Glass Harbour")
        ).all()
        assert len(harbours) == 2
        assert harbours[0].album_id != harbours[1].album_id


def test_artists_are_not_duplicated_across_albums(corpus, materialise):
    library.add(materialise(by_title(corpus, "Cartography for Sleepwalkers")))
    library.add(materialise(by_title(corpus, "Salt Meridian")))
    with db.session() as session:
        names = [a.name for a in rows(session, orm.Artist)]
        assert names.count("Tin Hatch Choir") == 1


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
    assert not list(leeks_root.glob("album-*"))
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
