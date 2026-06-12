# teebs Data Model

Canonical design for the core data model of teebs, a metadata reconciliation engine for music and successor to beets.

> **Provenance.** Synthesized from three independently generated drafts (v0, v1, v2 — same prompt) produced at teebs
> commit `c761a9b`. v0 designed the normalized album/track core, v1 added the MusicBrainz-shaped entity hierarchy
> (release groups, recordings, works), and v2 added the source layer. This document merges them into one record of the
> teebs design phase.

## Principles

- **Pydantic for validation, SQLAlchemy for storage.** Two separate layers. Pydantic models are the lingua franca of the
  pipeline — every stage validates through them. ORM models are just persistence.
- **Proper normalization.** No denormalization of album fields onto tracks. Artists, genres, and external IDs are proper
  relationships, not flattened columns.
- **Real columns, not JSON blobs.** The database is the integration point — it should be queryable with plain SQL by any
  tool.
- **Paths as TEXT, not BLOB.** It's 2026, filesystems are UTF-8.
- **Nullable references over mandatory hierarchy.** ReleaseGroup, Recording, and Work are useful when available but
  never required. A track with no recording reference and an album with no release group still work fine.
- **Sources are layers, not overwrites.** Every source's data is preserved independently. The merged view is computed,
  not authoritative.
- **Import everything, gate nothing.** Confidence is recorded, not enforced.
- **Non-destructive by default.** File modifications are explicit, separate actions — never side effects of import or
  matching.

## Architecture

```
                    Sources (background)
    ┌──────────┬──────────┬──────────┬──────────┐
    │file_tags │musicbrainz│ discogs  │ acoustid │ ...
    └────┬─────┴────┬─────┴────┬─────┴────┬─────┘
         │          │          │          │
         ▼          ▼          ▼          ▼
    ┌─────────────────────────────────────────┐
    │         source_values (per-field)        │
    │  entity + field + source + value + conf  │
    └──────────────────┬──────────────────────┘
                       │
              ┌────────┴────────┐
              │  pending_changes │  (new/changed values awaiting review)
              └────────┬────────┘
                       │
              human / agent / auto-rules
                       │
                       ▼
    ┌─────────────────────────────────────────┐
    │          Merged view (materialized)      │
    │  albums, tracks, artists, recordings,   │
    │  works, release_groups, artist_credits,  │
    │  genres, external_ids                    │
    └─────────────────────────────────────────┘
                       │
              ┌────────┴────────┐
              │  file operations │  (explicit, opt-in)
              │  tag write-back  │
              │  rename / move   │
              └─────────────────┘
```

### Design rationale: the source layer (Claude, 2026-03-31)

Beets conflates "should this file enter the library?" with "how confident are we in the metadata match?" — using
confidence as an import gate. This means unmatched music is unmanaged music, which is the worst outcome for the files
that need management most.

The source layer separates these concerns. Import is unconditional. Confidence is metadata about metadata, stored
per-source and used by merge rules — never as a gate. A 0.70 match today is stored and available; when a 0.98 match
arrives tomorrow, it supersedes without data loss.

The per-field granularity (rather than per-entity) is essential because sources disagree at the field level: MB has a
great title but wrong year, Discogs has the right year, the user manually fixed the genre. Per-entity source tracking
would force an all-or-nothing choice.

See `plans/design-principles.md` for the broader reasoning behind these decisions.

### Design rationale: the entity hierarchy (Claude, 2026-03-31)

A flat Album/Track model — what beets has — flattens MusicBrainz's hierarchy and is the "minimal" path. The "full" path
would replicate MB's generic relationship graph locally, which is scope creep for a file manager. teebs takes the middle
path, based on domain analysis of MusicBrainz, Discogs, FRBR, and the Music Ontology: three small lookup tables
(ReleaseGroup, Recording, Work) with FKs from existing tables, plus one column (`join_phrase` on artist credits).

1. **ReleaseGroup** — separates "the album concept" from "a specific edition." Enables deduplication across pressings,
   anniversary editions, regional variants. Populated from MB's release group ID during autotagging.
2. **Recording** — the audio itself, independent of which album it appears on. Enables "how many copies of this track do
   I have?" across compilations, soundtracks, best-ofs. Populated from MB's recording ID.
3. **Work** — the composition, independent of who performed it. Self-referential `parent_id` handles movements
   (classical) and also enables cover/remix tracking for non-classical music. Populated from MB's work ID.
