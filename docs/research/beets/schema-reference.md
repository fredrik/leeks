# Beets SQLite Database Schema Reference

Reference material for the beets music manager database, based on the source at `github.com/beetbox/beets` (current
`master`).

______________________________________________________________________

## 1. Tables Overview

The database contains **5 tables**:

| Table              | Purpose                                        |
| ------------------ | ---------------------------------------------- |
| `items`            | One row per audio file (track)                 |
| `albums`           | One row per album                              |
| `item_attributes`  | Flexible (custom) key-value fields for items   |
| `album_attributes` | Flexible (custom) key-value fields for albums  |
| `migrations`       | Tracks which data migrations have been applied |

There are no foreign key constraints enforced at the SQL level. The `items.album_id` column references `albums.id` by
convention, and queries use `LEFT JOIN items ON albums.id = items.album_id`. Singletons (non-album tracks) have
`album_id = NULL`.

______________________________________________________________________

## 2. `items` Table — Full Column List

Source: `beets/library/models.py:634-727`

| Column                 | SQL Type              | Python Type     | Notes                                      |
| ---------------------- | --------------------- | --------------- | ------------------------------------------ |
| `id`                   | `INTEGER PRIMARY KEY` | `int \| None`   | Auto-increment row ID                      |
| `path`                 | `BLOB`                | `bytes`         | Absolute filesystem path to the audio file |
| `album_id`             | `INTEGER`             | `int \| None`   | FK to `albums.id`; NULL for singletons     |
| `title`                | `TEXT`                | `str`           |                                            |
| `artist`               | `TEXT`                | `str`           | Primary/display artist                     |
| `artists`              | `TEXT`                | `list[str]`     | Multi-value, `\0`-delimited                |
| `artists_ids`          | `TEXT`                | `list[str]`     | MusicBrainz artist IDs, multi-value        |
| `artist_sort`          | `TEXT`                | `str`           |                                            |
| `artists_sort`         | `TEXT`                | `list[str]`     | Multi-value                                |
| `artist_credit`        | `TEXT`                | `str`           |                                            |
| `artists_credit`       | `TEXT`                | `list[str]`     | Multi-value                                |
| `remixer`              | `TEXT`                | `str`           |                                            |
| `album`                | `TEXT`                | `str`           |                                            |
| `albumartist`          | `TEXT`                | `str`           |                                            |
| `albumartists`         | `TEXT`                | `list[str]`     | Multi-value                                |
| `albumartist_sort`     | `TEXT`                | `str`           |                                            |
| `albumartists_sort`    | `TEXT`                | `list[str]`     | Multi-value                                |
| `albumartist_credit`   | `TEXT`                | `str`           |                                            |
| `albumartists_credit`  | `TEXT`                | `list[str]`     | Multi-value                                |
| `genres`               | `TEXT`                | `list[str]`     | Multi-value, `\0`-delimited                |
| `style`                | `TEXT`                | `str`           |                                            |
| `discogs_albumid`      | `INTEGER`             | `int`           |                                            |
| `discogs_artistid`     | `INTEGER`             | `int`           |                                            |
| `discogs_labelid`      | `INTEGER`             | `int`           |                                            |
| `lyricist`             | `TEXT`                | `str`           |                                            |
| `composer`             | `TEXT`                | `str`           |                                            |
| `composer_sort`        | `TEXT`                | `str`           |                                            |
| `work`                 | `TEXT`                | `str`           | Musical work name                          |
| `mb_workid`            | `TEXT`                | `str`           | MusicBrainz work ID                        |
| `work_disambig`        | `TEXT`                | `str`           |                                            |
| `arranger`             | `TEXT`                | `str`           |                                            |
| `grouping`             | `TEXT`                | `str`           |                                            |
| `year`                 | `INTEGER`             | `int`           | Zero-padded to 4 digits in display         |
| `month`                | `INTEGER`             | `int`           | Zero-padded to 2 digits                    |
| `day`                  | `INTEGER`             | `int`           | Zero-padded to 2 digits                    |
| `track`                | `INTEGER`             | `int`           | Track number, zero-padded to 2             |
| `tracktotal`           | `INTEGER`             | `int`           |                                            |
| `disc`                 | `INTEGER`             | `int`           |                                            |
| `disctotal`            | `INTEGER`             | `int`           |                                            |
| `lyrics`               | `TEXT`                | `str`           |                                            |
| `comments`             | `TEXT`                | `str`           |                                            |
| `bpm`                  | `INTEGER`             | `int`           |                                            |
| `comp`                 | `INTEGER`             | `bool`          | Compilation flag (SQLite has no bool)      |
| `mb_trackid`           | `TEXT`                | `str`           | MusicBrainz recording ID                   |
| `mb_albumid`           | `TEXT`                | `str`           |                                            |
| `mb_artistid`          | `TEXT`                | `str`           |                                            |
| `mb_artistids`         | `TEXT`                | `list[str]`     | Multi-value                                |
| `mb_albumartistid`     | `TEXT`                | `str`           |                                            |
| `mb_albumartistids`    | `TEXT`                | `list[str]`     | Multi-value                                |
| `mb_releasetrackid`    | `TEXT`                | `str`           |                                            |
| `trackdisambig`        | `TEXT`                | `str`           |                                            |
| `albumtype`            | `TEXT`                | `str`           | Primary release type                       |
| `albumtypes`           | `TEXT`                | `str`           | All types, `"; "`-delimited                |
| `label`                | `TEXT`                | `str`           |                                            |
| `barcode`              | `TEXT`                | `str`           |                                            |
| `acoustid_fingerprint` | `TEXT`                | `str`           |                                            |
| `acoustid_id`          | `TEXT`                | `str`           |                                            |
| `mb_releasegroupid`    | `TEXT`                | `str`           |                                            |
| `release_group_title`  | `TEXT`                | `str`           |                                            |
| `asin`                 | `TEXT`                | `str`           | Amazon Standard Identification Number      |
| `isrc`                 | `TEXT`                | `str`           |                                            |
| `catalognum`           | `TEXT`                | `str`           |                                            |
| `script`               | `TEXT`                | `str`           | ISO 15924 script code                      |
| `language`             | `TEXT`                | `str`           | ISO 639 language code                      |
| `country`              | `TEXT`                | `str`           | Release country                            |
| `albumstatus`          | `TEXT`                | `str`           | MusicBrainz release status                 |
| `media`                | `TEXT`                | `str`           | Physical media type (CD, Vinyl, etc.)      |
| `albumdisambig`        | `TEXT`                | `str`           |                                            |
| `releasegroupdisambig` | `TEXT`                | `str`           |                                            |
| `disctitle`            | `TEXT`                | `str`           |                                            |
| `encoder`              | `TEXT`                | `str`           |                                            |
| `rg_track_gain`        | `REAL`                | `float \| None` | ReplayGain track gain (dB)                 |
| `rg_track_peak`        | `REAL`                | `float \| None` |                                            |
| `rg_album_gain`        | `REAL`                | `float \| None` | ReplayGain album gain (dB)                 |
| `rg_album_peak`        | `REAL`                | `float \| None` |                                            |
| `r128_track_gain`      | `REAL`                | `float \| None` | R128 loudness normalization                |
| `r128_album_gain`      | `REAL`                | `float \| None` |                                            |
| `original_year`        | `INTEGER`             | `int`           | Original release date                      |
| `original_month`       | `INTEGER`             | `int`           |                                            |
| `original_day`         | `INTEGER`             | `int`           |                                            |
| `initial_key`          | `TEXT`                | `str \| None`   | Musical key (e.g. "C#m"), normalized       |
| `length`               | `REAL`                | `float`         | Duration in seconds                        |
| `bitrate`              | `INTEGER`             | `int`           | Bits per second (displayed as kbps)        |
| `bitrate_mode`         | `TEXT`                | `str`           | CBR/VBR/ABR                                |
| `encoder_info`         | `TEXT`                | `str`           |                                            |
| `encoder_settings`     | `TEXT`                | `str`           |                                            |
| `format`               | `TEXT`                | `str`           | File format (MP3, FLAC, etc.)              |
| `samplerate`           | `INTEGER`             | `int`           | Hz (displayed as kHz)                      |
| `bitdepth`             | `INTEGER`             | `int`           |                                            |
| `channels`             | `INTEGER`             | `int`           |                                            |
| `mtime`                | `REAL`                | `float`         | File modification time (epoch)             |
| `added`                | `REAL`                | `float`         | Import timestamp (epoch)                   |

