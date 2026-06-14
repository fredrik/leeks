"""The library's verbs: the add pipeline and the list query.

The write-path discipline from the slice 1 plan: every claim lands as a
source_values row and the merged columns are computed by merge() — an
identity copy while file_tags is the only source, but a real seam.
Structured fields (artists, genres) are written relationally at add
time; their merge story arrives with the second source. Originals are
never modified; copies shelve per the scheme (ADR 0010).

The read side is list_albums: the merged view in shelf order, never the
source layer (ADR 0011).
"""

import re
import shutil
from collections import defaultdict
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, aliased

from leeks import db, path_source, tags
from leeks.detect import detect
from leeks.fields import CLAIMS, merged_fields
from leeks.models import AlbumInfo
from leeks.orm import (
    Album,
    AlbumGenre,
    Artist,
    File,
    Genre,
    Source,
    SourceValue,
    Track,
)

# The scalar columns merge() owns, derived from the registry (ADR 0025):
# every claim field that carries a cast is a merged column.
MERGED_FIELDS: dict[str, dict[str, type]] = {
    "album": merged_fields("album"),
    "track": merged_fields("track"),
}


class AlreadyAdded(Exception):
    """Some of these files are already in the library."""


@dataclass(frozen=True)
class Added:
    """What `leek add` accomplished, for the summary card."""

    album_id: int
    title: str
    artist: str | None
    year: int | None
    tracks: int
    claims: int
    destination: Path


@dataclass(frozen=True)
class Listed:
    """One album of `leek list`'s shelf."""

    id: int
    artist: str | None
    year: int | None
    title: str
    # The album's genres, a set (ADR 0022) — empty when none is claimed, which
    # is also the default: absent and empty are the same state for a genre set.
    # Opt-in via --fields, not a default shelf column.
    genres: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ListedTrack:
    """One track of `leek list --tracks`, in tree-walk order (ADR 0013)."""

    id: int
    album_id: int
    number: int | None
    title: str
    # The effective artist: the track's own credit when it overrides the
    # album's (a feat.), else the album artist. Rows sort by album artist
    # (the shelf), so an override still displays under its album.
    artist: str | None
    album: str


@dataclass(frozen=True)
class ListedArtist:
    """One artist of `leek list --artists`."""

    id: int
    name: str


@dataclass(frozen=True)
class Claim:
    """One source's claim about one field (ADR 0008), source resolved to its name.

    The unit `--sources` reveals: who said what. Trivial today — every claim
    is the `file_tags` source — but the seam that earns its keep at source #2.
    """

    source: str
    field: str
    value: str


@dataclass(frozen=True)
class ShownFile:
    """The measurements of one file realising a track (ADR 0007).

    Read off the file row, not the source layer: no source has a vote on
    what the bytes are, so these are facts, not claims.
    """

    path: str
    format: str
    bitrate: int | None
    samplerate: int | None
    channels: int | None
    duration: float | None
    size: int
    sha256: str


@dataclass(frozen=True)
class ShownTrack:
    """One track of `leek show`, in depth: its files' measurements and claims."""

    id: int
    number: int | None
    title: str
    # The effective artist: the track's own credit when it overrides the
    # album's, else the album artist — as `list_tracks` resolves it.
    artist: str | None
    files: list[ShownFile]
    claims: list[Claim]


@dataclass(frozen=True)
class ShownAlbum:
    """One album of `leek show`, in depth: the merged view, its tracks, its claims.

    The typed projection every formatter reads (ADR 0014): merged identity on
    top, the tracks (each with file measurements) beneath, and the claim layer
    carried alongside for `--sources` and for JSON, which always includes it.
    """

    id: int
    artist: str | None
    year: int | None
    title: str
    genres: list[str]
    tracks: list[ShownTrack]
    claims: list[Claim]


@dataclass(frozen=True)
class ShownTrackCard:
    """One track of `leek show --tracks`, in depth, with its album for context.

    The standalone counterpart to the `ShownTrack` embedded in an album: it
    carries the album title and year so a track shown on its own still says
    where it lives.
    """

    id: int
    number: int | None
    title: str
    artist: str | None
    album: str
    year: int | None
    files: list[ShownFile]
    claims: list[Claim]


@dataclass(frozen=True)
class ShownAlbumRef:
    """An album on an artist's shelf: enough to name it and find it by id."""

    id: int
    title: str
    year: int | None