4. **join_phrase on ArtistCredit** — enables lossless reconstruction of multi-artist display strings ("X feat. Y", "X &
   Y", "X, Y and Z") without string parsing heuristics.

This gives teebs the ability to answer relational questions locally — "what other editions of this album do I own?",
"what other performances of this composition do I have?", "how many copies of this track exist across my library?" —
without round-tripping to the MB API.

The acid test for music domain models is classical music. Without Work and sub-works, classical users have no way to
group movements or distinguish composer from performer. The self-referential `parent_id` on Work handles this with
minimal schema complexity. Non-classical users simply never populate it.

All four additions are nullable/optional. Nothing breaks when the data isn't available. They cost nothing for users who
don't care, and they're populated for free during MusicBrainz autotagging.

## Pipeline and Validation Layer

```
file tags ──→ TrackInfo ──→ plugins ──→ TrackInfo ──→ ORM ──→ SQLite
MusicBrainz ─┘                                        ↑
user edits ────────────────────────────────────────────┘
```

`TrackInfo` / `AlbumInfo` are Pydantic models. They flow through the entire import and editing pipeline: source plugins
produce them, the engine decomposes them into `source_values` rows, and the merged view is serialized back out through
them. ORM models accept validated data via `update_from(info)` and produce it via `to_info()`. With the source layer in
place, the arrow into the ORM passes through `source_values` and `pending_changes` rather than writing the merged view
directly — but the Pydantic models remain the validation boundary at every stage.

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Annotated

Year = Annotated[int | None, Field(ge=1000, le=2999)]
TrackNum = Annotated[int | None, Field(ge=0)]


class ArtistRef(BaseModel):
    name: str
    sort_name: str = ""
    credited_name: str = ""
    join_phrase: str = ""  # " feat. ", " & ", ", ", etc.
    role: str = "artist"  # artist, albumartist, composer, remixer, lyricist, arranger
    mb_id: str | None = None


class RecordingRef(BaseModel):
    """Reference to a recording (the audio itself, independent of release)."""
    title: str = ""
    mb_id: str | None = None
    length: float | None = None


class WorkRef(BaseModel):
    """Reference to a work (the composition, independent of performance)."""
    title: str = ""
    mb_id: str | None = None
    parent_mb_id: str | None = None  # for movements


class ReleaseGroupRef(BaseModel):
    """Reference to a release group (the album concept, independent of edition)."""
    title: str = ""
    mb_id: str | None = None
    primary_type: str = ""  # album, single, ep, broadcast, other
    secondary_types: list[str] = []  # compilation, soundtrack, live, remix, dj-mix


class TrackInfo(BaseModel):
    title: str = ""
    artists: list[ArtistRef] = []
    album: str = ""
    year: Year = None
    track: TrackNum = None
    disc: TrackNum = None
    disctitle: str = ""
    genres: list[str] = []
    length: float | None = None
    lyrics: str = ""
    comments: str = ""
    bpm: int | None = None
    initial_key: str | None = None
    recording: RecordingRef | None = None
    works: list[WorkRef] = []
    external_ids: dict[str, str] = {}  # {"musicbrainz:recording": "uuid", "isrc": "XX..."}


class AlbumInfo(BaseModel):
    title: str = ""
    artists: list[ArtistRef] = []
    year: Year = None
    month: int | None = None
    day: int | None = None
    original_year: Year = None
    original_month: int | None = None
    original_day: int | None = None
    country: str = ""
    label: str = ""
    catalognum: str = ""
    albumstatus: str = ""
    albumdisambig: str = ""
    comp: bool = False
    disctotal: int | None = None
    tracktotal: int | None = None
    media: str = ""
    script: str = ""
    language: str = ""
    barcode: str = ""
    genres: list[str] = []
    albumtypes: list[str] = []
    release_group: ReleaseGroupRef | None = None
    external_ids: dict[str, str] = {}
```

## Source Layer

### sources

Registry of metadata sources.

```python
class SourceORM(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)  # "file_tags", "musicbrainz", etc.
    priority: Mapped[int] = mapped_column(default=0)  # higher = wins ties
    enabled: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        Index("idx_source_name", "name"),
    )
```

Default sources and suggested priorities (configurable):

| Source        | Priority | Notes                               |
| ------------- | -------- | ----------------------------------- |
| `file_tags`   | 10       | Baseline. Always exists.            |
| `acoustid`    | 20       | Fingerprint-based identification.   |
| `musicbrainz` | 50       | Rich structured data.               |
| `discogs`     | 40       | Strong on physical release details. |
| `lastfm`      | 30       | Genres/tags mainly.                 |
| `user`        | 100      | Manual edits always win.            |

### source_values

Per-field, per-source metadata values. This is the core table of the source layer.

```python
class SourceValueORM(Base):
    __tablename__ = "source_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    entity_type: Mapped[str]  # "track", "album"
    entity_id: Mapped[int]    # FK to tracks.id or albums.id
    field: Mapped[str]        # "title", "year", "country", etc.
    value: Mapped[str]        # stored as text, interpreted by field type
    confidence: Mapped[float] = mapped_column(default=1.0)  # 0.0–1.0
    fetched_at: Mapped[float] = mapped_column(default=0.0)  # unix timestamp

    source: Mapped[SourceORM] = relationship()

    __table_args__ = (
        UniqueConstraint("source_id", "entity_type", "entity_id", "field"),
        Index("idx_sv_entity", "entity_type", "entity_id"),
        Index("idx_sv_source", "source_id"),
        Index("idx_sv_field", "entity_type", "entity_id", "field"),
    )