**Index:** `idx_item_album_id` on `(album_id)`.

**92 fixed columns total.**

______________________________________________________________________

## 3. `albums` Table — Full Column List

Source: `beets/library/models.py:234-278`

| Column                 | SQL Type              | Python Type     | Notes                                           |
| ---------------------- | --------------------- | --------------- | ----------------------------------------------- |
| `id`                   | `INTEGER PRIMARY KEY` | `int \| None`   | Auto-increment row ID                           |
| `artpath`              | `BLOB`                | `bytes \| None` | Filesystem path to cover art file; NULL if none |
| `added`                | `REAL`                | `float`         | Import timestamp (epoch)                        |
| `albumartist`          | `TEXT`                | `str`           |                                                 |
| `albumartist_sort`     | `TEXT`                | `str`           |                                                 |
| `albumartist_credit`   | `TEXT`                | `str`           |                                                 |
| `albumartists`         | `TEXT`                | `list[str]`     | Multi-value                                     |
| `albumartists_sort`    | `TEXT`                | `list[str]`     | Multi-value                                     |
| `albumartists_credit`  | `TEXT`                | `list[str]`     | Multi-value                                     |
| `album`                | `TEXT`                | `str`           |                                                 |
| `genres`               | `TEXT`                | `list[str]`     | Multi-value                                     |
| `style`                | `TEXT`                | `str`           |                                                 |
| `discogs_albumid`      | `INTEGER`             | `int`           |                                                 |
| `discogs_artistid`     | `INTEGER`             | `int`           |                                                 |
| `discogs_labelid`      | `INTEGER`             | `int`           |                                                 |
| `year`                 | `INTEGER`             | `int`           |                                                 |
| `month`                | `INTEGER`             | `int`           |                                                 |
| `day`                  | `INTEGER`             | `int`           |                                                 |
| `disctotal`            | `INTEGER`             | `int`           |                                                 |
| `comp`                 | `INTEGER`             | `bool`          | Compilation flag                                |
| `mb_albumid`           | `TEXT`                | `str`           |                                                 |
| `mb_albumartistid`     | `TEXT`                | `str`           |                                                 |
| `mb_albumartistids`    | `TEXT`                | `list[str]`     | Multi-value                                     |
| `albumtype`            | `TEXT`                | `str`           |                                                 |
| `albumtypes`           | `TEXT`                | `str`           | `"; "`-delimited                                |
| `label`                | `TEXT`                | `str`           |                                                 |
| `barcode`              | `TEXT`                | `str`           |                                                 |
| `mb_releasegroupid`    | `TEXT`                | `str`           |                                                 |
| `release_group_title`  | `TEXT`                | `str`           |                                                 |
| `asin`                 | `TEXT`                | `str`           |                                                 |
| `catalognum`           | `TEXT`                | `str`           |                                                 |
| `script`               | `TEXT`                | `str`           |                                                 |
| `language`             | `TEXT`                | `str`           |                                                 |
| `country`              | `TEXT`                | `str`           |                                                 |
| `albumstatus`          | `TEXT`                | `str`           |                                                 |
| `albumdisambig`        | `TEXT`                | `str`           |                                                 |
| `releasegroupdisambig` | `TEXT`                | `str`           |                                                 |
| `rg_album_gain`        | `REAL`                | `float \| None` |                                                 |
| `rg_album_peak`        | `REAL`                | `float \| None` |                                                 |
| `r128_album_gain`      | `REAL`                | `float \| None` |                                                 |
| `original_year`        | `INTEGER`             | `int`           |                                                 |
| `original_month`       | `INTEGER`             | `int`           |                                                 |
| `original_day`         | `INTEGER`             | `int`           |                                                 |