@dataclass(frozen=True)
class ShownGuestTrack:
    """A track an artist guests on, named under the album that hosts it."""

    album: str
    number: int | None
    title: str


@dataclass(frozen=True)
class ShownArtist:
    """One artist of `leek show --artists`, in depth: its shelf and guest spots.

    An artist has no measurements and no claims of its own — the source layer
    is album/track only (ADR 0007/0008) — so its depth is what it is credited
    on: the albums under its name, and the tracks it guests on by an
    overriding credit.
    """

    id: int
    name: str
    albums: list[ShownAlbumRef]
    guests: list[ShownGuestTrack]


class QueryError(Exception):
    """A query term names an unknown field or a malformed value (ADR 0029)."""


# Singular spellings a qualified term may use, mapped to the canonical field
# name the namespace exposes (ADR 0029). `genre:folk` reads as a membership
# test; `genres` is the name `leek fields` lists and `--fields` selects.
_FIELD_ALIASES = {"genre": "genres"}


def _substr(column):
    """A matcher: value -> a folded substring test on `column` (ADR 0021)."""
    return lambda value: column.icontains(value, autoescape=True)


def _album_has_genre(value: str):
    """A matcher: the album has a genre whose name contains `value`.

    Genre is relational — a set via the AlbumGenre junction (ADR 0022), not a
    column — so it filters by membership (an EXISTS over the junction), not a
    substring on a column. The reach to the genre table is a query-time join,
    like every other reach (ADR 0029); storage stays normalised.
    """
    return Album.id.in_(
        select(AlbumGenre.album_id)
        .join(Genre, AlbumGenre.genre_id == Genre.id)
        .where(Genre.name.icontains(value, autoescape=True))
    )


def _apply_terms(statement, terms: Sequence[str], *, fields, bare, pk):
    """Narrow a statement by query terms, ANDed (ADRs 0011, 0029).

    Each term is `[field:]value`. A bare term substring-matches any of `bare`
    — the subject's descriptive fields, which reach up the tree over the
    statement's own joins (a track's `bare` includes its album's artist and
    title, so `leek list --tracks radiohead computer` finds OK Computer). A
    qualified `field:value` applies the named field's matcher in `fields` (a
    substring on a column, or a membership test for a set-valued field like
    genres); `id:N` matches the primary key `pk` exactly, the lone exact term
    (ADR 0020). Matching folds case and accents through SQLite's overridden
    LIKE (ADR 0021).

    A term naming a field outside the namespace, or an `id:` value that is not
    a whole number, raises QueryError — loud, never silent: a stray colon
    becomes a clear error, not a silently guessed field query (ADR 0012).
    """
    for term in terms:
        field, sep, value = term.partition(":")
        field = _FIELD_ALIASES.get(field, field)
        if not sep:
            statement = statement.where(
                or_(*(column.icontains(term, autoescape=True) for column in bare))
            )
        elif field == "id":
            if not value.isdigit():
                raise QueryError(f"id: takes a whole number, not {value!r}")
            statement = statement.where(pk == int(value))
        elif field in fields:
            statement = statement.where(fields[field](value))
        else:
            valid = ", ".join((*fields, "id"))
            raise QueryError(f"no field called {field!r}; choose from {valid}")
    return statement


def _shelf_statement():
    """`select(Album, Artist.name)` joined and ordered as the shelf (ADR 0011)."""
    return (
        select(Album, Artist.name)
        .outerjoin(Artist, Album.artist_id == Artist.id)
        # INNER join leans on an invariant: every album has at least one
        # track, because add creates them together. It filters the shelf to
        # albums that have tracks — a future verb that deletes tracks must
        # revisit this, or empty albums silently vanish — and the group_by
        # collapses the per-track rows the join would otherwise produce.
        .join(Track, Track.album_id == Album.id)
        .group_by(Album.id)
        .order_by(
            func.coalesce(Artist.name, "Unknown Artist").collate(db.SORT_COLLATION),
            Album.year.is_(None),
            Album.year,
            Album.title.collate(db.SORT_COLLATION),
        )
    )