```

**On value storage:** All values stored as text. Field types are known from the schema (year is int, title is str,
etc.), so the application layer handles conversion. This keeps the source_values table simple and avoids parallel typed
columns.

**On structured fields (artists, genres):** These are multi-valued and relational in the merged view, but in the source
layer they're stored as serialized values per source. For example, a `file_tags` source might store `artists` as
`"DJ Koze feat. Apparat"` (raw tag string), while `musicbrainz` stores it as a JSON array of artist credit objects. The
merge logic for structured fields is more complex than for scalar fields — it must parse source-specific formats and
reconcile into the normalized merged view.

```
source_values examples:

source=file_tags,  entity=track:42, field=title, value="Karma Police"
source=file_tags,  entity=track:42, field=year,  value="1997"
source=musicbrainz, entity=track:42, field=title, value="Karma Police", confidence=0.95
source=musicbrainz, entity=track:42, field=year,  value="1997", confidence=0.95
source=discogs,    entity=track:42, field=year,  value="1998", confidence=0.88
source=user,       entity=track:42, field=year,  value="1997"
```

### source_matches

When a source identifies an entity (e.g., MB matches a track to a recording), the match itself is recorded with its
overall confidence. This is separate from per-field values — it captures "MB thinks this album is release X" at the
entity level.

```python
class SourceMatchORM(Base):
    __tablename__ = "source_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    entity_type: Mapped[str]  # "track", "album"
    entity_id: Mapped[int]
    external_type: Mapped[str]  # "release", "recording", "master_release", etc.
    external_id: Mapped[str]    # the source's ID for the match
    confidence: Mapped[float] = mapped_column(default=0.0)
    matched_at: Mapped[float] = mapped_column(default=0.0)

    source: Mapped[SourceORM] = relationship()

    __table_args__ = (
        UniqueConstraint("source_id", "entity_type", "entity_id", "external_type"),
        Index("idx_sm_entity", "entity_type", "entity_id"),
        Index("idx_sm_external", "source_id", "external_type", "external_id"),
    )
```

```
source_matches examples:

source=musicbrainz, entity=album:7, external_type=release,
    external_id="abc-123", confidence=0.92
source=musicbrainz, entity=album:7, external_type=release_group,
    external_id="def-456", confidence=0.92
source=discogs, entity=album:7, external_type=master_release,
    external_id="12345", confidence=0.85
source=acoustid, entity=track:42, external_type=recording,
    external_id="ghi-789", confidence=0.78
```

### pending_changes

Queue of source-provided changes awaiting review (human or agent) before updating the merged view.

```python
class PendingChangeORM(Base):
    __tablename__ = "pending_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    entity_type: Mapped[str]
    entity_id: Mapped[int]
    field: Mapped[str]
    old_value: Mapped[str | None]  # current merged view value (for display)
    new_value: Mapped[str]         # proposed value from source
    confidence: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(default="pending")  # pending, accepted, rejected
    created_at: Mapped[float] = mapped_column(default=0.0)
    reviewed_at: Mapped[float | None]
    reviewed_by: Mapped[str | None]  # "user", "agent:auto-accept", etc.

    source: Mapped[SourceORM] = relationship()

    __table_args__ = (
        Index("idx_pc_status", "status"),
        Index("idx_pc_entity", "entity_type", "entity_id"),
    )
```

## Merge Rules

Merge rules determine how source values are combined into the merged view. Stored as configuration (YAML/TOML), not in
the database.

```yaml
# Example merge config
merge:
  # Default: highest priority source wins
  strategy: priority

  # Per-field overrides
  overrides:
    genre:
      # For genres, combine all sources (union)
      strategy: union
    year:
      # For year, prefer highest confidence regardless of priority
      strategy: highest_confidence
    lyrics:
      # For lyrics, prefer longest non-empty value
      strategy: longest

  # Auto-accept rules (bypass pending queue)
  auto_accept:
    - source: musicbrainz
      min_confidence: 0.95
    - source: user
      # User edits always auto-accepted
      min_confidence: 0.0

  # Auto-reject rules
  auto_reject:
    - source: "*"
      max_confidence: 0.30