**44 fixed columns total** (including `id`). No indices beyond the primary key.

______________________________________________________________________

## 4. Flexible Attribute Tables

Both `item_attributes` and `album_attributes` share the same schema:

```sql
CREATE TABLE item_attributes (
    id          INTEGER PRIMARY KEY,
    entity_id   INTEGER,          -- FK to items.id or albums.id
    key         TEXT,             -- attribute name
    value       TEXT,             -- always stored as TEXT
    UNIQUE(entity_id, key) ON CONFLICT REPLACE
);
CREATE INDEX item_attributes_by_entity ON item_attributes (entity_id);
```

### Key Design Points

- **All values are TEXT.** There is no type information stored. When beets reads a flex attr, it uses the `Default` type
  (which is a plain string). Plugins can register typed flex attrs via `item_types()` / `album_types()` hooks, but the
  DB column is always TEXT regardless.
- **UPSERT via UNIQUE constraint.** `ON CONFLICT REPLACE` means setting a flex attr that already exists overwrites it
  without an explicit UPDATE.
- **No cascading deletes.** When an item or album is deleted, its flex attrs are cleaned up in application code, not via
  SQL foreign key constraints.
- **Plugins use these heavily.** The `fetchart` plugin stores `art_source` as a flex attr. The `lyrics` plugin stores
  `lyrics_backend`, `lyrics_url`, etc. The `acousticbrainz`, `lastgenre`, `parentwork`, and many other plugins write
  flex attrs.

### How Flex Attrs Are Loaded