def _apply_album_terms(statement, terms: Sequence[str]):
    """Narrow an album query by terms over the shelf statement (ADR 0029).

    A bare term reaches the album's artist, title, and year; the same names
    qualify a term, `genre:`/`genres:` filters by genre membership (ADR 0023),
    and `id:N` selects one album exactly. Shared by `list_albums` and
    `show_albums`, which both build on `_shelf_statement` (so its single
    `Artist` join is in scope).
    """
    fields = {
        "artist": _substr(Artist.name),
        "title": _substr(Album.title),
        "year": _substr(cast(Album.year, String)),
        "genres": _album_has_genre,
    }
    bare = [Artist.name, Album.title, cast(Album.year, String)]
    return _apply_terms(statement, terms, fields=fields, bare=bare, pk=Album.id)


def _apply_track_terms(statement, terms: Sequence[str], effective_artist):
    """Narrow a track query by terms, reaching up the tree (ADR 0029).

    A bare term reaches the track's title and its album's artist and title,
    so `leek list --tracks radiohead computer` returns OK Computer. Qualified
    terms add the album and the track number; `id:N` selects one track.
    `effective_artist` is the track's own credit over the album's, as the
    caller's joins resolve it.
    """
    fields = {
        "artist": _substr(effective_artist),
        "album": _substr(Album.title),
        "title": _substr(Track.title),
        "number": _substr(cast(Track.track, String)),
    }
    bare = [effective_artist, Album.title, Track.title]
    return _apply_terms(statement, terms, fields=fields, bare=bare, pk=Track.id)


def _apply_artist_terms(statement, terms: Sequence[str]):
    """Narrow an artist query by name, or by `id:N` exactly (ADR 0029)."""
    fields = {"name": _substr(Artist.name)}
    return _apply_terms(
        statement, terms, fields=fields, bare=[Artist.name], pk=Artist.id
    )


def _files_by_track(
    session: Session, track_ids: Sequence[int]
) -> dict[int, list[ShownFile]]:
    """The measurements of the files realising each track (ADR 0007), by id."""
    files: dict[int, list[ShownFile]] = defaultdict(list)
    if not track_ids:
        return files
    for file in session.scalars(
        select(File).where(File.track_id.in_(track_ids)).order_by(File.id)
    ):
        files[file.track_id].append(
            ShownFile(
                path=file.path,
                format=file.format,
                bitrate=file.bitrate,
                samplerate=file.samplerate,
                channels=file.channels,
                duration=file.duration,
                size=file.size,
                sha256=file.sha256,
            )
        )
    return files


def list_albums(terms: Sequence[str] = ()) -> list[Listed]:
    """The library's albums in shelf order, narrowed by terms (ADR 0011)."""
    statement = _apply_album_terms(_shelf_statement(), terms)
    with db.session() as session:
        rows = list(session.execute(statement))
        genres = _genres_by_album(session, [album.id for album, _ in rows])
        return [
            Listed(
                id=album.id,
                artist=artist,
                year=album.year,
                title=album.title,
                genres=genres[album.id],
            )
            for album, artist in rows
        ]


def list_tracks(terms: Sequence[str] = ()) -> list[ListedTrack]:
    """The library's tracks as a depth-first walk of the tree (ADR 0013).

    Tree-walk order is album shelf order (ADR 0011), then track number with
    unnumbered last, then `Track.id`. `Track.id` is assembly order — track
    number then filename (glossary) — so it already *is* the filename
    tie-break, materialised; no file join is needed. (That assembly order
    can diverge from the on-disk destination-filename order only for
    unnumbered tracks.) `Album.id` keeps one album's tracks contiguous when
    two albums share shelf coordinates.

    Terms AND together and reach up the tree: a bare term matches the track
    title and its album's artist and title, qualified terms add the album and
    number, and `id:N` selects one track (ADR 0029).
    """
    # Two artist joins: the album artist sets the shelf (and the sort); the
    # track artist overrides the display when a track carries its own credit.
    album_artist = aliased(Artist)
    track_artist = aliased(Artist)
    effective_artist = func.coalesce(track_artist.name, album_artist.name)
    statement = (
        select(Track, effective_artist, Album.title)
        # INNER: every track has an album (NOT NULL album_id).
        .join(Album, Track.album_id == Album.id)
        .outerjoin(album_artist, Album.artist_id == album_artist.id)
        .outerjoin(track_artist, Track.artist_id == track_artist.id)
        .order_by(
            func.coalesce(album_artist.name, "Unknown Artist").collate(
                db.SORT_COLLATION
            ),
            Album.year.is_(None),
            Album.year,
            Album.title.collate(db.SORT_COLLATION),
            Album.id,
            Track.track.is_(None),
            Track.track,
            Track.id,
        )
    )
    statement = _apply_track_terms(statement, terms, effective_artist)
    with db.session() as session:
        return [
            ListedTrack(
                id=track.id,
                album_id=track.album_id,
                number=track.track,
                title=track.title,
                artist=artist,
                album=album,
            )
            for track, artist, album in session.execute(statement)
        ]


