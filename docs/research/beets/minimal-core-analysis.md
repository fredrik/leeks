# Beets Minimal Core — Blind Analysis

> **Method:** Static codebase exploration of `/workspace/beets/` (~17,900 lines of core code). No runtime testing, no
> user interviews, no usage telemetry. Conclusions drawn from reading source only.

______________________________________________________________________

## Inputs Used

- `pyproject.toml` — entry points, dependencies, project metadata
- `beets/__init__.py` — global config object, version, library paths
- `beets/library/` — `models.py` (Item/Album), `library.py` (Library DB handle)
- `beets/dbcore/` — `db.py`, `query.py`, `types.py` (SQLite abstraction, query system, type system)
- `beets/importer/` — `session.py`, `stages.py`, `tasks.py` (import pipeline)
- `beets/autotag/` — `match.py`, `distance.py`, `hooks.py` (autotagging, LAP matching, scoring)
- `beets/plugins.py` — plugin base class, event bus, plugin loading
- `beets/metadata_plugins.py` — metadata source plugin interface
- `beets/ui/__init__.py` — CLI framework, subcommand parser
- `beets/ui/commands/` — built-in CLI commands
- `beets/util/` — path ops, template engine, pipeline runner, config helpers
- `beets/config_default.yaml` — default configuration
- `beetsplug/` — directory listing (50+ plugins, not read in depth)

______________________________________________________________________

## Architecture (6 Layers)

### 1. Database Layer (`beets/dbcore/`)

Lightweight SQLite abstraction. No ORM.

- **Fixed + flexible schema** — core fields are table columns; plugins store arbitrary key-value pairs in separate
  `_attributes` tables
- **Query system** — `FieldQuery`, `AndQuery`, `OrQuery`, type-aware comparisons, smart artist sort
- **Type system** — `STRING`, `INTEGER`, `DATE`, `PathType`, `DurationType`, `MusicalKey`, etc. Handles serialization
  to/from SQLite
- **Migrations** — version tracking with automatic schema upgrades

### 2. Data Models (`beets/library/`)

- **`Item`** — single track. ~60+ fixed fields: path, title, artist, album, track, bitrate, format, MusicBrainz IDs,
  Discogs IDs, acoustic fingerprint, etc.
- **`Album`** — groups Items via `album_id` FK. Holds album-level metadata (albumartist, year, artpath, disctotal).
- **`Library`** — database handle extending `dbcore.Database`. Methods: `add()`, `add_album()`, `items(query)`,
  `albums(query)`, `remove()`. Default path: `~/.config/beets/library.db`.

Both Item and Album extend `LibModel` → `dbcore.Model`, which provides template evaluation, flexible attribute access,
and change notification via the plugin event bus.

### 3. Import Pipeline (`beets/importer/`)

A staged generator pipeline (can run threaded):

```
read_tasks → group_albums → lookup_candidates → user_query → plugin_stages → manipulate_files → add to DB
```

- **`ImportSession`** — manages overall workflow. Abstract base; UI must implement `choose_match()`,
  `resolve_duplicate()`, `choose_item()`.
- **`ImportTask`** — carries state through pipeline stages (paths, items, match candidates, chosen action).
- **Actions:** `SKIP`, `ASIS`, `APPLY`, `MANUAL`.
- **Variants:** `SingletonImportTask`, `ArchiveImportTask`.

### 4. Autotagger (`beets/autotag/`)

The core "magic" of beets.

- **`tag_album()`** — fetches candidates from all metadata sources, then solves a **linear assignment problem** (LAP) to
  optimally match local tracks to remote tracklists.
- **`tag_item()`** — simpler single-track matching.
- **Distance scoring** (`distance.py`) — string similarity on artist/title/album, penalties for missing/extra tracks,
  various-artist handling.
- **Data structures** (`hooks.py`) — `AlbumInfo`, `TrackInfo` (metadata from sources), `AlbumMatch`, `TrackMatch`
  (candidates with distance scores).

