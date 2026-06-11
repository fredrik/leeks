# teebs — Vision for First Implementation

> **Provenance.** This document was synthesized from three independently generated drafts (vision-one, vision-two,
> vision-three) that all answered the same prompt, merged into one canonical record at teebs commit `c761a9b`. It is a
> historical record of the teebs design phase.

A music library manager successor to [beets](https://github.com/beetbox/beets). This document consolidates all research,
design, and annoyances into a single vision for the first implementation.

______________________________________________________________________

## Why teebs exists

Beets is the best music library manager available. It is also a 15-year-old project carrying deep structural debt that
compounds over time:

**The data model is flat and fragile.** 92 columns on `items`, 44 on `albums`, 33 duplicated between both tables.
"Artist" is not an entity — it's 17+ string columns that grew to 27+ after the multi-value artist work (2023-2025) added
delimiter-separated list columns alongside the originals rather than fixing the model. Genres are `\0`-delimited
strings. External IDs (`mb_albumid`, `discogs_albumid`, etc.) are baked into the schema — adding a new source requires a
migration. Columns are never removed; the schema only grows via `ALTER TABLE ADD COLUMN`. Paths are BLOBs, which makes
the DB impossible to query with standard tools. No foreign keys. One index — all text searches are full table scans.
Flex attributes are untyped (all TEXT regardless of actual type).

**Import is monolithic and destructive.** Scanning, matching, choosing, tagging, and moving files are one inseparable
interactive pipeline. A wrong match at 0.60 confidence means wrong filenames and wrong tags with no undo. Confidence is
an import gate — unmatched music is unmanaged music, which is the worst outcome for the files that need management most.
Import decisions aren't tracked. There's no queue, no batching, no "come back later." Getting it wrong means `import -L`
hacks.

**Metadata is lossy.** Original tags are overwritten. Matched metadata isn't stored separately. There's no way to see
what changed, compare sources, undo a match, or recreate original files. No audit log of any kind.

**Source files are not safe.** Beets can move files on import, destroying the source. `fetchart` modifies source
directories. There's no guarantee your original collection survives an import.

**Tag writing is opaque.** Too many tags written by default. No clear mapping between DB fields and file tags. Poor
error feedback when things don't match up. No obvious way to control what gets written.

**Genres, moods, and descriptive metadata are afterthoughts.** Almost entirely missing from core. Bolted on via
`lastgenre` and flexible attributes.

**MusicBrainz is the only real path.** The architecture assumes MB. MB is slow and not every release is there. Other
sources exist as plugins but aren't first-class.

**Plugins are inconsistent.** 78 plugins, many stale, no shared conventions. No universal `--dry-run`, no consistent
error handling. Plugin sprawl encouraged breadth over quality.

teebs fixes these by starting clean with a normalized schema, proper separation of concerns, and modern Python tooling.

______________________________________________________________________

## Design Principles

### 1. Albums are the primary unit

Tracks exist within albums. A single track is an album with one track. There are no singletons.

### 2. Copy on import, source is sacred

Import **always copies** from source to library. There is no "move on import." Source directories are read-only — teebs
never modifies, renames, or deletes anything in the source path. Library files are freely managed: tagged, renamed,
organized.

### 3. Import everything, gate nothing

Every file enters the library unconditionally. Confidence is metadata *about* metadata — stored per source, used by
merge rules, never as a gate. A 0.70 match today is stored and available; when a 0.98 match arrives tomorrow, it
supersedes without data loss.

### 4. Sources are layers, not overwrites

Each metadata source is an independent layer. File tags, MusicBrainz, Discogs, user edits — all stored separately, all
preserved. The library view is a materialized merge of these layers with clear precedence. A wrong match is a
low-confidence source entry you can ignore or delete — nothing irreversible happened. This is what enables undo,
re-match, "what changed?", and recreate-from-source.

### 5. Background fetch, foreground review

Source fetching happens in the background. Changes from sources appear in a pending changes queue. Review is separate: a
human or agent inspects pending changes and approves, rejects, or edits them. Fetch and review are decoupled.

### 6. Proper normalization

Artists are entities. Genres are entities. External IDs are a generic table. No delimiter-separated strings. No
denormalized album fields on tracks. Adding a new metadata source requires zero schema changes.

### 7. Pydantic for validation, SQLAlchemy for storage

Two separate layers. Pydantic models (`TrackInfo`, `AlbumInfo`) are the pipeline lingua franca — every stage validates
through them. ORM models are just persistence. The database is queryable with plain SQL by any tool.

### 8. Decomposed import

Scanning, matching, reviewing, and organizing are independent steps with persistent state. You can add 50 albums to a
queue, walk away, come back tomorrow.

### 9. Non-destructive by default

Operations that modify files (tag writing, renaming, moving) are explicit, separate actions — never side effects of
import or matching. The database can be rebuilt from sources at any time.

### 10. Opinionated defaults

One good way to do things. Not ten configurable ways. Fewer features, done well.

### 11. Everything is logged

Every operation is recorded: what happened, when, to what, by whom (user vs auto-match vs plugin). Import decisions are
tracked and queryable.

______________________________________________________________________

## Architecture

### Two-layer data architecture

The defining architectural feature of teebs is the separation between the **source layer** and the **merged view**:

```
                    Sources (background)
    +----------+----------+----------+----------+
    |file_tags |musicbrainz| discogs  | acoustid | ...
    +----+-----+----+-----+----+-----+----+-----+
         |          |          |          |
         v          v          v          v
    +-------------------------------------------+
    |         source_values (per-field)          |
    |  entity + field + source + value + conf   |
    +-------------------+-----------------------+
                        |
               +--------+--------+
               |  pending_changes |  (new/changed values awaiting review)
               +--------+--------+
                        |
               human / agent / auto-rules
                        |
                        v
    +-------------------------------------------+
    |          Merged view (materialized)        |
    |  albums, tracks, artists, recordings,     |
    |  works, release_groups, artist_credits,   |
    |  genres, external_ids                     |
    +-------------------------------------------+
                        |
               +--------+--------+
               |  file operations |  (explicit, opt-in)
               |  tag write-back  |
               |  rename / move   |
               +-----------------+
```

The **source layer** stores per-field, per-source metadata with confidence scores and provenance. The **merged view** is
a materialized cache computed from source data according to configurable merge rules. Queries, templates, CLI, and
plugins operate on the merged view. The source layer enables debugging, undo, re-matching, and source comparison.

In effect the merge expresses a clear precedence: user edits beat matched metadata, which beats original file tags — but
precedence is configurable per source and per field, not hard-coded.

### Layer stack

| Layer               | teebs                                     | Replaces in beets                           | Tech                    |
| ------------------- | ----------------------------------------- | ------------------------------------------- | ----------------------- |
| **Storage**         | SQLAlchemy ORM + SQLite                   | `dbcore/` (hand-rolled SQLite)              | SQLAlchemy 2.0, Alembic |
| **Validation**      | Pydantic models                           | `autotag/hooks.py` AlbumInfo/TrackInfo      | Pydantic v2             |
| **Source layer**    | Per-field source values + pending changes | Not modeled (single truth, last write wins) | New                     |
| **Import pipeline** | Decomposed state machine                  | `importer/` (monolithic generator pipeline) | Sequential              |
| **Autotagger**      | MusicBrainz (v0.1)                        | `autotag/` (LAP matching, distance scoring) | Port from beets         |
| **Tag I/O**         | `mediafile`                               | `mediafile` (extracted from beets)          | Same lib                |
| **CLI**             | `click`                                   | Custom optparse framework                   | click                   |
| **Config**          | Single YAML                               | `confuse`                                   | PyYAML or tomllib       |

### Technology choices

| Concern    | Choice                        | Rationale                                         |
| ---------- | ----------------------------- | ------------------------------------------------- |
| Language   | Python 3.12+                  | Ecosystem, beets compat, mediafile                |
| Validation | Pydantic v2                   | Fast, typed, `model_validate` from ORM            |
| ORM        | SQLAlchemy 2.0                | Mapped columns, relationship loading, mature      |
| Database   | SQLite                        | Single-file, no server                            |
| Migrations | Alembic                       | Proper up/down, never "add columns, never remove" |
| Tag I/O    | `mediafile`                   | Battle-tested, all formats                        |
| CLI        | `click`                       | Standard, simple                                  |
| Config     | YAML or TOML                  | Single file, minimal                              |
| Matching   | `jellyfish` + `lap` + `numpy` | Same proven approach as beets                     |
| Testing    | pytest                        | Standard                                          |
| Packaging  | `uv`                          | Modern                                            |

______________________________________________________________________

## Data Model

### Entity hierarchy

```
+-----------------+
|  ReleaseGroup   |  "OK Computer" as a concept
|  mb_id, title   |
+--------+--------+
         | 1:N
+--------+--------+
|     Album       |  specific edition (UK CD, US vinyl, 25th anniv.)
|  + release_group|
+--------+--------+
         | 1:N
+--------+--------+
|     Track       |  position on this album, links to a file
|  + recording_id |
+--------+--------+
         | N:1
+--------+--------+
|   Recording     |  the audio itself, shared across albums
|  mb_id, title   |
+--------+--------+
         | N:N (recording_works junction)
+--------+--------+
|     Work        |  the composition
|  mb_id, title   |
|  parent_id (self)|  movements / parts
+-----------------+
```

ReleaseGroup, Recording, and Work are nullable/optional. They cost nothing when data isn't available and are populated
for free during MusicBrainz autotagging. They enable queries like "what other editions of this album do I own?", "how
many copies of this track exist across my library?", and "show me all performances of this composition I own."

### Pydantic models (validation + pipeline)

These flow through the entire import and editing pipeline. Every stage validates through them.

```python
class ArtistRef(BaseModel):
    name: str
    sort_name: str = ""
    credited_name: str = ""
    join_phrase: str = ""  # " feat. ", " & ", etc.
    role: str = "artist"  # artist, albumartist, composer, remixer, ...
    mb_id: str | None = None

class RecordingRef(BaseModel):
    title: str = ""
    mb_id: str | None = None
    length: float | None = None

class WorkRef(BaseModel):
    title: str = ""
    mb_id: str | None = None
    parent_mb_id: str | None = None  # for movements

class ReleaseGroupRef(BaseModel):
    title: str = ""
    mb_id: str | None = None
    primary_type: str = ""
    secondary_types: list[str] = []

class TrackInfo(BaseModel):
    title: str = ""
    artists: list[ArtistRef] = []
    album: str = ""
    year: int | None = None
    track: int | None = None
    disc: int | None = None
    disctitle: str = ""
    genres: list[str] = []
    length: float | None = None
    lyrics: str = ""
    comments: str = ""
    bpm: int | None = None
    initial_key: str | None = None
    recording: RecordingRef | None = None
    works: list[WorkRef] = []
    external_ids: dict[str, str] = {}
    data_source: str = ""

class AlbumInfo(BaseModel):
    title: str = ""
    artists: list[ArtistRef] = []
    year: int | None = None
    month: int | None = None
    day: int | None = None
    original_year: int | None = None
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
    data_source: str = ""
```

ORM models accept validated data via `update_from(info)` and produce it via `to_info()`. Validation and storage are
always separate.

### Schema: Source layer (4 tables)

**`sources`** — registry of metadata sources

| Column     | Type        | Notes                                                    |
| ---------- | ----------- | -------------------------------------------------------- |
| `id`       | int PK      |                                                          |
| `name`     | text UNIQUE | file_tags, musicbrainz, discogs, user, etc.              |
| `priority` | int         | Higher wins ties. user=100, musicbrainz=50, file_tags=10 |
| `enabled`  | bool        |                                                          |

**`source_values`** — per-field, per-source metadata with confidence

| Column        | Type   | Notes                        |
| ------------- | ------ | ---------------------------- |
| `id`          | int PK |                              |
| `source_id`   | int FK |                              |
| `entity_type` | text   | "track", "album"             |
| `entity_id`   | int    | FK to tracks.id or albums.id |
| `field`       | text   | "title", "year", etc.        |
| `value`       | text   | All values stored as text    |
| `confidence`  | float  | 0.0-1.0                      |
| `fetched_at`  | float  | Unix timestamp               |

**`source_matches`** — entity-level match identifications

| Column          | Type   | Notes                         |
| --------------- | ------ | ----------------------------- |
| `id`            | int PK |                               |
| `source_id`     | int FK |                               |
| `entity_type`   | text   |                               |
| `entity_id`     | int    |                               |
| `external_type` | text   | "release", "recording", etc.  |
| `external_id`   | text   | The source's ID for the match |
| `confidence`    | float  |                               |
| `matched_at`    | float  |                               |

**`pending_changes`** — source changes awaiting review

| Column        | Type   | Notes                             |
| ------------- | ------ | --------------------------------- |
| `id`          | int PK |                                   |
| `source_id`   | int FK |                                   |
| `entity_type` | text   |                                   |
| `entity_id`   | int    |                                   |
| `field`       | text   |                                   |
| `old_value`   | text?  | Current merged view value         |
| `new_value`   | text   | Proposed value                    |
| `confidence`  | float  |                                   |
| `status`      | text   | pending, accepted, rejected       |
| `created_at`  | float  |                                   |
| `reviewed_at` | float? |                                   |
| `reviewed_by` | text?  | "user", "agent:auto-accept", etc. |

### Schema: Audit log (1 table)

**`events`** — append-only audit log backing principle 11. Every operation is a row: what happened, when, to which
entity, by whom (user, auto-match rule, agent, plugin). Import decisions, match choices, metadata edits, and file
operations are all recorded and queryable. Rows are never updated or deleted.

### Schema: Merged view (14 tables)

These are the "effective" library that queries, templates, and the CLI operate on. They are recomputed from source data
when pending changes are accepted or merge rules change.

**`tracks`** (~20 columns) — one row per audio file

| Column         | Type        | Notes                        |
| -------------- | ----------- | ---------------------------- |
| `id`           | int PK      |                              |
| `path`         | text UNIQUE | TEXT, not BLOB               |
| `album_id`     | int? FK     | NULL = unmatched loose track |
| `recording_id` | int? FK     | Links to recordings table    |
| `title`        | text        |                              |
| `track`        | int?        | Track number                 |
| `disc`         | int?        | Disc number                  |
| `disctitle`    | text        |                              |
| `lyrics`       | text        |                              |
| `comments`     | text        |                              |
| `bpm`          | int?        |                              |
| `initial_key`  | text?       |                              |
| `length`       | float?      | Duration in seconds          |
| `bitrate`      | int?        | Read-only from file          |
| `bitrate_mode` | text        | CBR/VBR/ABR                  |
| `samplerate`   | int?        |                              |
| `bitdepth`     | int?        |                              |
| `channels`     | int?        |                              |
| `format`       | text        | MP3, FLAC, etc.              |
| `encoder`      | text        |                              |
| `mtime`        | float       | File modification time       |
| `added`        | float       | Import timestamp             |

**`albums`** (~23 columns) — one row per release

| Column                                            | Type    | Notes                      |
| ------------------------------------------------- | ------- | -------------------------- |
| `id`                                              | int PK  |                            |
| `release_group_id`                                | int? FK | Links to release_groups    |
| `title`                                           | text    |                            |
| `year`, `month`, `day`                            | int?    | Release date               |
| `original_year`, `original_month`, `original_day` | int?    | Original release date      |
| `country`                                         | text    |                            |
| `label`                                           | text    |                            |
| `catalognum`                                      | text    |                            |
| `albumstatus`                                     | text    |                            |
| `albumdisambig`                                   | text    |                            |
| `comp`                                            | bool    | Compilation flag           |
| `disctotal`                                       | int?    |                            |
| `tracktotal`                                      | int?    |                            |
| `media`                                           | text    | Physical media type        |
| `script`                                          | text    |                            |
| `language`                                        | text    |                            |
| `barcode`                                         | text    |                            |
| `artpath`                                         | text?   | Cover art file path        |
| `added`                                           | float   |                            |
| `status`                                          | text    | Import state machine state |

**`release_groups`** — the album concept across editions

| Column            | Type         | Notes                   |
| ----------------- | ------------ | ----------------------- |
| `id`              | int PK       |                         |
| `title`           | text         |                         |
| `mb_id`           | text? UNIQUE |                         |
| `primary_type`    | text         | album, single, ep, etc. |
| `secondary_types` | text         | comma-separated         |

**`recordings`** — distinct audio, shared across releases

| Column   | Type         | Notes |
| -------- | ------------ | ----- |
| `id`     | int PK       |       |
| `title`  | text         |       |
| `mb_id`  | text? UNIQUE |       |
| `length` | float?       |       |

**`works`** — compositions, with movement hierarchy

| Column      | Type           | Notes               |
| ----------- | -------------- | ------------------- |
| `id`        | int PK         |                     |
| `title`     | text           |                     |
| `mb_id`     | text? UNIQUE   |                     |
| `parent_id` | int? FK (self) | For movements/parts |

**`recording_works`** — N:N junction

| Column         | Type      |
| -------------- | --------- |
| `recording_id` | int FK PK |
| `work_id`      | int FK PK |

**`artists`** — deduplicated artist entities

| Column      | Type         | Notes |
| ----------- | ------------ | ----- |
| `id`        | int PK       |       |
| `name`      | text         |       |
| `sort_name` | text         |       |
| `mb_id`     | text? UNIQUE |       |

**`artist_credits`** — who did what on which album/track

Replaces beets' `artist`, `artists`, `artist_sort`, `artists_sort`, `artist_credit`, `artists_credit`, `albumartist`,
`albumartists`, `albumartist_sort`, `albumartists_sort`, `albumartist_credit`, `albumartists_credit`, `composer`,
`composer_sort`, `lyricist`, `arranger`, `remixer` columns — all 17+ of them.

| Column          | Type    | Notes                                                                           |
| --------------- | ------- | ------------------------------------------------------------------------------- |
| `id`            | int PK  |                                                                                 |
| `artist_id`     | int FK  |                                                                                 |
| `album_id`      | int? FK |                                                                                 |
| `track_id`      | int? FK |                                                                                 |
| `role`          | text    | artist, albumartist, composer, remixer, lyricist, arranger, conductor, producer |
| `credited_name` | text    | "Phife Dawg" vs "Malik Taylor" — same artist, different credit                  |
| `join_phrase`   | text    | " feat. ", " & ", etc. for display string reconstruction                        |
| `position`      | int     | Ordering for multi-artist credits                                               |

**`genres`** + junction tables — replaces `\0`-delimited strings

| Table          | Columns                                     |
| -------------- | ------------------------------------------- |
| `genres`       | `id`, `name` (unique)                       |
| `album_genres` | `album_id` FK, `genre_id` FK (composite PK) |
| `track_genres` | `track_id` FK, `genre_id` FK (composite PK) |

**`external_ids`** — replaces 15+ `mb_*`/`discogs_*` columns

| Column     | Type    | Notes                                                        |
| ---------- | ------- | ------------------------------------------------------------ |
| `id`       | int PK  |                                                              |
| `album_id` | int? FK |                                                              |
| `track_id` | int? FK |                                                              |
| `source`   | text    | musicbrainz, discogs, acoustid, isrc, asin                   |
| `kind`     | text    | release, recording, artist, release_group, work, fingerprint |
| `value`    | text    |                                                              |

New metadata sources need zero schema changes — just new `source`/`kind` values.

**`flex_attrs`** — typed plugin extension fields

| Column     | Type    | Notes                       |
| ---------- | ------- | --------------------------- |
| `id`       | int PK  |                             |
| `album_id` | int? FK |                             |
| `track_id` | int? FK |                             |
| `key`      | text    |                             |
| `value`    | text    |                             |
| `type`     | text    | str, int, float, bool, json |

**`replaygain`** — separated loudness metadata (replaces 6 nullable float columns on beets' items)

| Column            | Type      |
| ----------------- | --------- |
| `track_id`        | int PK FK |
| `track_gain`      | float?    |
| `track_peak`      | float?    |
| `album_gain`      | float?    |
| `album_peak`      | float?    |
| `r128_track_gain` | float?    |
| `r128_album_gain` | float?    |
| `standard`        | text      |

teebs stores ReplayGain data when it exists (read from file tags or written by external tools); it does not calculate
loudness itself in v0.1.

### Schema summary

| Layer      | Table                | Purpose                                                            |
| ---------- | -------------------- | ------------------------------------------------------------------ |
| **Source** | `sources`            | Registered metadata sources                                        |
| **Source** | `source_values`      | Per-field values from each source, with confidence                 |
| **Source** | `source_matches`     | Entity-level match identifications                                 |
| **Source** | `pending_changes`    | Changes awaiting review                                            |
| **Audit**  | `events`             | Append-only log of every operation                                 |
| **Merged** | `tracks`             | Audio files (~20 cols, replaces beets' 92-col `items`)             |
| **Merged** | `albums`             | Releases (~23 cols, replaces beets' 44-col `albums`)               |
| **Merged** | `release_groups`     | Album concept across editions                                      |
| **Merged** | `recordings`         | Distinct audio, shared across releases                             |
| **Merged** | `works`              | Compositions with movement hierarchy                               |
| **Merged** | `recording_works`    | Recording-to-work links                                            |
| **Merged** | `artists`            | Deduplicated people/groups (replaces 17+ flattened string columns) |
| **Merged** | `artist_credits`     | Who did what, with display info                                    |
| **Merged** | `genres` + junctions | Normalized genre names (replaces `\0`-delimited strings)           |
| **Merged** | `external_ids`       | All external IDs, source-agnostic (replaces 15+ hardcoded columns) |
| **Merged** | `flex_attrs`         | Typed plugin extension fields (replaces untyped EAV tables)        |
| **Merged** | `replaygain`         | Loudness metadata                                                  |

19 tables total (4 source + 1 audit + 14 merged). Replaces beets' 5 tables (2 flat entity tables + 2 untyped EAV tables
\+ 1 migration tracker). Access patterns use `track.album.year` instead of denormalized copies; eager loading
(`joinedload` / `selectinload`) keeps common operations fast.

### Merge rules

Configurable priority and strategy per source, with per-field overrides:

| Strategy             | Behaviour                                                            |
| -------------------- | -------------------------------------------------------------------- |
| `priority`           | Highest priority source with a non-empty value wins. **Default.**    |
| `highest_confidence` | Source with highest confidence wins, ignoring priority.              |
| `union`              | Combine values from all sources (for set-valued fields like genres). |
| `longest`            | Longest non-empty value wins (useful for lyrics).                    |
| `newest`             | Most recently fetched value wins.                                    |

Auto-accept rules bypass the pending queue (e.g., "auto-accept MB fields where confidence > 0.95", "always auto-accept
user edits"). Auto-reject rules discard junk (e.g., "reject anything below 0.30 confidence").

______________________________________________________________________

## Import Pipeline

The monolithic beets import is decomposed into independent, resumable steps with persistent state:

```
added --> matching --> matched --> review --> accepted --> organizing --> done
                  \-> unmatched --> review
```

| State                 | What happens                                                                 | CLI command      |
| --------------------- | ---------------------------------------------------------------------------- | ---------------- |
| **added**             | Files copied to library, original tags read and stored as `file_tags` source | `teebs add`      |
| **matching**          | Querying metadata sources in background                                      | `teebs match`    |
| **matched/unmatched** | Result ready for review                                                      |                  |
| **review**            | Human or agent inspects, edits, accepts/rejects                              | `teebs review`   |
| **accepted**          | Metadata confirmed, merged view updated                                      |                  |
| **organizing**        | Writing tags to library files, renaming/moving                               | `teebs organize` |
| **done**              | In the library                                                               |                  |

Or `teebs import` for the full pipeline — the convenience shortcut for users who want the beets-like interactive flow.

Key properties:

- **The queue is a DB table** (the `status` column on albums), not in-memory. Survives across sessions.
- **Each step independently runnable and resumable.** Do 10 of 50 reviews, quit, come back later.
- **Matching can be slow.** It runs in the background and resumes across sessions.
- **Auto-accept threshold** for high-confidence matches. Default: nothing auto-accepts (safe).
- **Sequential execution.** Threaded pipeline is a later optimization.

### Import lifecycle example

```
1. teebs add /path/to/new/music
   - Files copied to library directory
   - Track/album rows created in merged view (path, audio properties)
   - file_tags source values written for every tag found in files
   - Merged view computed from file_tags (only source available)
   - Albums enter queue with status "added"

2. teebs match (or background daemon)
   - AcoustID fingerprint -> recording match (confidence 0.82)
   - Recording -> MB release match (confidence 0.91)
   - source_matches and source_values rows created
   - Per auto_accept rules: confidence 0.91 < 0.95 threshold -> pending_changes created

3. teebs review
   - "MB says year=1997 (conf 0.91), file says 2003. Accept MB?" -> User accepts
   - "Discogs says genre=Britpop, MB says genre=Alternative Rock. Accept?" -> Both accepted (union strategy)
   - Merged view updated, pending_change status=accepted

4. teebs organize
   - Compute effective metadata from merged view
   - Write configured tags to library files
   - Rename/move files per path template
   - Album status -> done
```

______________________________________________________________________

## Autotagger

The autotagger is the hardest part to replicate. The plan is to **port beets' algorithms** (~565 lines of logic) into a
standalone `teebs.autotag` module, decoupled from beets internals.

### What we port

| Component                                            | Lines | Deps                 |
| ---------------------------------------------------- | ----- | -------------------- |
| `Distance` class (weighted scoring framework)        | 250   | none                 |
| `string_dist()` (Levenshtein + semantic adjustments) | 55    | jellyfish, unidecode |
| `track_distance()` (7 dimensions)                    | 45    | above                |
| `album_distance()` (11 dimensions + per-track)       | 110   | above                |
| `assign_items()` (LAP solver)                        | 30    | lap, numpy           |
| `_recommendation()` (threshold logic)                | 55    | none                 |
| Default weights                                      | 20    | none                 |

### Key design decisions

- **Weights as a dataclass, not config.** Replace all beets `config["match"]` reads with a `MatchConfig` object. Default
  to beets' proven defaults.
- **Candidate source as a callable.** `tag_album()` accepts an iterable of candidates. The caller fetches them. This
  decouples matching from source plugins.
- **`display_artist()` bridges normalized artists.** The distance functions need flat strings; the helper reconstructs
  them from `list[ArtistRef]` using join phrases. The same helper serves path templates and display anywhere a
  denormalized artist string is needed.

```python
def tag_album(
    items: Sequence[TrackInfo],
    candidates: Iterable[AlbumInfo],
    weights: MatchConfig = DEFAULT_CONFIG,
) -> Proposal: ...

class MetadataSource(Protocol):
    def search_albums(self, artist: str, album: str, va: bool) -> Iterator[AlbumInfo]: ...
    def search_tracks(self, artist: str, title: str) -> Iterator[TrackInfo]: ...
    def album_by_id(self, id: str) -> AlbumInfo | None: ...
```

### Module structure

```
teebs/autotag/
    __init__.py     # public API: tag_album, tag_item, Recommendation
    distance.py     # Distance class, string_dist, track_distance, album_distance
    match.py        # assign_items (LAP), recommendation, tag_album
    weights.py      # default weights, thresholds, VA_ARTISTS
```

______________________________________________________________________

## Tag Writing

Teebs maintains a clear, explicit mapping between DB fields and file tags.

- **Whitelist, not blacklist.** Only write tags that are explicitly configured.
- **The mapping is documented and queryable.** "Which DB field writes to which tag in which format?"
- **`--dry-run` on every write operation, always.**
- **Clear error messages** when a tag can't be written (unsupported format, etc.).
- **Tag writing is a separate step** (`teebs organize`), never a side effect of import or matching.

______________________________________________________________________

## Path Templates

The default layout is `$albumartist/$album/$track $title`, rendered from the merged view. Normalized artists need a
denormalized display string for paths — that's `display_artist()`, which reconstructs credit order and join phrases from
`artist_credits`. One good default layout; how much template power beyond `$field` substitution is actually needed is an
open question.

______________________________________________________________________

## What to Build First (v0.1)

### Must have

| Component                                     | Effort | Notes                                                      |
| --------------------------------------------- | ------ | ---------------------------------------------------------- |
| SQLAlchemy ORM + all tables                   | Medium | Alembic migrations from day one                            |
| Pydantic TrackInfo/AlbumInfo                  | Low    | Already designed                                           |
| File tag reading via `mediafile`              | Low    | Read-only initially                                        |
| `teebs add` — scan, copy, store original tags | Medium | Foundation. Creates file_tags source values.               |
| `teebs list` — query and display library      | Medium | Simple `field:value` matching on merged view               |
| `display_artist()` helper                     | Low    | Denormalized display string from normalized artist_credits |
| CLI framework (`click`)                       | Low    | `add`, `list`, `info`                                      |
| Config (single YAML)                          | Low    | Library path, path template, merge rules                   |
| Source layer tables + basic merge logic       | Medium | Priority-based merge for scalar fields                     |

### Should have

| Component                                  | Effort | Notes                                      |
| ------------------------------------------ | ------ | ------------------------------------------ |
| `teebs match` — MusicBrainz lookup + LAP   | High   | **Hardest part.** Port beets' autotagger.  |
| `teebs review` — interactive match review  | Medium | Terminal UI for accept/reject/edit         |
| `teebs organize` — write tags + move files | Medium | Path templates, tag whitelist              |
| Pending changes queue + review workflow    | Medium | Accept/reject/auto-accept rules            |
| Event/audit log                            | Low    | Append-only `events` table, log everything |

### Defer

| Component                                   | Why                                                    |
| ------------------------------------------- | ------------------------------------------------------ |
| Discogs, Spotify, RED, Deezer sources       | MusicBrainz first. Architecture supports adding later. |
| Plugin system                               | Build core first. No plugins in v0.1.                  |
| Web UI / API                                | CLI only                                               |
| Media server integration                    | Out of scope                                           |
| Transcode / convert                         | Out of scope                                           |
| Threaded import                             | Sequential is fine                                     |
| ReplayGain calculation                      | Store if present, don't calculate                      |
| Smart playlists                             | Later                                                  |
| Fetchart / embedart                         | Copy art from source if present. No fetching.          |
| Duplicate/variant management                | Design later                                           |
| Album relationships (remix of, remaster of) | Design later                                           |
| Listening history / play counts             | Design later                                           |
| Album art table (multiple images)           | Single `artpath` for v0.1                              |
| Beets DB migration tool                     | v0.2                                                   |
| Background source re-polling                | Architecture supports it; build later                  |
| AI agent review of pending changes          | Design the contract; build later                       |

______________________________________________________________________

## Key Differences from Beets

| Aspect             | beets                                    | teebs                                                        |
| ------------------ | ---------------------------------------- | ------------------------------------------------------------ |
| Schema             | 2 tables, 136 columns                    | 14 merged-view tables, ~100 columns total, plus source layer |
| Source tracking    | Not modeled (single truth)               | Per-field, per-source with confidence                        |
| Artists            | 17+ flattened string columns             | Normalized `artists` + `artist_credits`                      |
| External IDs       | 15+ hardcoded `mb_*`/`discogs_*` columns | Generic `external_ids` table                                 |
| Genres             | `\0`-delimited strings                   | Junction tables                                              |
| Multi-value fields | Delimiter-separated TEXT columns         | Proper relationships                                         |
| Paths              | BLOB                                     | TEXT                                                         |
| Flex attrs         | Untyped (all TEXT)                       | Typed via `type` column                                      |
| Validation         | Mixed into ORM                           | Separate Pydantic layer                                      |
| Migrations         | ALTER TABLE ADD COLUMN, never remove     | Alembic                                                      |
| Import             | Monolithic, destructive, gatekeeping     | Decomposed, non-destructive, unconditional                   |
| Unmatched files    | Rejected or imported bare                | Always imported, always managed                              |
| Confidence         | Import gate                              | Stored metadata, used by merge rules                         |
| File modification  | Side effect of import                    | Explicit, separate action                                    |
| Source files       | May be moved/modified                    | Never touched                                                |
| Tag writing        | Writes many tags, hard to control        | Clear minimal whitelist, full control, `--dry-run`           |
| Review             | Interactive terminal, one-shot           | Async, resumable, human or agent                             |
| Singletons         | Special second-class concept             | Just an album with one track                                 |
| Foreign keys       | None enforced                            | Real constraints                                             |
| Indices            | One (`album_id`)                         | On all common query fields                                   |

______________________________________________________________________

## Decisions Made (Formerly Open Questions)

| Question                    | Decision                                                                  | Rationale                                                                         |
| --------------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Singletons?                 | No. An album with one track.                                              | Singletons are a weird second-class concept in beets. One model.                  |
| Source files modified?      | Never. Copy on import. Source is read-only.                               | Core tenet. Beets' `move` and `fetchart` source-dir writes are a category of bug. |
| Layered metadata?           | Yes, from day one — the source layer + merged view.                       | This is what makes "preserve everything" real. Retrofitting is hard.              |
| Confidence as import gate?  | No. Confidence is stored metadata used by merge rules.                    | Unmatched music is unmanaged music — the worst outcome.                           |
| Work/recording abstraction? | Modeled as nullable entities (release_groups, recordings, works).         | They cost nothing when absent and are populated for free during MB autotagging.   |
| Album art?                  | `artpath` on albums for v0.1. Multiple-attachment table later.            | Keep v0.1 simple. The annoyance is real but not blocking.                         |
| Tag writing?                | Whitelist. Explicit mapping. `--dry-run` always available.                | Beets writes too many tags with no visibility.                                    |
| Path templates?             | `$albumartist/$album/$track $title` with `display_artist()` helper.       | Normalized artists need a denormalized display string for paths.                  |
| Metadata sources?           | MusicBrainz only for v0.1. Architecture supports adding more.             | `sources` and `external_ids` tables are source-agnostic by design.                |
| Plugin system?              | None for v0.1. Build what's needed directly.                              | Beets' plugin sprawl is a problem. Fewer things, done well.                       |
| Import moves files?         | No. `teebs add` copies; `teebs organize` renames within the library only. | Non-destructive by default.                                                       |

______________________________________________________________________

## Considered and Rejected

Alternatives that came up during the design phase and were deliberately not taken:

**Defer layered metadata to v0.2.** One line of thinking: ship v0.1 with a flat, single-truth schema ("the design is
clear, implementation can wait") and add the source layer in a later release. Rejected. The source layer is the defining
architectural feature — it is what makes "preserve everything", undo, re-matching, and source comparison real.
Retrofitting provenance onto a flat schema is hard: every write path must be rewritten, and data imported before the
retrofit carries no provenance and can never get it back. Build it from day one, even if the v0.1 merge logic is just
priority-based scalar merging.

**Keep the work/recording hierarchy flat for v0.1.** Capture the MB hierarchy via `external_ids` rows with `kind="work"`
/ `kind="recording"` and model the entities later if needed. Rejected in favour of nullable ReleaseGroup/Recording/Work
entities: they cost nothing when data isn't available, they're populated for free during MB autotagging, and
`external_ids` still carries the raw IDs either way.

**A minimal plugin system (event bus + entry points) in v0.1.** Tempting because it's small, but it front-loads API
stability promises before the core exists. No plugins in v0.1; build capabilities directly and extract an extension
surface once the core is stable.

**Move-on-import as an option.** Beets offers copy or move. teebs only copies. A "move" mode reintroduces the entire
category of source-destruction bugs for the sake of disk space; users who need to reclaim space can delete the source
themselves after verifying the import.

______________________________________________________________________

## Open Questions (Tracked, Not Blocking v0.1)

- **Structured field merging.** Artists and genres are relational in the merged view but serialized in `source_values`.
  The merge logic for these is necessarily more complex than for scalar fields. Needs a clear strategy for reconciling a
  raw tag string "DJ Koze feat. Apparat" and a MB artist credit JSON array into `ArtistCreditORM` rows.
- **Loose track representation.** No singleton concept — but is an unmatched loose track a row with `album_id = NULL`,
  or does `add` create a synthetic one-track album immediately? Start with NULL for unmatched tracks and see how it
  feels; organize into a one-track album once matched.
- **Performance with JOINs + source layer volume.** A 10k track library with 3 sources is ~200k-600k `source_values`
  rows. SQLite handles this fine, but merge recomputation must be incremental, not full-table. Verify eager loading
  keeps the normalized schema fast on 10k+ album libraries. Benchmark early.
- **Pending change grouping.** When MB provides 15 new field values for an album, should those be 15 individual pending
  changes or one grouped change? Grouping is better UX.
- **`display_artist()` concatenation rules.** `join_phrase` and `position` cover reconstruction, but the rules need
  pinning down: which roles appear in path templates, fallback when join phrases are missing, ordering across roles.
- **Path template syntax.** Reuse beets' `$field` / `%func{}` syntax, or simplify? How much template power is actually
  needed?
- **How opinionated on file layout?** One layout or a small set of choices? Start with one good default.
- **Config surface.** What's configurable? Library path, path template, merge rules, auto-accept threshold, tag write
  whitelist — what else? Keep it minimal.
- **Source fetch scheduling.** How often to re-check sources? Per-source config? Event-driven?
- **Beets migration path.** Read beets' SQLite DB and import into the teebs schema. How much of the 92-column schema
  maps cleanly to the normalized model? Not blocking v0.1 but needed for adoption.
- **Tag writing policy.** Which tags get written to files vs stay DB-only? Define a clear, minimal default set.
- **RED/Gazelle as a source.** The tracker has artist roles, tags, edition metadata. No track-level data (only
  filenames+sizes). MusicBrainz IDs often parseable from torrent descriptions. Worth building as a source plugin after
  v0.1.