def list_artists(terms: Sequence[str] = ()) -> list[ListedArtist]:
    """Every artist in the library, in case-folded name order (ADR 0013).

    Every row of the artists table, raw multi-artist credit strings included
    ("… feat. …", until artist-credit splitting refines them into real
    artists): the honest view of what the table holds today. Terms AND
    together and match the name, or `id:N` exactly (ADR 0029).
    """
    statement = select(Artist).order_by(Artist.name.collate(db.SORT_COLLATION))
    statement = _apply_artist_terms(statement, terms)
    with db.session() as session:
        return [
            ListedArtist(id=artist.id, name=artist.name)
            for artist in session.scalars(statement)
        ]


def _genres_by_album(
    session: Session, album_ids: Sequence[int]
) -> dict[int, list[str]]:
    """Each album's genres in name order — the merged set (ADR 0022).

    Shared by the shelf (`list_albums`) and the depth read (`show_albums`):
    one batched query, grouped by album, so neither does it per row. Names
    sort in the library's Swedish order (ADR 0026), like every other listing.
    """
    genres: dict[int, list[str]] = defaultdict(list)
    for album_id, name in session.execute(
        select(AlbumGenre.album_id, Genre.name)
        .join(Genre, AlbumGenre.genre_id == Genre.id)
        .where(AlbumGenre.album_id.in_(album_ids))
        .order_by(Genre.name.collate(db.SORT_COLLATION))
    ):
        genres[album_id].append(name)
    return genres


def _claims_by_entity(
    session: Session, entity_type: str, entity_ids: Sequence[int]
) -> dict[int, list[Claim]]:
    """Every source's claims about these entities (ADR 0008), grouped by id."""
    claims: dict[int, list[Claim]] = defaultdict(list)
    if not entity_ids:
        return claims
    statement = (
        select(SourceValue, Source.name)
        .join(Source, SourceValue.source_id == Source.id)
        .where(
            SourceValue.entity_type == entity_type,
            SourceValue.entity_id.in_(entity_ids),
        )
        .order_by(SourceValue.id)
    )
    for value, source in session.execute(statement):
        claims[value.entity_id].append(
            Claim(source=source, field=value.field, value=value.value)
        )
    return claims


def show_albums(terms: Sequence[str] = ()) -> list[ShownAlbum]:
    """The matching albums, each in depth: tracks, file measurements, claims.

    The depth read behind `leek show` (ADR 0020): the same shelf-order
    selection as `list_albums`, then each album hydrated with its tracks
    (effective artist as `list_tracks` resolves it), the measurements of the
    files realising them (ADR 0007), its genres, and every source's claims
    (ADR 0008). Claims ride along for `--sources` and for JSON, which carries
    them regardless. Several matches return several albums; `show` decides how
    to present them.
    """
    album_artist = aliased(Artist)
    track_artist = aliased(Artist)
    with db.session() as session:
        album_rows = session.execute(
            _apply_album_terms(_shelf_statement(), terms)
        ).all()
        album_ids = [album.id for album, _ in album_rows]
        if not album_ids:
            return []

        tracks_by_album: dict[int, list[tuple[Track, str | None]]] = defaultdict(list)
        track_statement = (
            select(Track, func.coalesce(track_artist.name, album_artist.name))
            .join(Album, Track.album_id == Album.id)
            .outerjoin(album_artist, Album.artist_id == album_artist.id)
            .outerjoin(track_artist, Track.artist_id == track_artist.id)
            .where(Track.album_id.in_(album_ids))
            .order_by(Track.track.is_(None), Track.track, Track.id)
        )
        for track, artist in session.execute(track_statement):
            tracks_by_album[track.album_id].append((track, artist))
        track_ids = [track.id for rows in tracks_by_album.values() for track, _ in rows]

        files_by_track = _files_by_track(session, track_ids)

        genres_by_album = _genres_by_album(session, album_ids)

        album_claims = _claims_by_entity(session, "album", album_ids)
        track_claims = _claims_by_entity(session, "track", track_ids)

        return [
            ShownAlbum(
                id=album.id,
                artist=artist,
                year=album.year,
                title=album.title,
                genres=genres_by_album[album.id],
                tracks=[
                    ShownTrack(
                        id=track.id,
                        number=track.track,
                        title=track.title,
                        artist=effective_artist,
                        files=files_by_track[track.id],
                        claims=track_claims[track.id],
                    )
                    for track, effective_artist in tracks_by_album[album.id]
                ],
                claims=album_claims[album.id],
            )
            for album, artist in album_rows
        ]