```

Merge strategies:

| Strategy             | Behaviour                                                            |
| -------------------- | -------------------------------------------------------------------- |
| `priority`           | Highest priority source with a non-empty value wins. Default.        |
| `highest_confidence` | Source with highest confidence wins, ignoring priority.              |
| `union`              | Combine values from all sources (for set-valued fields like genres). |
| `longest`            | Longest non-empty value wins (useful for lyrics, comments).          |
| `newest`             | Most recently fetched value wins.                                    |

## Merged View (Materialized)

The merged view tables are the "effective" library that queries, templates, CLI, and plugins operate on. They are
recomputed from source data when:

- A pending change is accepted
- Merge rules are changed
- A full refresh is triggered

### Entity Hierarchy

```
┌─────────────────┐
│  ReleaseGroup    │  "OK Computer" as a concept
│  mb_id, title    │
└────────┬────────┘
         │ 1:N
┌────────┴────────┐
│     Album        │  specific edition (UK CD, US vinyl, 25th anniv.)
│  + release_group │
└────────┬────────┘
         │ 1:N
┌────────┴────────┐
│     Track        │  position on this album, links to a file
│  + recording_id  │
└────────┬────────┘
         │ N:1
┌────────┴────────┐
│   Recording      │  the audio itself, shared across albums
│  mb_id, title    │
└────────┬────────┘
         │ N:N (recording_works junction)
┌────────┴────────┐
│     Work         │  the composition
│  mb_id, title    │
│  parent_id (self)│  movements / parts
└─────────────────┘
```

### release_groups

```python
class ReleaseGroupORM(Base):
    __tablename__ = "release_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(default="")
    mb_id: Mapped[str | None] = mapped_column(unique=True)
    primary_type: Mapped[str] = mapped_column(default="")
    secondary_types: Mapped[str] = mapped_column(default="")  # comma-separated

    albums: Mapped[list["AlbumORM"]] = relationship(back_populates="release_group")

    __table_args__ = (
        Index("idx_rg_title", "title"),
    )
```

### albums

Release-level data for a specific edition/pressing. No per-track info, no artist columns.

```python
class AlbumORM(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    release_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("release_groups.id")
    )
    title: Mapped[str] = mapped_column(default="")
    year: Mapped[int | None]
    month: Mapped[int | None]
    day: Mapped[int | None]
    original_year: Mapped[int | None]
    original_month: Mapped[int | None]
    original_day: Mapped[int | None]
    country: Mapped[str] = mapped_column(default="")
    label: Mapped[str] = mapped_column(default="")
    catalognum: Mapped[str] = mapped_column(default="")
    albumstatus: Mapped[str] = mapped_column(default="")
    albumdisambig: Mapped[str] = mapped_column(default="")
    comp: Mapped[bool] = mapped_column(default=False)
    disctotal: Mapped[int | None]
    tracktotal: Mapped[int | None]
    media: Mapped[str] = mapped_column(default="")
    script: Mapped[str] = mapped_column(default="")
    language: Mapped[str] = mapped_column(default="")
    barcode: Mapped[str] = mapped_column(default="")
    artpath: Mapped[str | None]
    added: Mapped[float] = mapped_column(default=0.0)

    # Relationships
    release_group: Mapped["ReleaseGroupORM | None"] = relationship(
        back_populates="albums"
    )
    tracks: Mapped[list["TrackORM"]] = relationship(
        back_populates="album", cascade="all, delete-orphan"
    )
    artist_credits: Mapped[list["ArtistCreditORM"]] = relationship()
    external_ids: Mapped[list["ExternalIDORM"]] = relationship()
    genres: Mapped[list["AlbumGenreORM"]] = relationship()
    albumtypes: Mapped[list["AlbumTypeORM"]] = relationship()

    def to_info(self) -> AlbumInfo:
        return AlbumInfo.model_validate(self, from_attributes=True)

    def update_from(self, info: AlbumInfo):
        for key, val in info.model_dump(exclude_unset=True).items():
            if hasattr(self, key):
                setattr(self, key, val)
```

### recordings

The audio itself, independent of which album it appears on.

```python
class RecordingORM(Base):
    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(default="")
    mb_id: Mapped[str | None] = mapped_column(unique=True)
    length: Mapped[float | None]

    tracks: Mapped[list["TrackORM"]] = relationship(back_populates="recording")
    works: Mapped[list["WorkORM"]] = relationship(
        secondary="recording_works", back_populates="recordings"
    )

    __table_args__ = (
        Index("idx_recording_title", "title"),
    )
