# teebs implementation plan (simplified)

> Carried over verbatim from teebs@6e2f5b4 (2026-04-01). Written twenty minutes after [plan.md](plan.md) and before any
> code: the 8 phases collapsed to 3, replaygain and flex_attrs dropped, the source layer and MB entities deferred to the
> phase where a second source exists. This is the plan that was actually built, and the version
> [assessment.md](assessment.md)'s pushback predicted. leeks' slicing rules in
> [project-principles](../../design/project-principles.md) are distilled from this simplification.

Claude's plan for building teebs, based on Fredrik's design notes.

## Where we are

A skeleton: click CLI with a `version` command. No data model, no storage, no import logic.

## What to build, in what order

Three phases to a useful tool. Each phase produces something runnable.

______________________________________________________________________

### Phase 1: Data model + `teebs add`

Get music into a database.

**Tables (merged view only, no source layer yet):**

- `albums` -- one row per release
- `tracks` -- one row per audio file, FK to album
- `artists` -- deduplicated artist entities
- `artist_credits` -- who did what on which album/track (role, position, join phrase)
- `genres` + `album_genres` + `track_genres` -- normalized genre junction tables
- `external_ids` -- generic source/kind/value (MB, Discogs, ISRC, etc.)

No release_groups, recordings, or works yet. Those arrive with MB matching.

**What gets built:**

01. SQLAlchemy ORM models for the 7 tables above
02. Pydantic models: TrackInfo, AlbumInfo, ArtistRef
03. `to_info()` / `update_from(info)` on ORM models
04. `display_artist()` helper
05. Alembic setup with initial migration
06. Database class (engine/session lifecycle)
07. Tag reading via `mediafile`
08. Directory scanning: walk a path, group files into albums by directory
09. Copy files to library directory
10. `teebs add /path/to/music` CLI command
11. Config: library path (single YAML or TOML file)
12. Tests

**Key decisions:**

- Source files are copied, never modified
- All files accepted unconditionally
- Albums grouped by directory
- No source layer -- file tags write directly to merged view tables
- Alembic from day one so we can evolve the schema

______________________________________________________________________

### Phase 2: `teebs list` + `teebs info`

Make the library queryable.

**What gets built:**

1. `teebs list` -- show albums and tracks
2. `teebs info` -- detailed view of an album or track
3. Simple query: `field:value` matching

______________________________________________________________________

### Phase 3: MusicBrainz matching + source layer

This is when multiple sources exist, so this is when the source layer earns its keep.

**New tables:**

- `sources` -- registry of metadata sources
- `source_values` -- per-field, per-source values with confidence
- `source_matches` -- entity-level match identifications
- `pending_changes` -- changes awaiting review
- `release_groups`, `recordings`, `works`, `recording_works` -- MB entities

**What gets built:**

1. Alembic migration adding the new tables
2. Port beets' autotagger (Distance, string_dist, LAP solver, etc.)
3. MusicBrainz API client
4. `teebs match` CLI command
5. Basic merge logic (priority-based for scalars, union for genres)
6. `teebs review` -- accept/reject pending changes
7. Auto-accept rules

______________________________________________________________________

### Later

Not planned in detail. Build when needed.

- Tag writing + file organization (`teebs organize`)
- `teebs import` (full pipeline: add + match + review + organize)
- Discogs, Last.fm, other sources
- Background source re-polling
- Path templates
- Plugin system
- Beets DB migration tool

______________________________________________________________________

## Open questions

- **Structured field merging.** How to reconcile "DJ Koze feat. Apparat" (file tag) with MB artist credit JSON into
  ArtistCreditORM rows. Punt for now: highest-priority source wins for artists.
- **Path template syntax.** Decide when we build `teebs organize`.
- **Pending change grouping.** One grouped change per entity or one per field?
- **Album art.** Single `artpath` column for now.

## Principles

1. **Opinionated.** One good way.
2. **Non-destructive.** Never modify source files.
3. **Import everything.** No gatekeeping.
4. **Plain SQL.** No nested JSON, no application-specific encoding.
5. **Simple first.** Build the v0 schema, evolve with Alembic.
