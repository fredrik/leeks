# teebs implementation plan

> Carried over verbatim from teebs@b85f579 (2026-04-01). The closing artifact of the teebs design phase: the 8-phase
> plan for building the design in [vision.md](vision.md) and [data-model.md](data-model.md). Companion to
> [assessment.md](assessment.md).

Claude's plan for building teebs, based on Fredrik's design notes.

## Where we are

A skeleton: click CLI with a `version` command. No data model, no storage, no import logic. The research docs contain a
fully designed data model (v2) and architecture. The gap is entirely implementation.

## What to build, in what order

The plan is divided into phases. Each phase produces something runnable and testable. No phase depends on unfinished
work from a later phase.

______________________________________________________________________

### Phase 1: Data model + storage

The foundation everything else builds on.

**Deliverables:**

1. SQLAlchemy ORM models for the merged view (14 tables)
1. SQLAlchemy ORM models for the source layer (4 tables)
1. Pydantic models for validation (TrackInfo, AlbumInfo, ArtistRef, etc.)
1. `to_info()` and `update_from(info)` on ORM models
1. Alembic setup with initial migration
1. A `Database` class that manages the engine/session lifecycle
1. Tests: round-trip ORM \<-> Pydantic, migration up/down

**Key decisions (from Fredrik's notes):**

- SQLite, single file
- Pydantic validates, SQLAlchemy persists. They don't inherit from each other.
- All paths are TEXT, not BLOB
- Proper FKs and indices from day one
- `display_artist()` helper: reconstruct "DJ Koze feat. Apparat" from normalized artist_credits

**What I won't do yet:**

- Merge logic (Phase 3)
- Anything that reads actual music files

**File layout:**

```
src/teebs/
  db/
    __init__.py        # Database class (engine, session, init)
    models.py          # all ORM models
    migrations/        # alembic
  models.py            # Pydantic models (TrackInfo, AlbumInfo, etc.)
```

______________________________________________________________________

### Phase 2: File scanning + `teebs add`

Read music files, copy them into the library, extract tags.

**Deliverables:**

1. Tag reading via `mediafile` -- extract all standard tags into TrackInfo/AlbumInfo
1. Directory scanning: walk a path, group files into albums (by directory)
1. Copy files to library directory (configurable root)
1. Create Track/Album rows in merged view
1. Write file_tags source values for every extracted tag
1. `teebs add /path/to/music` CLI command
1. Tests with fixture audio files (short silent FLACs)

**Key decisions:**

- Source files are copied, never modified
- All files accepted unconditionally
- Albums grouped by directory (simple heuristic for v0.1)
- The `file_tags` source is auto-created on first run
- Merged view is populated directly from file_tags at this stage (no merge logic yet -- file_tags is the only source)

**File layout:**

```
src/teebs/
  scan.py              # directory walking, grouping, tag reading
  add.py               # copy + create DB rows + source values
```

______________________________________________________________________

### Phase 3: Source layer merge logic

The core architectural innovation. Makes the source layer actually work.

**Deliverables:**

1. Merge engine: given an entity, read all source_values, apply merge rules, write to merged view tables
1. Default merge rules (priority-based for scalars, union for genres)
1. `display_artist()` helper for reconstructing artist display strings
1. Config file support (YAML or TOML) for merge rules + library path
1. Tests: conflicting sources, priority resolution, confidence-based resolution, union merge for genres

**Key decisions:**

- Merge is incremental: recompute one entity at a time, not the whole DB
- Start with `priority` and `union` strategies. Add `highest_confidence`, `longest`, `newest` as needed.
- Structured field merging (artists, genres) is the hard part. For v0.1:
  - Scalar fields: straightforward priority merge
  - Genres: union from all sources
  - Artists: highest-priority source wins entirely (don't try to merge individual artist credits across sources yet)

**File layout:**

```
src/teebs/
  merge.py             # merge engine
  config.py            # config loading (library path, merge rules)
```

______________________________________________________________________

### Phase 4: `teebs list` + `teebs info`

Make the library queryable from the CLI.

**Deliverables:**

1. `teebs list` -- query and display albums/tracks
1. `teebs info <album|track>` -- show detailed info including source layer data
1. Simple query language: `field:value` matching on merged view
1. Show source disagreements in `info` output

**File layout:**

```
src/teebs/
  query.py             # query parsing + execution
  fmt.py               # display formatting
```

______________________________________________________________________

### Phase 5: MusicBrainz matching

The hardest phase. Port beets' autotagger.

**Deliverables:**

1. Port `Distance` class (weighted scoring framework)
1. Port `string_dist()` (Levenshtein + semantic adjustments)
1. Port `track_distance()` and `album_distance()`
1. Port `assign_items()` (LAP solver for track-to-track assignment)
1. Port `_recommendation()` (threshold logic)
1. MusicBrainz API client (search + lookup, rate-limited)
1. `MetadataSource` protocol + MB implementation
1. `teebs match` CLI command: run MB lookup against unmatched albums, create source_values and source_matches, generate
   pending_changes
1. Tests with fixture MB responses

**Key decisions:**

- Port beets' proven algorithms, don't reinvent
- Candidate source is a callable (decoupled from MB specifics)
- `MatchConfig` dataclass instead of reading from config dict
- Rate limiting: respect MB's 1 req/sec
- Write source_values for every MB-provided field
- Write source_matches for entity-level identification
- Create pending_changes unless auto-accept rules fire

**File layout:**

```
src/teebs/
  autotag/
    __init__.py        # public API: tag_album, Recommendation
    distance.py        # Distance, string_dist, track/album_distance
    match.py           # assign_items, recommendation, tag_album
    weights.py         # defaults, thresholds, VA_ARTISTS
  sources/
    __init__.py        # MetadataSource protocol
    musicbrainz.py     # MB API client + source implementation
```

______________________________________________________________________

### Phase 6: Review + pending changes workflow

**Deliverables:**

1. `teebs review` -- interactive TUI for pending changes
1. Accept / reject / edit individual changes
1. Bulk accept/reject with filters
1. Auto-accept and auto-reject rules from config
1. On accept: trigger merge for affected entity

______________________________________________________________________

### Phase 7: Tag writing + file organization

**Deliverables:**

1. Tag writing via `mediafile` -- write configured fields back to library files
1. File renaming via path templates
1. `teebs organize` CLI command
1. `--dry-run` on every write operation
1. Tag mapping documentation (which DB field -> which file tag)

______________________________________________________________________

### Phase 8: `teebs import` (full pipeline)

**Deliverables:**

1. `teebs import /path` = add + match + review + organize in sequence
1. Album status state machine in DB (added -> matching -> matched -> review -> accepted -> organizing -> done)
1. Resumable: quit and restart where you left off

______________________________________________________________________

## Open questions (not blocking Phase 1)

These are explicitly deferred per Fredrik's notes. Tracked here so they don't get lost.

- **Structured field merging across sources.** The hard case: reconciling "DJ Koze feat. Apparat" (file tag string) with
  a MB artist credit JSON array into normalized ArtistCreditORM rows. Phase 3 punts by using
  highest-priority-source-wins for artists.
- **Path template syntax.** Reuse beets' `$field/%func{}` or simplify?
- **Pending change grouping.** 15 field changes from MB for one album: 15 individual changes or one grouped change?
  Grouping is better UX.
- **Source fetch scheduling.** How often to re-poll MB/Discogs. Not needed until background fetching is built.
- **Flexible attributes.** The flex_attrs table exists but the policy for when to use it vs. adding a real column is
  undefined.
- **Album art.** Single `artpath` for now. Multiple images table later.
- **Beets DB migration tool.** Needed for adoption but explicitly deferred.

## Principles I'll follow

From Fredrik's notes, distilled:

1. **Opinionated.** One good way, not ten configurable ways.
1. **Non-destructive.** Never modify source files. DB operations are reversible.
1. **Import everything.** No gatekeeping. Confidence is metadata, not a gate.
1. **Sources are layers.** All sources preserved independently.
1. **Plain SQL.** No nested JSON, no application-specific encoding in the DB.
1. **Test early.** Every phase has tests.
1. **Sequential.** Build the simple version first. Optimize later.