Flex attrs are batch-loaded when querying items/albums. The ORM fetches all flex attrs for the result set in one query:

```sql
SELECT * FROM item_attributes WHERE entity_id IN (SELECT id FROM ...)
```

They are then indexed by `entity_id` and attached to each model object in memory.

______________________________________________________________________

## 5. `migrations` Table

```sql
CREATE TABLE migrations (
    name       TEXT NOT NULL,
    table_name TEXT NOT NULL,
    PRIMARY KEY(name, table_name)
);
```

Tracks which named migrations have been applied to which tables. Current migrations (registered in
`beets/library/library.py`):

1. **`MultiGenreFieldMigration`** — Applied to both `items` and `albums`. Migrates legacy single-value `genre` field to
   multi-value `genres`.
1. **`LyricsMetadataInFlexFieldsMigration`** — Applied to `items` only. Moves lyrics metadata (backend, URL, language)
   from hypothetical fixed fields into flex attributes.

Schema evolution for adding new fixed columns uses `ALTER TABLE ADD COLUMN` at startup — if the Python model defines a
field that doesn't exist in the database, it's added automatically. This means the DB schema is self-healing on upgrade,
but columns are **never removed**.

______________________________________________________________________

## 6. Stored vs. Computed/Derived Fields

### Stored in DB

Everything listed in the `_fields` dicts (sections 2 and 3 above) is persisted as a real SQLite column.

### Computed at Runtime (never stored)

These are registered via `_getters()` and exist only in the object model:

**Item computed fields:**

| Field           | Source                                              |
| --------------- | --------------------------------------------------- |
| `singleton`     | `True` if `album_id is None`                        |
| `filesize`      | `os.path.getsize(path)` — reads actual file on disk |
| `has_cover_art` | Checks embedded art via mediafile                   |
| Plugin fields   | Registered via `plugins.item_field_getters()`       |

**Album computed fields:**

| Field         | Source                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------ |
| `path`        | Directory of the album's first item (`os.path.dirname(item.path)`) — **not a real column** |
| `albumtotal`  | Count of items in the album                                                                |
| Plugin fields | Registered via `plugins.album_field_getters()`                                             |

### Item Field Inheritance from Album

When accessing a field on an Item that doesn't exist on the item itself, beets falls back to the item's parent Album.
This means album-level flex attrs are accessible on items transparently. The `Album.item_keys` list (33 fields) defines
which album fields are **synced** (copied) to items on album updates — these are denormalized into both tables.

### Media-Backed Fields

A subset of item fields map directly to audio file metadata tags (via the `mediafile` library). These are defined by
`Item._media_fields` (intersection of `_fields` with `MediaFile.readable_fields()`). Only these fields are read from
disk on `item.read()` and written back on `item.write()`.

The writable subset is `Item._media_tag_fields` (excludes read-only audio properties like `bitrate`, `length`,
`samplerate`, etc.).

______________________________________________________________________

## 7. Album Art / Image Storage

Album art is stored as a **filesystem path**, not as binary data in the DB.

- **Column:** `albums.artpath` — `BLOB` type (stores a bytestring path), nullable.
- **Property:** `Album.art_filepath` returns it as a `pathlib.Path`.
- **Setting art:** `Album.set_art(path)` copies/moves the image file to the album directory (using a configured
  filename, default `cover`), then stores the destination path in `artpath`.
- **Art destination:** Computed by `Album.art_destination()`, which places art next to the album's items using the
  configured art filename.
- **Removal:** Setting `album.artpath = None` clears the reference. The file itself is deleted separately if requested.

### Plugin integration

- **fetchart** — Downloads art from Cover Art Archive, Amazon, etc. Calls `album.set_art()`. Optionally stores
  `art_source` as a flex attr.
- **embedart** — Embeds/extracts art from audio file metadata. Uses `artpath` as the source image.
- **thumbnails** — Generates freedesktop thumbnails from `artpath`.

There is **no thumbnail/resized image cache** in the database. All image processing happens on the filesystem.

______________________________________________________________________

## 8. Path Template System

### Configuration

Path templates are configured under the `paths:` key in `config.yaml`:

```yaml
paths:
    default: $albumartist/$album/$track $title
    comp: Compilations/$album/$track $title
    singleton: Non-Album/$artist/$title
    albumtype:soundtrack: Soundtracks/$album/$track $title
```

The keys are either special names (`default`, `comp`, `singleton`) or arbitrary beets queries. They are evaluated in
order; the first matching query wins, falling back to `default`.

### How Destination Paths Are Computed

`Item.destination()` (`models.py:1195`) computes the target filesystem path:

