"""Pipeline models: the lingua franca between sources and the library.

Pydantic in the pipeline, ORM at rest (ADR 0001). These carry claims
only — absent tags are absent fields, never empty strings — and they are
slice-sized, growing as sources demand. Measurements travel separately
(ADR 0007); see tags.FileFacts.
"""

from pathlib import Path

from pydantic import BaseModel, Field


class TrackInfo(BaseModel):
    # Files belong to persistence, but the pipeline must keep each track
    # tied to the bytes it came from; the path is that thread.
    path: Path
    title: str | None = None
    # Present only when it overrides the album artist (a feat. credit).
    artist: str | None = None
    track: int | None = Field(default=None, ge=1)


class AlbumInfo(BaseModel):
    title: str | None = None
    artist: str | None = None
    year: int | None = Field(default=None, ge=1000, le=2999)
    genre: str | None = None
    tracktotal: int | None = Field(default=None, ge=1)
    tracks: list[TrackInfo] = []