def show_tracks(terms: Sequence[str] = ()) -> list[ShownTrackCard]:
    """The matching tracks, each in depth: its album, file measurements, claims.

    `leek show --tracks` (ADR 0020): tracks in tree-walk order (as
    `list_tracks` defines it), narrowed the same way `list_tracks` narrows —
    bare terms reaching up to the album, qualified terms and `id:N` too
    (ADR 0029) — each hydrated with the measurements of the files realising it
    (ADR 0007) and every source's claims (ADR 0008). The effective artist is
    the track's own credit when it overrides the album's, else the album's.
    """
    album_artist = aliased(Artist)
    track_artist = aliased(Artist)
    effective_artist = func.coalesce(track_artist.name, album_artist.name)
    statement = (
        select(Track, effective_artist, Album.title, Album.year)
        .join(Album, Track.album_id == Album.id)
        .outerjoin(album_artist, Album.artist_id == album_artist.id)
        .outerjoin(track_artist, Track.artist_id == track_artist.id)
        .order_by(
            func.coalesce(album_artist.name, "Unknown Artist").collate(
                db.SORT_COLLATION
            ),
            Album.year.is_(None),
            Album.year,
            Album.title.collate(db.SORT_COLLATION),
            Album.id,
            Track.track.is_(None),
            Track.track,
            Track.id,
        )
    )
    statement = _apply_track_terms(statement, terms, effective_artist)
    with db.session() as session:
        rows = session.execute(statement).all()
        track_ids = [track.id for track, _, _, _ in rows]
        files_by_track = _files_by_track(session, track_ids)
        track_claims = _claims_by_entity(session, "track", track_ids)
        return [
            ShownTrackCard(
                id=track.id,
                number=track.track,
                title=track.title,
                artist=artist,
                album=album_title,
                year=album_year,
                files=files_by_track[track.id],
                claims=track_claims[track.id],
            )
            for track, artist, album_title, album_year in rows
        ]


def show_artists(terms: Sequence[str] = ()) -> list[ShownArtist]:
    """The matching artists, each in depth: their shelf and their guest spots.

    `leek show --artists` (ADR 0020): artists in case-folded name order,
    narrowed by name or by `id:N` (the artist's id, ADR 0029). An artist has
    no measurements or claims of its own (the source layer is album/track
    only), so its depth is the albums credited to it and the tracks it guests
    on by an overriding credit.
    """
    statement = select(Artist).order_by(Artist.name.collate(db.SORT_COLLATION))
    statement = _apply_artist_terms(statement, terms)
    with db.session() as session:
        artists = session.scalars(statement).all()
        artist_ids = [artist.id for artist in artists]
        if not artist_ids:
            return []

        albums_by_artist: dict[int, list[ShownAlbumRef]] = defaultdict(list)
        for album in session.scalars(
            select(Album)
            .where(Album.artist_id.in_(artist_ids))
            .order_by(
                Album.year.is_(None), Album.year, Album.title.collate(db.SORT_COLLATION)
            )
        ):
            if album.artist_id is not None:
                albums_by_artist[album.artist_id].append(
                    ShownAlbumRef(id=album.id, title=album.title, year=album.year)
                )

        guests_by_artist: dict[int, list[ShownGuestTrack]] = defaultdict(list)
        for track, album_title in session.execute(
            select(Track, Album.title)
            .join(Album, Track.album_id == Album.id)
            .where(Track.artist_id.in_(artist_ids))
            .order_by(
                Album.title.collate(db.SORT_COLLATION),
                Track.track.is_(None),
                Track.track,
                Track.id,
            )
        ):
            if track.artist_id is not None:
                guests_by_artist[track.artist_id].append(
                    ShownGuestTrack(
                        album=album_title, number=track.track, title=track.title
                    )
                )

        return [
            ShownArtist(
                id=artist.id,
                name=artist.name,
                albums=albums_by_artist[artist.id],
                guests=guests_by_artist[artist.id],
            )
            for artist in artists
        ]