```

### works

The composition, independent of who performed it.

```python
class WorkORM(Base):
    __tablename__ = "works"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(default="")
    mb_id: Mapped[str | None] = mapped_column(unique=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("works.id"))

    parent: Mapped["WorkORM | None"] = relationship(
        remote_side=[id], back_populates="parts"
    )
    parts: Mapped[list["WorkORM"]] = relationship(back_populates="parent")
    recordings: Mapped[list[RecordingORM]] = relationship(
        secondary="recording_works", back_populates="works"
    )

    __table_args__ = (
        Index("idx_work_title", "title"),
        Index("idx_work_parent", "parent_id"),
    )
```

### recording_works

Junction table linking recordings to works (N:N because a single recording can contain multiple works, e.g. a medley,
and a single work can have many recordings).

```python
class RecordingWorkORM(Base):
    __tablename__ = "recording_works"

    recording_id: Mapped[int] = mapped_column(
        ForeignKey("recordings.id"), primary_key=True
    )
    work_id: Mapped[int] = mapped_column(
        ForeignKey("works.id"), primary_key=True
    )
```

### tracks

Track-specific data only. ~18 columns, against the 92 on beets' `items`.

```python
class TrackORM(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(unique=True)
    album_id: Mapped[int | None] = mapped_column(ForeignKey("albums.id"))
    recording_id: Mapped[int | None] = mapped_column(ForeignKey("recordings.id"))

    # Track metadata
    title: Mapped[str] = mapped_column(default="")
    track: Mapped[int | None]
    disc: Mapped[int | None]
    disctitle: Mapped[str] = mapped_column(default="")
    lyrics: Mapped[str] = mapped_column(default="")
    comments: Mapped[str] = mapped_column(default="")
    bpm: Mapped[int | None]
    initial_key: Mapped[str | None]
    length: Mapped[float | None]

    # Audio properties (read-only from file)
    bitrate: Mapped[int | None]
    bitrate_mode: Mapped[str] = mapped_column(default="")
    samplerate: Mapped[int | None]
    bitdepth: Mapped[int | None]
    channels: Mapped[int | None]
    format: Mapped[str] = mapped_column(default="")
    encoder: Mapped[str] = mapped_column(default="")

    # Housekeeping
    mtime: Mapped[float] = mapped_column(default=0.0)
    added: Mapped[float] = mapped_column(default=0.0)

    # Relationships
    album: Mapped["AlbumORM | None"] = relationship(back_populates="tracks")
    recording: Mapped["RecordingORM | None"] = relationship(back_populates="tracks")
    artist_credits: Mapped[list["ArtistCreditORM"]] = relationship()
    external_ids: Mapped[list["ExternalIDORM"]] = relationship()
    genres: Mapped[list["TrackGenreORM"]] = relationship()

    __table_args__ = (
        Index("idx_track_album_id", "album_id"),
        Index("idx_track_recording_id", "recording_id"),
        Index("idx_track_title", "title"),
    )

    def to_info(self) -> TrackInfo:
        return TrackInfo.model_validate(self, from_attributes=True)

    def update_from(self, info: TrackInfo):
        for key, val in info.model_dump(exclude_unset=True).items():
            if hasattr(self, key):
                setattr(self, key, val)
```

### artists

Deduplicated artist entities.

```python
class ArtistORM(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    sort_name: Mapped[str] = mapped_column(default="")
    mb_id: Mapped[str | None] = mapped_column(unique=True)

    __table_args__ = (
        Index("idx_artist_name", "name"),
    )
```

### artist_credits

Who did what on which album or track, with ordering and display info. Replaces beets' `artist`, `artists`,
`artist_sort`, `artists_sort`, `artist_credit`, `artists_credit`, `albumartist`, `albumartists`, `albumartist_sort`,
`albumartists_sort`, `albumartist_credit`, `albumartists_credit`, `composer`, `composer_sort`, `lyricist`, `arranger`,
`remixer` columns.

```python
class ArtistCreditORM(Base):
    __tablename__ = "artist_credits"

    id: Mapped[int] = mapped_column(primary_key=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"))
    album_id: Mapped[int | None] = mapped_column(ForeignKey("albums.id"))
    track_id: Mapped[int | None] = mapped_column(ForeignKey("tracks.id"))
    role: Mapped[str] = mapped_column(default="artist")
    credited_name: Mapped[str] = mapped_column(default="")
    join_phrase: Mapped[str] = mapped_column(default="")  # " feat. ", " & ", etc.
    position: Mapped[int] = mapped_column(default=0)

    artist: Mapped[ArtistORM] = relationship()

    __table_args__ = (
        Index("idx_credit_album", "album_id"),
        Index("idx_credit_track", "track_id"),
        Index("idx_credit_artist", "artist_id"),
    )
```

`role` values: `"artist"`, `"albumartist"`, `"composer"`, `"remixer"`, `"lyricist"`, `"arranger"`, `"conductor"`,
`"producer"`, etc.

`credited_name` allows "Phife Dawg" on one album and "Malik Taylor" on another, while both point to the same `ArtistORM`
row.

`join_phrase` is the text that follows this artist in a display string. For "DJ Koze feat. Apparat": position 0 has
`join_phrase=" feat. "`, position 1 has `join_phrase=""`. Display is reconstructed by concatenating
`credited_name + join_phrase` in position order.

`position` preserves ordering for multi-artist credits.

### genres

Deduplicated genre names with junction tables for albums and tracks.

```python
class GenreORM(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class AlbumGenreORM(Base):
    __tablename__ = "album_genres"

    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)

    genre: Mapped[GenreORM] = relationship()


class TrackGenreORM(Base):
    __tablename__ = "track_genres"

    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)

    genre: Mapped[GenreORM] = relationship()
```

### external_ids

Generic external identifier storage on the merged view. Replaces beets' `mb_trackid`, `mb_albumid`, `mb_artistid`,
`mb_albumartistid`, `mb_albumartistids`, `mb_releasetrackid`, `mb_releasegroupid`, `mb_workid`, `discogs_albumid`,
`discogs_artistid`, `discogs_labelid`, `asin`, `isrc`, `acoustid_id`, `acoustid_fingerprint` — all one pattern.

```python
class ExternalIDORM(Base):
    __tablename__ = "external_ids"

    id: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int | None] = mapped_column(ForeignKey("albums.id"))
    track_id: Mapped[int | None] = mapped_column(ForeignKey("tracks.id"))
    source: Mapped[str]   # "musicbrainz", "discogs", "acoustid", "isrc", "asin"
    kind: Mapped[str]     # "release", "recording", "artist", "release_group", "work", "fingerprint"
    value: Mapped[str]

    __table_args__ = (
        Index("idx_ext_lookup", "source", "kind", "value"),
        Index("idx_ext_album", "album_id"),
        Index("idx_ext_track", "track_id"),
    )
```

### flex_attrs

For plugin-defined custom fields. Unlike beets, values are typed via a `type` column.

```python
class FlexAttrORM(Base):
    __tablename__ = "flex_attrs"

    id: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int | None] = mapped_column(ForeignKey("albums.id"))
    track_id: Mapped[int | None] = mapped_column(ForeignKey("tracks.id"))
    key: Mapped[str]
    value: Mapped[str]
    type: Mapped[str] = mapped_column(default="str")  # str, int, float, bool, json

    __table_args__ = (
        UniqueConstraint("album_id", "track_id", "key"),
        Index("idx_flex_album", "album_id"),
        Index("idx_flex_track", "track_id"),
    )
