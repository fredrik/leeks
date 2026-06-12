"""Reading files: claims into pipeline models, measurements kept apart.

All tag I/O goes through mediafile (project convention). A file yields
two distinct things (ADR 0007): FileTags, the claims its tags make, and
FileFacts, measurements of the bytes. They never mix.
"""

from dataclasses import dataclass
from pathlib import Path

from mediafile import MediaFile, UnreadableFileError

from leeks.models import AlbumInfo, TrackInfo


@dataclass(frozen=True)
class FileTags:
    """The claims one file's tags make, raw and per-file."""

    path: Path
    title: str | None
    artist: str | None
    albumartist: str | None
    album: str | None
    year: int | None
    genre: str | None
    track: int | None
    tracktotal: int | None


@dataclass(frozen=True)
class FileFacts:
    """Measurements of one file: facts about the bytes, never claims."""

    path: Path
    format: str
    bitrate: int | None
    samplerate: int | None
    channels: int | None
    duration: float | None
    size: int
    mtime: float


def _text(value: str | None) -> str | None:
    # An empty tag is an absent claim, never an empty string.
    return value if value else None


def read_tags(path: Path) -> FileTags | None:
    """The file's claims, or None if mediafile cannot read it as audio."""
    try:
        media = MediaFile(str(path))
    except UnreadableFileError:
        return None
    return FileTags(
        path=path,
        title=_text(media.title),
        artist=_text(media.artist),
        albumartist=_text(media.albumartist),
        album=_text(media.album),
        year=media.year,
        genre=_text(media.genre),
        track=media.track,
        tracktotal=media.tracktotal,
    )


def measure(path: Path) -> FileFacts:
    """Measurements of a readable audio file."""
    media = MediaFile(str(path))
    stat = path.stat()
    return FileFacts(
        path=path,
        format=media.format,
        bitrate=media.bitrate,
        samplerate=media.samplerate,
        channels=media.channels,
        duration=media.length,
        size=stat.st_size,
        mtime=stat.st_mtime,
    )


def _consensus[T](values: list[T | None]) -> T | None:
    """The single value everyone who speaks agrees on, else nothing."""
    distinct = {value for value in values if value is not None}
    return distinct.pop() if len(distinct) == 1 else None


def assemble(files: list[FileTags]) -> AlbumInfo:
    """Per-file claims become one album: consensus above, tracks below.

    Track order is track number then filename; unnumbered tracks sort
    after numbered ones. The directory name is not a claim and never
    appears here — fallbacks for NOT NULL columns happen at write time.
    """
    ordered = sorted(files, key=lambda f: (f.track is None, f.track or 0, f.path.name))
    album_artist = _consensus([f.albumartist for f in files]) or _consensus(
        [f.artist for f in files]
    )
    tracks = [
        TrackInfo(
            path=f.path,
            title=f.title,
            artist=f.artist if f.artist != album_artist else None,
            track=f.track,
        )
        for f in ordered
    ]
    return AlbumInfo(
        title=_consensus([f.album for f in files]),
        artist=album_artist,
        year=_consensus([f.year for f in files]),
        genre=_consensus([f.genre for f in files]),
        tracktotal=_consensus([f.tracktotal for f in files]),
        tracks=tracks,
    )
