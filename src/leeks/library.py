"""The add pipeline: claims through the source layer, bytes into the library.

The write-path discipline from the slice 1 plan: every claim lands as a
source_values row and the merged columns are computed by merge() — an
identity copy while file_tags is the only source, but a real seam.
Structured fields (artists, genres) are written relationally at add
time; their merge story arrives with the second source. Originals are
never modified; copies land under <root>/album-<id>/.
"""

import hashlib
import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from leeks import db, tags
from leeks.detect import detect
from leeks.models import AlbumInfo
from leeks.orm import (
    Album,
    AlbumGenre,
    Artist,
    ArtistCredit,
    File,
    Genre,
    Source,
    SourceValue,
    Track,
)

# The scalar columns merge() owns, with their casts back from claim text.
MERGED_FIELDS: dict[str, dict[str, type]] = {
    "album": {"title": str, "year": int},
    "track": {"title": str, "track": int},
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


def merge(session: Session, entity_type: str, entity_id: int, row: object) -> None:
    """Recompute merged columns from the entity's source_values.

    Identity while file_tags is the only source; real merge strategies
    slot in here when a second source exists.
    """
    claims = session.scalars(
        select(SourceValue).where(
            SourceValue.entity_type == entity_type,
            SourceValue.entity_id == entity_id,
        )
    )
    for claim in claims:
        cast = MERGED_FIELDS[entity_type].get(claim.field)
        if cast is not None:
            setattr(row, claim.field, cast(claim.value))


def add(directory: Path) -> Added:
    """Ingest one album: detect, assemble, record claims, merge, copy."""
    directory = directory.expanduser().resolve()
    info = tags.assemble(detect(directory))
    with db.session() as session:
        _refuse_readds(session, info)
        now = datetime.now(UTC).replace(tzinfo=None)
        file_tags = session.scalars(
            select(Source).where(Source.name == "file_tags")
        ).one()

        # The directory name is the fallback for the NOT NULL title, not a claim.
        album = Album(title=info.title or directory.name, added=now)
        session.add(album)
        session.flush()
        _credit_artists(session, info, album)
        _link_genre(session, info, album)
        tracks = _create_tracks(session, info, album, now)

        claims = _record_claims(session, info, album, tracks, file_tags, now)
        merge(session, "album", album.id, album)
        for row in tracks:
            merge(session, "track", row.id, row)

        destination = db.library_root() / f"album-{album.id}"
        try:
            _copy_files(session, info, tracks, destination, now)
            session.commit()
            return Added(
                album_id=album.id,
                title=album.title,
                artist=info.artist,
                year=album.year,
                tracks=len(tracks),
                claims=claims,
                destination=destination,
            )
        except BaseException:
            session.rollback()
            shutil.rmtree(destination, ignore_errors=True)
            raise


def _refuse_readds(session: Session, info: AlbumInfo) -> None:
    sources = [str(track.path) for track in info.tracks]
    known = session.scalars(
        select(File.source_path).where(File.source_path.in_(sources))
    ).all()
    if known:
        raise AlreadyAdded(f"already added ({len(known)} of these files are known)")


def _get_or_create[R: (Artist, Genre)](
    session: Session, model: type[R], name: str
) -> R:
    row = session.scalar(select(model).where(model.name == name))
    if row is None:
        row = model(name=name)
        session.add(row)
        session.flush()
    return row


def _credit_artists(session: Session, info: AlbumInfo, album: Album) -> None:
    if info.artist:
        artist = _get_or_create(session, Artist, info.artist)
        session.add(
            ArtistCredit(
                artist_id=artist.id, album_id=album.id, role="albumartist", position=0
            )
        )


def _link_genre(session: Session, info: AlbumInfo, album: Album) -> None:
    if info.genre:
        genre = _get_or_create(session, Genre, info.genre)
        session.add(AlbumGenre(album_id=album.id, genre_id=genre.id))


def _create_tracks(
    session: Session, info: AlbumInfo, album: Album, now: datetime
) -> list[Track]:
    rows = []
    for track in info.tracks:
        # The file stem is the fallback for the NOT NULL title, not a claim.
        row = Track(
            album_id=album.id,
            title=track.title or track.path.stem,
            track=track.track,
            added=now,
        )
        session.add(row)
        session.flush()
        if track.artist:
            artist = _get_or_create(session, Artist, track.artist)
            session.add(
                ArtistCredit(
                    artist_id=artist.id, track_id=row.id, role="artist", position=0
                )
            )
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

    for field in ("title", "artist", "year", "genre", "tracktotal"):
        claim("album", album.id, field, getattr(info, field))
    for track, row in zip(info.tracks, tracks):
        claim("track", row.id, "title", track.title)
        claim("track", row.id, "artist", track.artist)
        claim("track", row.id, "track", track.track)
    session.add_all(claimed)
    return len(claimed)


def _slug(title: str) -> str:
    ascii_ish = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", ascii_ish).strip("-").lower() or "track"


def _copy_files(
    session: Session,
    info: AlbumInfo,
    tracks: list[Track],
    destination: Path,
    now: datetime,
) -> None:
    destination.mkdir(parents=True)
    taken: set[str] = set()
    for track, row in zip(info.tracks, tracks):
        name = _slug(row.title)
        if row.track is not None:
            name = f"{row.track:02d}-{name}"
        if name in taken:
            name = f"{name}-{row.id}"
        taken.add(name)
        copy = destination / f"{name}{track.path.suffix.lower()}"
        sha256 = _copy_and_hash(track.path, copy)
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
                sha256=sha256,
                mtime=facts.mtime,
                added=now,
            )
        )


def _copy_and_hash(source: Path, copy: Path) -> str:
    shutil.copyfile(source, copy)
    digest = hashlib.sha256()
    with copy.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()