```

### replaygain

Separated out because it's a distinct concern — audio loudness metadata that gets recalculated independently.

```python
class ReplayGainORM(Base):
    __tablename__ = "replaygain"

    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"), primary_key=True)
    track_gain: Mapped[float | None]
    track_peak: Mapped[float | None]
    album_gain: Mapped[float | None]
    album_peak: Mapped[float | None]
    r128_track_gain: Mapped[float | None]
    r128_album_gain: Mapped[float | None]
    standard: Mapped[str] = mapped_column(default="")  # "replaygain", "r128"

    track: Mapped[TrackORM] = relationship()
```

## Table Summary

### Source layer

| Table             | Rows represent                                     | Replaces in beets                           |
| ----------------- | -------------------------------------------------- | ------------------------------------------- |
| `sources`         | Registered metadata sources                        | Not modeled                                 |
| `source_values`   | Per-field values from each source, with confidence | Not modeled (sources overwrite each other)  |
| `source_matches`  | Entity-level match identifications per source      | Not modeled (match confidence is discarded) |
| `pending_changes` | Source changes awaiting review                     | Not modeled (import-time prompt only)       |

### Merged view (materialized)

| Table             | Rows represent                             | Replaces in beets                                |
| ----------------- | ------------------------------------------ | ------------------------------------------------ |
| `release_groups`  | The album concept across editions          | Not modeled (`mb_releasegroupid` on albums)      |
| `albums`          | Specific editions/pressings (~22 cols)     | `albums` (44 cols)                               |
| `recordings`      | Distinct audio, shared across releases     | Not modeled (`mb_trackid` on items)              |
| `works`           | Compositions, with movement hierarchy      | Not modeled (`mb_workid` on items)               |
| `recording_works` | Recording-to-work links                    | Not modeled                                      |
| `tracks`          | Audio files on a specific album (~18 cols) | `items` (92 cols)                                |
| `artists`         | Deduplicated people/groups                 | Flattened into 17+ columns on items/albums       |
| `artist_credits`  | Who did what, with display info            | Same                                             |
| `genres`          | Deduplicated genre names                   | `\0`-delimited strings                           |
| `album_genres`    | Album-genre junction                       | Same                                             |
| `track_genres`    | Track-genre junction                       | Same                                             |
| `external_ids`    | MusicBrainz, Discogs, ISRC, etc.           | 15+ `mb_*`/`discogs_*` columns                   |
| `flex_attrs`      | Plugin custom fields (typed)               | `item_attributes` / `album_attributes` (untyped) |
| `replaygain`      | Loudness metadata                          | 6 nullable float columns on items                |

## Key Differences from beets

01. **Sources are layered, not overwritten.** Every source's data is preserved per-field with confidence and provenance.
    The merged view is computed from source data by configurable rules.
02. **Import everything, gate nothing.** Confidence never blocks import; it feeds merge rules and the review queue.
03. **Changes are reviewed, not imposed.** New or changed source data enters `pending_changes` for human or agent review
    (or auto-accept rules), instead of silently rewriting the library.
04. **No denormalization.** Album fields live on albums only. Access via `track.album.year`, not duplicated onto every
    track row.
05. **Artists are entities.** One `artists` table, linked via `artist_credits` with role, ordering, and join phrase. Not
    17 flattened string columns.
06. **Release groups.** "I own OK Computer on CD and vinyl" is a query, not a guess. Anniversary editions, regional
    variants, remasters all group together.
07. **Recordings.** "Karma Police appears on 3 of my albums" is a JOIN, not fuzzy title matching.
08. **Works.** "Show me all performances of Clair de Lune I own" works. Movements nest via `parent_id`. Non-classical
    users pay zero cost.
09. **Join phrases.** "DJ Koze feat. Apparat" is reconstructed from data, not parsed from a string.
10. **External IDs are generic.** One table for MusicBrainz, Discogs, ISRC, AcoustID, ASIN. New sources need zero schema
    changes.
11. **Genres are normalized.** Junction tables, not delimiter-separated strings.
12. **Flex attrs are typed.** A `type` column means plugins can store integers as integers.
13. **Validation is separate from storage.** Pydantic models validate data throughout the pipeline. ORM models just
    persist it.
14. **Alembic for migrations.** Not "add columns, never remove them."

## Example: Import + Source Fetch Lifecycle

```
1. User adds files to watched directory (or runs `teebs import /path`)

