# Slice 1: Library core — `leek add` (detail)

The implementation map for [the high-level plan](2026-06-11-slice-1-library-core.md). Same scope, same punts; this pass
names modules, tables, and tests.

## Modules

| Path                   | Holds                                                                  |
| ---------------------- | ---------------------------------------------------------------------- |
| `src/leeks/models.py`  | Pydantic pipeline models: `AlbumInfo`, `TrackInfo`                     |
| `src/leeks/orm.py`     | SQLAlchemy ORM models, persistence only                                |
| `src/leeks/db.py`      | Engine/session factory; library root and database location             |
| `src/leeks/tags.py`    | mediafile reading: claims → pipeline models, measurements → file facts |
| `src/leeks/detect.py`  | Single-album validation                                                |
| `src/leeks/library.py` | The add pipeline: source_values, identity merge, copy-on-import        |
| `src/leeks/cli.py`     | Gains the `add` command                                                |
| `migrations/`          | Alembic environment and migration 0001                                 |

The library root is resolved in one place (`db.py`): `$LEEKS_ROOT` if set, else `~/Music/leeks`. The database lives at
`<root>/leeks.db`; copied audio under `<root>/album-<id>/`.

## Schema (migration 0001)

Merged view — slimmed to what file tags can populate, per ADR 0006:

- `albums`: id, title, year (nullable), added. Album-level claims only; no artist columns, no track data.
- `tracks`: id, album_id (FK, NOT NULL — singletons are excluded), title, track (nullable), added.
- `files`: id, track_id (FK, NOT NULL), path (unique, under the root), source_path (unique — the re-add punt keys on
  it), plus measurements per ADR 0007: format, bitrate, samplerate, channels, duration, size, sha256, mtime, added.
- `artists`: id, name (unique). Raw credit strings, whole and unparsed, per the punt.
- `artist_credits`: id, artist_id (FK), album_id (nullable FK), track_id (nullable FK), role (`albumartist` | `artist`),
  position. Exactly one of album_id/track_id set (CHECK). Track credits are written only when a track's artist tag
  differs from the album's. `join_phrase` and `credited_name` wait for MusicBrainz.
- `genres`: id, name (unique); `album_genres`: album_id + genre_id (composite PK). Track-level genres wait for a source
  that provides them; the corpus tags genre on albums.

Source layer — the shape without the machinery:

- `sources`: id, name (unique). Seeded with `file_tags` by the migration. Priority arrives with the second source.
- `source_values`: id, source_id (FK), entity_type (`album` | `track`), entity_id, field, value (text), added. Unique on
  (source_id, entity_type, entity_id, field). Confidence arrives with matching.

tracktotal is an album-level claim (`source_values` field on the album); whether it earns a merged column is decided
when something reads it — the claim is recorded either way.

## Pipeline models

Slice-sized, grown later as sources demand:

- `TrackInfo`: title, artist (raw string, optional — present only when it overrides the album artist), track (optional
  positive int).
- `AlbumInfo`: title, artist (raw string), year (optional, bounded), genre (optional), tracktotal (optional), tracks:
  `list[TrackInfo]`.

Measurements never ride on these models (ADR 0007). `tags.py` returns them separately as a per-file facts record (a
small frozen dataclass) consumed only by `library.py` when writing file rows.

## The add pipeline

`leek add <dir>` runs:

1. **Detect** (`detect.py`): the directory must contain at least one readable audio file, all audio directly in the
   directory (audio in subdirectories → "looks like more than one album, try `leek import`"), and at most one distinct
   non-empty album tag across files (two album tags → refusal naming both). Returns the parsed per-file tags so the
   pipeline reads each file once.
2. **Assemble** (`tags.py`): per-file claims become `TrackInfo`s ordered by track number then filename; album claims are
   the consensus of the files' album-level tags. Absent tags are absent fields — never empty strings.
3. **Refuse re-adds** (`library.py`): any source path already in `files.source_path` → "already added", no writes.
4. **Write** (`library.py`, one transaction): create the album row (its id names the copy directory), artists, tracks,
   credits, genres; write every claim as a `source_values` row; run the identity merge — a real `merge(entity)` function
   that reads all of an entity's source_values and writes merged columns, trivial today, the seam tomorrow.
5. **Copy** files into `<root>/album-<id>/<track>-<title>.<ext>` (track number zero-padded; title slugified ASCII-ish,
   collisions suffixed). Hash and probe each copy for the measurements; write file rows. A copy failure rolls back the
   transaction and removes the partial directory — originals are never touched either way.
6. **Report**: a summary card — album, artist, year, track count, where it landed, and a note of how many claims were
   recorded. Output worth reading is the requirement.

## Tests

`tests/conftest.py` gains the fixture harness: a corpus loader (tomllib) and `materialise_album(album, tmp_path)`, which
copies tone fixtures and writes the corpus tags through mediafile — sparse fields genuinely absent from the files. An
autouse fixture points `$LEEKS_ROOT` at a tmp directory.

| Test                       | Asserts                                                                                                                                  |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `test_harness`             | Materialised albums round-trip their corpus tags through mediafile; sparse fields truly absent                                           |
| `test_detect`              | Clean album accepted; mixed album tags refused with both named; nested audio refused; empty dir refused                                  |
| `test_add_clean`           | Row counts and merged values across all tables; source_values match tags; copies exist; originals byte-identical; measurements populated |
| `test_add_sparse`          | *Tape Hiss Archipelago*: NULL year, NULL track numbers, no genre rows, no claims for absent fields — and the add succeeds                |
| `test_add_feat`            | "Tin Hatch Choir feat. Vesna Holloway" is one artist row, verbatim; the track credit points at it                                        |
| `test_add_duplicate_title` | "Glass Harbour" on two albums → two distinct track rows, no cross-linking                                                                |
| `test_readd`               | Second add refused; database row counts unchanged                                                                                        |
| `test_cli_add`             | Exit 0 and a card naming the album on success; exit nonzero with the import hint on a multi-album dir                                    |

Each build step lands with its tests; `just check` green throughout.

## Commit shape

Roughly one commit per build-order step in the high-level plan, each leaving the gates green: harness, schema,
models+tags, detect, write path, CLI, docs. Branch declared ready with land-suggestion titles when the slice is runnable
end-to-end against the fixtures and a real directory.