def merge(
    session: Session, entity_type: str, entity_id: int, row: Album | Track
) -> None:
    """Recompute the merged view from claims, by source priority (ADR 0031).

    A scalar column takes the highest-priority claim, cast back from text. The
    artist foreign key takes the highest-priority artist claim too, but
    reconciled to an Artist row rather than stored as a string — relational
    merge (ADR 0032). Confidence is recorded but does not yet decide; merging
    collapses to identity while one source claims a field.
    """
    casts = MERGED_FIELDS[entity_type]
    best: dict[str, tuple[int, str]] = {}
    for name, value, priority in session.execute(
        select(SourceValue.field, SourceValue.value, Source.priority)
        .join(Source, SourceValue.source_id == Source.id)
        .where(
            SourceValue.entity_type == entity_type,
            SourceValue.entity_id == entity_id,
        )
    ):
        if name not in best or priority > best[name][0]:
            best[name] = (priority, value)
    for name, caster in casts.items():
        if name in best:
            setattr(row, name, caster(best[name][1]))
    # The artist is a foreign key, not a column: the winning claim's name
    # resolves to an Artist row (ADR 0032). genre, a junction, joins relational
    # merge when a second source claims it — the path source does not.
    if "artist" in best:
        row.artist_id = _get_or_create(session, Artist, best["artist"][1]).id


def add(directory: Path) -> Added:
    """Ingest one album: detect, assemble, record claims, merge, copy."""
    directory = directory.expanduser().resolve()
    info = tags.assemble(detect(directory))
    root = db.library_root()
    with db.session(root) as session:
        _refuse_readds(session, info)
        now = datetime.now(UTC).replace(tzinfo=None)
        file_tags = session.scalars(
            select(Source).where(Source.name == "file_tags")
        ).one()

        # The directory name is the fallback for the NOT NULL title, not a claim.
        album = Album(title=info.title or directory.name, added=now)
        session.add(album)
        session.flush()
        _link_genres(session, info, album)
        tracks = _create_tracks(session, info, album, now)

        claims = _record_claims(session, info, album, tracks, file_tags, now)
        path = session.scalars(select(Source).where(Source.name == "path")).one()
        _record_path_claims(session, directory, album, path, now)
        # merge sets the artist foreign key from the claims (ADR 0032), so the
        # album's artist is read back from the merged row, not from file_tags.
        merge(session, "album", album.id, album)
        for row in tracks:
            merge(session, "track", row.id, row)

        artist = session.get(Artist, album.artist_id) if album.artist_id else None
        destination = _destination(root, album, artist.name if artist else None)
        try:
            _copy_files(session, info, tracks, destination, now)
            session.commit()
            return Added(
                album_id=album.id,
                title=album.title,
                artist=artist.name if artist else None,
                year=album.year,
                tracks=len(tracks),
                claims=claims,
                destination=destination,
            )
        except BaseException:
            session.rollback()
            shutil.rmtree(destination, ignore_errors=True)
            with suppress(OSError):  # the artist shelf, if this add created it
                destination.parent.rmdir()
            raise


def _refuse_readds(session: Session, info: AlbumInfo) -> None:
    sources = [str(track.path) for track in info.tracks]
    known = session.scalars(
        select(File.source_path).where(File.source_path.in_(sources))
    ).all()
    if known:
        more = f" (+{len(known) - 1} more)" if len(known) > 1 else ""
        raise AlreadyAdded(f"already added: {known[0]}{more}")


def _get_or_create[R: (Artist, Genre)](
    session: Session, model: type[R], name: str
) -> R:
    row = session.scalar(select(model).where(model.name == name))
    if row is None:
        row = model(name=name)
        session.add(row)
        session.flush()
    return row


def _link_genres(session: Session, info: AlbumInfo, album: Album) -> None:
    # An album's genres are a set (ADR 0022): each links its own junction row.
    for name in info.genres:
        genre = _get_or_create(session, Genre, name)
        session.add(AlbumGenre(album_id=album.id, genre_id=genre.id))