2. File scan:
   - Track rows created in merged view (path, audio properties)
   - Album row created (grouped by directory or tag heuristics)
   - file_tags source values written for every tag found in files
   - Merged view computed from file_tags (only source available)

3. Background: MusicBrainz lookup
   - acoustid fingerprint → recording match (confidence 0.82)
   - recording → release match (confidence 0.91)
   - source_matches rows created for both
   - source_values rows created for all MB-provided fields
   - Per auto_accept rules:
     - confidence 0.91 > 0.95 threshold? No → pending_changes created
     - (or if 0.96: auto-accepted, merged view updated immediately)

4. Background: Discogs lookup
   - Same pattern: match, source_values, pending_changes

5. User (or agent) reviews pending changes:
   - "MB says year=1997 (conf 0.91), file says 2003. Accept MB?"
   - User accepts → merged view updated, pending_change status=accepted
   - "Discogs says genre=Britpop, MB says genre=Alternative Rock. Accept?"
   - User accepts both → genres merged (union strategy)

6. Later: MB updates release date
   - Background refetch detects change
   - New pending_change: "MB now says month=6 (was month=5)"
   - Agent auto-accepts (confidence > 0.95, existing match)
   - Merged view updated
```

## Example Queries

Queries against the merged view:

```sql
-- What does my library look like?
SELECT t.title, a.title AS album, t.path
FROM tracks t
JOIN albums a ON t.album_id = a.id;

-- What editions of "OK Computer" do I own?
SELECT a.title, a.year, a.country, a.media, a.catalognum
FROM albums a
JOIN release_groups rg ON a.release_group_id = rg.id
WHERE rg.title = 'OK Computer';

-- How many copies of "Karma Police" do I have across albums?
SELECT t.title, a.title AS album, t.path
FROM tracks t
JOIN recordings r ON t.recording_id = r.id
JOIN albums a ON t.album_id = a.id
WHERE r.title = 'Karma Police';

-- All performances of Clair de Lune in my library
SELECT r.title AS recording, t.path, a.title AS album
FROM works w
JOIN recording_works rw ON rw.work_id = w.id
JOIN recordings r ON rw.recording_id = r.id
JOIN tracks t ON t.recording_id = r.id
JOIN albums a ON t.album_id = a.id
WHERE w.title = 'Clair de lune';