1. **Query matching** — Iterate `path_formats`, test each query against the item. Use the first match (or `default`).
1. **Template evaluation** — Substitute all `$field` references using the item's formatted field values. Template
   functions like `%upper{}`, `%if{}`, `%aunique{}` are available.
1. **Path sanitization** — Unicode normalization (NFC/NFD), optional asciification, path separator replacement,
   character replacements.
1. **Legalization** — Truncate path components to filesystem limits, replace illegal characters.
1. **Join with library directory** — Prepend the library's base directory.

### Relationship Between `path` Column and Templates

- `items.path` stores the **actual current location** of the audio file on disk.
- Templates compute the **desired destination** path.
- These may diverge if files haven't been moved after a metadata change. The `beet move` command re-evaluates templates
  and moves files to match.
- `albums.path` is **not a real column** — it's computed at runtime as the directory of the album's first item.

### Template Syntax

- `$field` or `${field}` — field value substitution
- `%func{arg1,arg2}` — template function call
- `$$` — literal `$`
- `/` in template — creates directory levels

### Built-in Template Functions

Defined in `models.py:1314-1585`:

| Function                           | Description                     |
| ---------------------------------- | ------------------------------- |
| `%lower{text}`                     | Lowercase                       |
| `%upper{text}`                     | Uppercase                       |
| `%capitalize{text}`                | Capitalize first letter         |
| `%title{text}`                     | Title case                      |
| `%left{text,n}`                    | First n characters              |
| `%right{text,n}`                   | Last n characters               |
| `%if{cond,then,else}`              | Conditional                     |
| `%ifdef{field,then,else}`          | Check if flex field is defined  |
| `%asciify{text}`                   | Transliterate to ASCII          |
| `%aunique{keys,disam,bracket}`     | Album disambiguation suffix     |
| `%sunique{keys,disam,bracket}`     | Singleton disambiguation suffix |
| `%time{datetime,fmt}`              | strftime formatting             |
| `%first{text,count,skip,sep,join}` | Extract from delimited values   |

Plugins can register additional template functions and fields.

______________________________________________________________________

## 9. Schema Design Oddities and Limitations

### Massive denormalization

Album metadata is **copied into every item row** (33 fields via `item_keys`). Fields like `albumartist`, `year`,
`genres`, `label`, `mb_albumid`, etc. exist in both `items` and `albums`. Updating an album requires propagating changes
to all its items. This is done in application code (`Album.store()` calls item updates).

### No actual foreign keys

`album_id` is a plain INTEGER with no `REFERENCES` clause and no `ON DELETE CASCADE`. Orphaned items or dangling
album_ids are possible if application code has bugs.

### Flex attrs are untyped at the DB level

All flex attr values are TEXT. A plugin might store an integer, but it's serialized as a string and deserialized based
on what type the plugin declares at runtime. If the plugin isn't loaded, the value is treated as a plain string.

### Paths stored as BLOBs

Filesystem paths are stored as raw bytes (`BLOB`), not TEXT. This preserves non-UTF-8 byte sequences that can exist on
Unix filesystems, but makes the database harder to query with standard SQL tools.

### No multi-value column type in SQLite

Multi-value fields (like `artists`, `genres`, `mb_artistids`) are stored as delimiter-separated strings in a single TEXT
column. The delimiter is `\0` (null character) for most fields, or `"; "` for `albumtypes`. There is no normalization
into junction tables. Querying individual values requires application-level parsing.

### Dates are epoch floats, not ISO strings

`added` and `mtime` are REAL columns storing Unix epoch timestamps. Date components (`year`, `month`, `day`) are
separate INTEGER columns rather than a single date field.

### Columns are never removed

Schema evolution only adds columns via `ALTER TABLE ADD COLUMN`. Removed fields from the Python model remain as orphaned
columns in the database forever.

### Album `path` is ephemeral

Albums have no stored path. `Album.path` is computed on the fly from the first item's directory. If an album has no
items, accessing `path` raises a `ValueError`. This also means the album "path" could change if items are reordered.

### Boolean fields use INTEGER

SQLite has no native boolean. `comp` is stored as `INTEGER` and interpreted as boolean in Python. The value `0` = false,
anything else = true.

### ReplayGain fields are nullable

The `rg_*` and `r128_*` gain/peak fields use `NULL_FLOAT` — they can be `NULL` to indicate "not measured". Most other
numeric fields default to `0`.

### No indexing on common query fields

Beyond `idx_item_album_id` on `items.album_id`, there are no indices on frequently queried columns like `artist`,
`album`, `title`, `mb_trackid`, etc. All text searches are full table scans.