def _create_tracks(
    session: Session, info: AlbumInfo, album: Album, now: datetime
) -> list[Track]:
    rows = []
    for track in info.tracks:
        # The file stem is the fallback for the NOT NULL title, not a claim.
        # The artist override, when present, is set by merge from the claims
        # (ADR 0032), the same path the album artist takes.
        row = Track(
            album_id=album.id,
            title=track.title or track.path.stem,
            track=track.track,
            added=now,
        )
        session.add(row)
        session.flush()
        rows.append(row)
    return rows


def _record_claims(
    session: Session,
    info: AlbumInfo,
    album: Album,
    tracks: list[Track],
    source: Source,
    now: datetime,
) -> int:
    claimed: list[SourceValue] = []

    def claim(entity_type: str, entity_id: int, field: str, value: object) -> None:
        if value is not None:
            claimed.append(
                SourceValue(
                    source_id=source.id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field=field,
                    value=str(value),
                    added=now,
                )
            )

    def record(entity_type: str, entity_id: int, source_obj: object) -> None:
        # The registry says which fields exist and their arity (ADR 0025): a
        # set-valued field yields one claim per value, a scalar at most one.
        for f in CLAIMS:
            if f.entity != entity_type:
                continue
            raw = getattr(source_obj, f.model_attr)
            for value in raw if f.multi else [raw]:
                claim(entity_type, entity_id, f.name, value)

    record("album", album.id, info)
    for track, row in zip(info.tracks, tracks):
        record("track", row.id, track)
    session.add_all(claimed)
    return len(claimed)


def _record_path_claims(
    session: Session, directory: Path, album: Album, source: Source, now: datetime
) -> int:
    """Record the path source's claims about the album (ADR 0008/0031).

    The directory name is parsed for what it asserts — slice 3, the year —
    and each becomes a claim carrying the parser's confidence. Unlike a
    fallback, an empty parse records nothing (ADR 0008): the path claims only
    what its name actually says.
    """
    claimed = [
        SourceValue(
            source_id=source.id,
            entity_type="album",
            entity_id=album.id,
            field=claim.field,
            value=claim.value,
            confidence=claim.confidence,
            added=now,
        )
        for claim in path_source.parse(directory.name)
    ]
    session.add_all(claimed)
    return len(claimed)


def _pathsafe(text: str) -> str:
    """Filesystem-safe but human (ADR 0010): replace hostile characters only."""
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", text)
    return cleaned.strip().rstrip(".") or "_"


def _destination(root: Path, album: Album, artist: str | None) -> Path:
    """<Album Artist>/<Year> <Album Title>, collision-suffixed (ADR 0010)."""
    shelf = root / _pathsafe(artist or "Unknown Artist")
    name = f"{album.year} {album.title}" if album.year else album.title
    return _vacant(shelf, _pathsafe(name))


def _copy_files(
    session: Session,
    info: AlbumInfo,
    tracks: list[Track],
    destination: Path,
    now: datetime,
) -> None:
    destination.mkdir(parents=True)
    for track, row in zip(info.tracks, tracks):
        name = _pathsafe(row.title)
        if row.track is not None:
            name = f"{row.track:02d} {name}"
        copy = _vacant(destination, name, track.path.suffix.lower())
        shutil.copyfile(track.path, copy)
        facts = tags.measure(copy)
        session.add(
            File(
                track_id=row.id,
                path=str(copy),
                source_path=str(track.path),
                format=facts.format,
                bitrate=facts.bitrate,
                samplerate=facts.samplerate,
                channels=facts.channels,
                duration=facts.duration,
                size=facts.size,
                sha256=facts.sha256,
                mtime=facts.mtime,
                added=now,
            )
        )


def _vacant(directory: Path, name: str, suffix: str = "") -> Path:
    """The first free path for this name; collisions count up from -2.

    Compared case-insensitively even on case-sensitive filesystems: the
    library must survive being copied to one that folds case (ADR 0010).
    """
    taken = (
        {p.name.casefold() for p in directory.iterdir()}
        if directory.exists()
        else set()
    )
    candidate = f"{name}{suffix}"
    counter = 2
    while candidate.casefold() in taken:
        candidate = f"{name}-{counter}{suffix}"
        counter += 1
    return directory / candidate