-- All movements of Beethoven's 9th that I own
SELECT w.title AS movement, r.title AS recording, a.title AS album
FROM works parent
JOIN works w ON w.parent_id = parent.id
JOIN recording_works rw ON rw.work_id = w.id
JOIN recordings r ON rw.recording_id = r.id
JOIN tracks t ON t.recording_id = r.id
JOIN albums a ON t.album_id = a.id
WHERE parent.title LIKE 'Symphony No. 9%'
ORDER BY w.title;

-- Display string for a track's artists
SELECT ac.credited_name, ac.join_phrase
FROM artist_credits ac
WHERE ac.track_id = ? AND ac.role = 'artist'
ORDER BY ac.position;
-- Concatenate: credited_name || join_phrase for each row
```

Queries against the source layer:

```sql
-- Where do my sources disagree on year for a specific album?
SELECT s.name AS source, sv.value, sv.confidence
FROM source_values sv
JOIN sources s ON sv.source_id = s.id
WHERE sv.entity_type = 'album'
  AND sv.entity_id = 7
  AND sv.field = 'year';

-- What pending changes need review?
SELECT pc.entity_type, pc.entity_id, pc.field,
       pc.old_value, pc.new_value, pc.confidence,
       s.name AS source
FROM pending_changes pc
JOIN sources s ON pc.source_id = s.id
WHERE pc.status = 'pending'
ORDER BY pc.confidence DESC;

-- How many tracks have no MB match?
SELECT COUNT(*) AS unmatched
FROM tracks t
LEFT JOIN source_matches sm
  ON sm.entity_type = 'track'
  AND sm.entity_id = t.id
  AND sm.source_id = (SELECT id FROM sources WHERE name = 'musicbrainz')
WHERE sm.id IS NULL;

-- Show all source data for a specific track
SELECT s.name AS source, sv.field, sv.value, sv.confidence
FROM source_values sv
JOIN sources s ON sv.source_id = s.id
WHERE sv.entity_type = 'track' AND sv.entity_id = 42
ORDER BY sv.field, s.priority DESC;
```

## Open Questions

- **Path template system.** How does it work with normalized artists? Probably needs a denormalized "display artist"
  helper, e.g. `track.display_artist(role="artist")` → `"A Tribe Called Quest"`.
- **Singleton handling.** Tracks with `album_id = NULL`. Do they need their own album-level metadata (year, label, etc.)
  or is that just omitted?
- **Album art.** Keep as `artpath` on albums, or make it another table to support multiple images (front, back,
  booklet)?
- **Performance.** More JOINs than beets. Need to verify that eager loading (`joinedload` / `selectinload`) keeps common
  operations fast. The hierarchy tables are small (one row per unique recording/work/release group) so their data volume
  increase is modest, but the source layer adds real volume: source_values for a 10k track library with 3 sources is
  ~200k–600k rows. SQLite handles this fine, but the merge recomputation needs to be efficient (incremental, not
  full-table).
- **Work population.** Works and recording-work links are only available from MusicBrainz for a subset of recordings.
  How aggressively should the autotagger try to fetch these? Lazy (only when user asks) vs eager (always during import)?
- **Recording deduplication.** When importing a compilation, should the autotagger try to link tracks to existing
  recordings already in the DB? This would enable the "how many copies" query but adds import complexity.
- **Structured field merging.** Artists and genres are relational in the merged view but serialized in source_values.
  The merge logic for these fields is necessarily more complex than for scalar fields. Needs a clear strategy for how
  e.g. a raw tag string "DJ Koze feat. Apparat" and a MB artist credit JSON array get reconciled into ArtistCreditORM
  rows.
- **Source fetch scheduling.** How often to re-check sources? Per-source config? Global schedule? Event-driven (e.g.,
  refetch when user queries an entity with stale source data)?
- **Pending change grouping.** When MB provides 15 new field values for an album, should those be 15 individual pending
  changes or one grouped change? Grouping is better UX but adds complexity.
- **Agent review interface.** What does the contract look like for an AI agent reviewing pending changes? Probably a
  simple API: list pending, accept/reject with reason, bulk operations.
- **external_ids vs source_matches.** The drafts overlap here: the merged-view `external_ids` table and the source-layer
  `source_matches` table both record external identifiers per entity. One draft frames `external_ids` as the home for
  all MB/Discogs/ISRC IDs; another records the same identifications in `source_matches` with confidence and timestamp.
  Either `external_ids` becomes a materialized projection of accepted `source_matches`, or one of the two is dropped.
  Unresolved.
- **Where does barcode live?** The drafts disagree: `barcode` appears as a real column on `albums` in all of them, yet
  one draft also lists it among the identifiers that `external_ids` replaces. Pick one home (the album column seems
  right — a barcode is a property of the edition, not a foreign key into another database).
