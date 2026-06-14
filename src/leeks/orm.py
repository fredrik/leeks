"""The persistence layer: SQLAlchemy ORM models.

Persistence only (ADR 0001): pipeline code speaks Pydantic and never
receives these objects. The schema realises the part of the entity
hierarchy that file tags can populate (ADR 0006); measurements live on
file rows, claims in source_values (ADR 0007).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, MetaData, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Deterministic constraint names, so future migrations can refer to them.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Album(Base):
    """A release: one specific edition. Release groups arrive with MusicBrainz."""

    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    # A single artist link; the credits table (roles, ordering, join
    # phrases) arrives with the MusicBrainz data that populates it.
    artist_id: Mapped[int | None] = mapped_column(ForeignKey("artists.id"))
    year: Mapped[int | None]
    added: Mapped[datetime]

    tracks: Mapped[list[Track]] = relationship(
        back_populates="album", order_by="Track.id"
    )


class Track(Base):
    """A position on an album, realised by one or more files."""

    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NOT NULL: add is single-album and singletons are excluded, per the punt.
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"))
    title: Mapped[str]
    # Set only when the track's artist overrides the album's.
    artist_id: Mapped[int | None] = mapped_column(ForeignKey("artists.id"))
    track: Mapped[int | None]
    added: Mapped[datetime]

    album: Mapped[Album] = relationship(back_populates="tracks")
    files: Mapped[list[File]] = relationship(back_populates="track")


class File(Base):
    """Bytes on disk realising a track; beyond the paths, all measurements."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"))
    path: Mapped[str] = mapped_column(unique=True)
    # Where the original lives; re-adds are refused against it (the punt).
    source_path: Mapped[str] = mapped_column(unique=True)
    format: Mapped[str]
    bitrate: Mapped[int | None]
    samplerate: Mapped[int | None]
    channels: Mapped[int | None]
    duration: Mapped[float | None]
    size: Mapped[int]
    sha256: Mapped[str]
    mtime: Mapped[float]
    added: Mapped[datetime]

    track: Mapped[Track] = relationship(back_populates="files")


class Artist(Base):
    """A first-class artist row; raw credit strings until MusicBrainz refines."""

    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NOCASE: "Daft Punk" and "Daft punk" are one artist, spelled as first
    # seen (ADR 0010). ASCII folding only; aliases arrive later.
    name: Mapped[str] = mapped_column(String(collation="NOCASE"), unique=True)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NOCASE for the same reason as artists: "Indie Rock" is "indie rock".
    name: Mapped[str] = mapped_column(String(collation="NOCASE"), unique=True)


class AlbumGenre(Base):
    __tablename__ = "album_genres"

    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)


class Source(Base):
    """A registered metadata source. Priority arrives with the second one."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class SourceValue(Base):
    """One source's claim about one field of one entity (ADR 0007)."""

    __tablename__ = "source_values"
    __table_args__ = (
        # value is in the key: a field may be set-valued (genre), so one
        # source can make several claims for it — but never the same one
        # twice (ADR 0022). Single-valued fields stay single by the write
        # path's discipline, not this constraint.
        UniqueConstraint("source_id", "entity_type", "entity_id", "field", "value"),
        CheckConstraint("entity_type IN ('album', 'track')", name="entity_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    entity_type: Mapped[str]  # "album" | "track"
    entity_id: Mapped[int]
    field: Mapped[str]
    value: Mapped[str]
    added: Mapped[datetime]

    source: Mapped[Source] = relationship()