### 5. Plugin System (`beets/plugins.py`)

- **`BeetsPlugin`** base class with hooks:
  - `commands()` — register CLI subcommands
  - `get_import_stages()` / `get_early_import_stages()` — inject into import pipeline
  - `register_listener(event, func)` — subscribe to events
- **Event bus:** `plugins.send('album_imported', album=album)` — 30+ event types covering the full lifecycle.
- **Extension points:** template functions, custom queries, custom field types, metadata sources.
- **Loading:** reads `plugins` list from config, imports from `beetsplug` namespace.
- **50+ bundled plugins:** musicbrainz, fetchart, replaygain, web, convert, lastgenre, discogs, etc.

### 6. CLI (`beets/ui/`)

- Custom `SubcommandsOptionParser` built on `optparse`.
- Commands in `beets/ui/commands/`: import, list, modify, move, remove, update, write, config.
- Entry point: `beets.ui:main()` (registered in pyproject.toml).
- Error handling wrapper catches `UserError`, `ConfigError`, `InvalidQueryError`, `DBAccessError`.

### Supporting Utilities (`beets/util/`)

- **`functemplate.py`** — template evaluation engine for path formats (`$artist/$album/$title`)
- **`pipeline.py`** — task pipeline execution (sequential or parallel/threaded)
- **`artresizer.py`** — image resizing for artwork
- **`id_extractors.py`** — extract MusicBrainz/Discogs IDs from metadata
- **`diff.py`** — show metadata changes to user
- **Config** — uses `confuse` library; YAML-based with defaults in `config_default.yaml`

______________________________________________________________________

## Minimal Clone: Component Priority

| Priority   | Component           | Effort | Notes                                                            |
| ---------- | ------------------- | ------ | ---------------------------------------------------------------- |
| **Must**   | SQLite library/DB   | Medium | Simplify dbcore; skip flexible attrs initially                   |
| **Must**   | Item + Album models | Medium | Reduce to ~15-20 essential fields                                |
| **Must**   | Query parser        | Medium | Start with simple `field:value` matching                         |
| **Must**   | File tag reading    | Low    | Use `mediafile` (beets' own extracted lib) or `mutagen` directly |
| **Must**   | CLI framework       | Low    | Use `click` instead of custom optparse                           |
| **Should** | Autotagger          | High   | MusicBrainz API + LAP matching — hardest part                    |
| **Should** | File organization   | Medium | Move/copy + path templates (`$artist/$album/$track`)             |
| **Should** | Plugin system       | Medium | Simple event bus + entry points                                  |
| **Nice**   | Config system       | Low    | Single YAML file; skip `confuse`                                 |
| **Skip**   | 50+ bundled plugins | —      | Build only what you need                                         |

______________________________________________________________________

## Simplification Opportunities

1. **Replace dbcore with an ORM** (SQLAlchemy or Peewee) — beets rolls its own; a clone doesn't need to.
1. **Use `click`** instead of the custom optparse subcommand parser.
1. **Hardcode MusicBrainz** as the only metadata source — skip the pluggable `MetadataSourcePlugin` interface.
1. **Drop flexible attributes** initially — they add significant complexity for plugin extensibility that a simple
   system doesn't need.
1. **Sequential import** — skip the threaded pipeline; a simple loop works fine for most libraries.
1. **Use `mediafile`** (extracted from beets itself) for reading/writing audio file tags.

______________________________________________________________________

## What Makes Beets Hard to Replicate

The **autotagger** is the core differentiator. Specifically:

- The **LAP (linear assignment problem)** solver that optimally maps local tracks to remote tracklist positions.
- The **distance heuristics** — string similarity, penalty weights, various-artist detection, missing/extra track
  handling.
- **Candidate ranking** — combining scores from multiple metadata sources into a recommendation.

Everything else (DB, CLI, file management, config) is standard application plumbing.
