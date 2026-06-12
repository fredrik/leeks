# Beets Data Model: Year-by-Year Evolution, 2014–2026

## The Numbers

| Year     | Item Fields | Album Fields | Plugins | Key Change                                                         |
| -------- | ----------- | ------------ | ------- | ------------------------------------------------------------------ |
| **2014** | 56          | 30           | 37      | dbcore extracted, flex attrs born                                  |
| **2015** | 57          | 29           | 46      | OR queries, metasync, `types` plugin                               |
| **2016** | 56          | 29           | 54      | `NotQuery`, `NoneQuery`, `DurationQuery`, R128 fields              |
| **2017** | 61          | 30           | 57      | Relative date queries, Python 3 porting begins                     |
| **2018** | 62          | 30           | 58      | Discogs IDs, parentwork/MB work fields, AURA, Deezer               |
| **2019** | 66          | 34           | 61      | `LazyConvertDict`, SQLite extension loading                        |
| **2020** | 70          | 35           | 67      | `remixer`, `bitrate_mode`, `encoder_info/settings`, `albumtypes`   |
| **2021** | 72          | 35           | 68      | DB revision tracking, `FormattedMapping` optimization              |
| **2022** | 76          | 36           | 70      | `DelimitedString` type, `release_group_title`                      |
| **2023** | 78          | 37           | 70      | `NamedQuery`, `SingletonQuery` pushed to SQL, typing modernization |
| **2024** | 88          | 41           | 74      | Multi-value artist fields land (PR #4743), `barcode`               |
| **2025** | 88          | 42           | 76      | `InQuery`, `SmartArtistSort` → dbcore, multi-value `genres`        |
| **2026** | 92          | 44           | 78      | Migrations framework, library split into package                   |

*Field counts are from `_fields` dicts on `Item` and `Album` on master at each mid-year snapshot, counted by a single
consistent regex. Plugin counts are entries in `beetsplug/` excluding `__init__.py` and private modules.*

## Year-by-Year Narrative

### 2014: The Foundation Year

The dbcore extraction was complete and flexible attributes were live. This was beets' architectural coming-of-age — the
rigid hardcoded schema was replaced by a three-tier field model (fixed/flexible/computed) with a proper type system
driving both storage and query dispatch. **37 plugins** shipped. The architecture was set; everything after this is
filling in fields and polish.

### 2015: Quiet Growth

Five new plugins (metasync, play, plexupdate, spotify, thumbnails). The `types` plugin appeared, letting users declare
custom types for flexible attributes in their config. OR queries landed. No schema changes. This was a year of ecosystem
growth, not architecture.

### 2016: Query System Matures

The biggest query system expansion: `NotQuery` (negation), `NoneQuery` (null checks), `DurationQuery` (M:SS format), and
`StringQuery` (whole-string match). R128 loudness fields arrived alongside the existing ReplayGain fields. **15 new
plugins** in one year — the fastest plugin growth rate in the project's history. Highlights: `acousticbrainz`, `edit`,
`export`, `hook`, `embyupdate`.

### 2017: The Python 3 Transition

Almost no schema changes (just `lyricist`, `composer_sort`, `arranger`). The year was consumed by Python 3 porting —
`six` imports everywhere, `buffer`/`memoryview` handling for BLOB fields, `collections.abc` migration. Relative date
queries (`-3d`, `+2w`) were added. The calm before the storm.

### 2018: The Discogs & MusicBrainz Expansion

**+10 item fields, +6 album fields** — the biggest single-year schema expansion. Three Discogs ID fields
(`discogs_albumid/artistid/labelid`), MusicBrainz work metadata (`work`, `mb_workid`, `work_disambig`),
`mb_releasetrackid`, `trackdisambig`, `isrc`, `releasegroupdisambig`. This reflected beets expanding beyond
MusicBrainz-only metadata into Discogs as a first-class data source and deeper MusicBrainz relationship modeling (works,
not just releases). **13 new plugins** including `parentwork`, `aura`, `deezer`, `bpsync`.

### 2019: Internal Optimization

Modest schema changes. The big wins were internal: `LazyConvertDict` deferred type conversion from SQL until access time
(a meaningful performance improvement for large libraries), SQLite extension loading support, and decoupling
`queryparse` from the beets config system. The plugin count actually *decreased* from 70 to 61 due to removals and
restructuring.

### 2020: Audio Encoding Metadata

New encoding-detail fields: `bitrate_mode` (CBR/VBR/ABR), `encoder_info`, `encoder_settings`, `remixer`. The
`albumtypes` field arrived as a `DelimitedString` — beets' first multi-value fixed field, signaling a shift toward
richer data types. Plugin count hit 77. The `advancedrewrite`, `autobpm`, `limit`, `listenbrainz`, `musicbrainz`,
`replace`, `substitute` plugins appeared.

### 2021: Performance Architecture

The database revision tracking system landed — `Database` maintains a monotonic revision counter incremented on writes,
and `Model.load()` short-circuits if the model is clean and the DB revision hasn't changed. `FormattedMapping` gained
lazy album loading. These were targeted performance improvements for large-library workflows where the same items are
accessed repeatedly.

### 2022: Multi-Value Fields Arrive

`DelimitedString` became a proper type in dbcore, and `albumtypes` (on both items and albums) used it as
`SEMICOLON_SPACE_DSV`. `release_group_title` was added to both entities. The `r128_*_gain` fields changed from
`NullPaddedInt` to `NULL_FLOAT`, fixing a long-standing type mismatch.

### 2023: Typing Modernization

The `Type` base class became `Type[T, N]` with ABC enforcement. `Query` became an ABC. `NamedQuery` was extracted as a
formal base class for non-field queries. `SingletonQuery` was pushed from Python-side filtering into SQL. The year was
dominated by typing work — `from __future__ import annotations`, generic type parameters, proper `__eq__`/`__hash__` on
query classes. No new fields or plugins.

### 2024: The Multi-Value Artist Revolution

The biggest schema change since 2018. PR [#4743](https://github.com/beetbox/beets/pull/4743) (merged September 2023,
visible in this mid-2024 snapshot) added 10 multi-value artist fields: `artists`, `artists_ids`, `artists_sort`,
`artists_credit`, `albumartists`, `albumartists_sort`, `albumartists_credit`, `mb_artistids`, `mb_albumartistids` (all
`DelimitedString` using null-byte separators). Plus `barcode` (PR #5153). Items jumped from 78 to **88 fields** in one
year. The old single-value `artist`/`albumartist` fields were kept alongside for backward compatibility.

### 2025: Multi-Value Genres and Structural Refactoring

Multi-value `genres` field landed (December 2025, PR #6169), modeled on the same pattern as multi-value artists — a
`genres` list field alongside the legacy `genre` string, with `ensure_first_value()` keeping them in sync. Included a
formal `MultiGenreFieldMigration`. `SmartArtistSort` moved from `library.py` into `dbcore/query.py`. `InQuery` was added
for `field IN (...)` SQL patterns. `AnyFieldQuery` was removed in favor of model-level `any_field_query()` methods.

### 2026: Package Split and Migration Framework

The `library.py` monolith was finally split into a `beets/library/` package (`models.py`, `library.py`, `queries.py`,
`migrations.py`). A formal `Migration` ABC with a `migrations` tracking table was introduced. Items reached **92
fields**, albums **44 fields**. **78 plugins** — the highest ever. The long tail of multi-value field integration
continued, with plugins like `ftintitle`, `lastgenre`, `discogs`, and `spotify` updated to use `artists`/`albumartists`
instead of string-splitting `artist`.

______________________________________________________________________

## The Multi-Value Artist Fields in Detail

### The PR

**PR [#4743](https://github.com/beetbox/beets/pull/4743)** — "Add support for artists and albumartists multi-valued
tags"

- Author: Jesse Bannon (`@jbann1994`)
- Merged: **2023-09-09** (commit `f72261e44`)
- +511 lines, -26 lines across 17 files

### What it added

10 new `DelimitedString` fields across Item and Album:

**On Item:**

| Field                 | Stores                                 |
| --------------------- | -------------------------------------- |
| `artists`             | List of track artist names             |
| `artists_ids`         | List of MusicBrainz artist IDs         |
| `artists_sort`        | List of sortable artist names          |
| `artists_credit`      | List of artist-credit-as-printed names |
| `albumartists`        | List of album artist names             |
| `albumartists_sort`   | List of sortable album artist names    |
| `albumartists_credit` | List of album artist credits           |
| `mb_artistids`        | List of MB artist UUIDs                |
| `mb_albumartistids`   | List of MB album artist UUIDs          |

**On Album:**

| Field                 | Stores                              |
| --------------------- | ----------------------------------- |
| `albumartists`        | List of album artist names          |
| `albumartists_sort`   | List of sortable album artist names |
| `albumartists_credit` | List of album artist credits        |

### How it works

The key design decision: **the old single-value fields (`artist`, `albumartist`, etc.) were kept alongside the new
multi-value ones.** They weren't replaced. This is the denormalization trade-off made explicit:

- `artist` = `"Beyoncé & Jay-Z"` (the joined string, for display and backward compatibility)
- `artists` = `["Beyoncé", "Jay-Z"]` (the separated list, for proper per-artist operations)

The storage mechanism is a new `MULTI_VALUE_DSV` type — a `DelimitedString` using a **null character** (`\x00`) as the
delimiter:

```python
MULTI_VALUE_DSV = DelimitedString(delimiter='\\␀')
```

This maps directly to how ID3v2.4 stores multi-value tags (null-separated). In SQLite, it's stored as a single TEXT
column with null-byte separators. In Python, it's a `list[str]`.

### The MusicBrainz plumbing

The core change was splitting `_flatten_artist_credit()` into two functions:

- `_multi_artist_credit(credit, include_join_phrase)` — returns **lists** of artist parts (names, sort names, credits),
  optionally including join phrases like " & " or " feat. "
- `_flatten_artist_credit(credit)` — calls the above with `include_join_phrase=True` and joins everything into single
  strings (the old behavior)

So for a MusicBrainz release with artists `["Beyoncé", "Jay-Z"]` joined by `" & "`:

- `_flatten_artist_credit` → `"Beyoncé & Jay-Z"` (written to `artist`)
- `_multi_artist_credit(..., include_join_phrase=False)` → `["Beyoncé", "Jay-Z"]` (written to `artists`)

### The long tail of follow-up work

The initial PR was just the plumbing. It took **2+ more years** of follow-up to fully integrate:

| Date    | Commit      | What                                                                                                                                      |
| ------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 2023-09 | `f72261e44` | Initial multi-artist fields (PR #4743)                                                                                                    |
| 2024-03 | `6077b7a3a` | `barcode` field added (PR #5153)                                                                                                          |
| 2025-12 | `70bf57baf` | Multi-value `genres` field with migration (PR #6169)                                                                                      |
| 2025–26 | various     | Plugin fixes: `ftintitle`, `lastgenre`, `discogs`, `spotify` updated to use `artists`/`albumartists` instead of string-splitting `artist` |
| 2026-01 | `2ea7886c0` | Fix handling multi-valued fields (PR #6387)                                                                                               |

The `genres` change (Dec 2025) was modeled on the same pattern — a new `genres` list field alongside the legacy `genre`
string field, with `ensure_first_value('genre', 'genres')` keeping them in sync. It included a formal migration
(`MultiGenreFieldMigration`) to split existing comma/semicolon/slash-separated genre strings into proper lists.

### Why it took so long

PR #4743 was opened as an issue long before 2023. The fundamental tension was:

1. **ID3v2.3 vs ID3v2.4**: ID3v2.3 (the more widely supported standard) uses `/` as a multi-value separator *within a
   single tag frame*. ID3v2.4 uses null bytes to truly separate values. Many players don't support v2.4. Beets had to
   support both via its existing `id3v23` config toggle.

2. **Backward compatibility**: Every query, template, plugin, and display path that touched `artist` had to keep
   working. The solution was additive — new fields alongside old ones, never replacing them.

3. **The join-phrase problem**: MusicBrainz credits include join phrases ("feat.", "&", "and"). The joined `artist`
   string includes these; the split `artists` list does not. Which is "correct" depends on context (display vs. lookup
   vs. matching), so both representations are needed.

The result is arguably the ugliest part of the beets data model — 9 artist-related fields on Item where a normalized
`artists` table would have 2-3 columns — but it's the pragmatic choice that preserved backward compatibility with 15
years of existing configurations, templates, and plugins.

______________________________________________________________________

## Synthesis

### The Pattern: Stability Punctuated by Bursts

Beets' data model evolution from 2014–2026 follows a clear pattern: **long periods of stability punctuated by short
bursts of schema expansion**, each driven by a specific external motivation:

1. **2018 burst** (Discogs + MusicBrainz works): Driven by users wanting richer metadata sources beyond basic
   MusicBrainz release data.
2. **2020 burst** (encoding metadata + multi-value types): Driven by audiophile users wanting bitrate mode, encoder
   details, and the realization that fields like `albumtype` are inherently multi-valued.
3. **2023–2025 burst** (multi-value artists, then genres): The long-awaited acknowledgment that a track can have
   multiple artists — a fundamental limitation of the original single-string `artist` field that took 15 years to
   properly address. Multi-value genres followed 2 years later using the same pattern.

### What Didn't Change

The most remarkable thing about this 12-year span is what *didn't* change:

- **Still only 2 entity types** (Item, Album). No Artist, Playlist, Tag, or Label entities were ever added.
- **Still SQLite only**. The early `BaseLibrary` abstraction for alternative backends was never used.
- **Still 4+1 tables** (items, albums, item_attributes, album_attributes, plus a migrations tracking table added in
  2025–2026).
- **Still denormalized** — album metadata duplicated on items for query efficiency.
- **dbcore's core design** (Model with fixed/flex/computed fields, Type-driven query dispatch, EAV flex tables) has been
  stable since 2014.

### Where It Veered

The project never veered off its core mission (metadata-correct music library management), but it **accumulated scope
creep through plugins**. From 37 plugins in 2014 to 78 in 2026, beets became an integration hub — Discogs, Spotify,
Deezer, ListenBrainz, Plex, Kodi, Emby, Subsonic, Sonos, AURA. Each integration plugin is individually small, but
collectively they expanded beets' surface area far beyond "get your music collection right." The core data model stayed
focused; the plugin ecosystem sprawled.

### The Missed Opportunity

The one structural limitation that was never addressed is the **lack of a first-class Artist entity**. With 92 item
fields by 2026, many are artist-related near-duplicates (`artist`, `artists`, `artist_sort`, `artists_sort`,
`artist_credit`, `artists_credit`, `mb_artistid`, `mb_artistids`, `albumartist`, `albumartists`...). A normalized
`artists` table with a many-to-many relationship to items would have been cleaner, but beets chose the pragmatic path of
flat denormalized fields. Given SQLite's characteristics and the project's small-team history, this was probably the
right call — but it means the data model is wide rather than deep, with a lot of redundancy between item-level and
album-level metadata.

### Why the Denormalization Persists

SQLite didn't *cause* the denormalization — it made it the path of least resistance:

1. **The tag-file mental model.** Music files *are* denormalized. An MP3's ID3 tags store `artist`, `album`,
   `albumartist` as flat strings on every file. Beets' data model mirrors the file format, which makes the read/write
   roundtrip trivial. A normalized schema would require decomposing and recomposing on every read/write cycle.

2. **Application simplicity.** Beets was a solo-developer project for most of its life. A normalized schema with
   `artists`, `artist_items`, `albums`, `album_artists` tables plus proper foreign key constraints means more complex
   ORM code, more complex migration logic, more complex query generation. The flat schema made the `Item` class a
   glorified dict with dirty tracking — dead simple.

3. **Write-through semantics.** Setting `album.genre = 'Rock'` cascades to all items. With the denormalized design, you
   never need to JOIN to display an item's full metadata. For a tool where reads vastly outnumber writes, and writes
   happen in batch during import, this is a reasonable trade.

4. **SQLite's characteristics.** No concurrent writers (simpler queries release the write lock sooner), no hash joins
   (nested-loop joins make denormalized scans genuinely faster for the common case), no server process (no query cache
   warming — simpler queries perform more predictably in this cold-start model).
