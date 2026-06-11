# Autotagger Extraction Plan

Port beets' autotagger into teebs as an isolated module. Reuse the algorithms, weights, and heuristics — not redesigning
the scoring.

## What we're taking from beets

| Component              | Source                | ~Lines | Deps                  |
| ---------------------- | --------------------- | ------ | --------------------- |
| `Distance` class       | `autotag/distance.py` | 250    | none                  |
| `string_dist()`        | `autotag/distance.py` | 55     | jellyfish, unidecode  |
| `track_distance()`     | `autotag/distance.py` | 45     | Distance, string_dist |
| `distance()` (album)   | `autotag/distance.py` | 110    | all above             |
| `assign_items()` (LAP) | `autotag/match.py`    | 30     | lap, numpy            |
| `_recommendation()`    | `autotag/match.py`    | 55     | none                  |
| Default weights        | `config_default.yaml` | 20     | none                  |

Total: ~565 lines of logic, 4 external deps (jellyfish, unidecode, lap, numpy).

## What changes for teebs

### Data model differences

Beets' autotagger operates on `Item` (ORM) and `TrackInfo`/`AlbumInfo` (dict-like objects from `hooks.py`). Teebs uses
Pydantic models with normalized artists and generic external IDs.

Key mismatches:

| Beets field              | Teebs equivalent                                     |
| ------------------------ | ---------------------------------------------------- |
| `item.artist` (str)      | `item.artists[0].name` (via ArtistRef)               |
| `item.mb_trackid`        | `item.external_ids.get("musicbrainz:recording")`     |
| `info.va` (bool)         | `info.comp` (bool)                                   |
| `info.artist` (str)      | `info.artists` (list[ArtistRef])                     |
| `info.album` (str)       | `info.title` (str)                                   |
| `info.album_id` (str)    | `info.external_ids.get("musicbrainz:release")`       |
| `info.track_id` (str)    | `info.external_ids.get("musicbrainz:recording")`     |
| `info.data_source` (str) | not modeled yet — needs adding or passing separately |

### Approach: protocol-based input

Don't couple to teebs' Pydantic models directly. Define minimal protocols (or just use the Pydantic models as-is since
they have the right fields).

The distance functions need access to a small surface:

**For track comparison:**

- title: str
- length: float | None
- artist name: str (flattened from artists list)
- track number: int | None
- disc number: int | None
- track_id: str | None (from external_ids)

**For album comparison:**

- title: str (beets calls this `album`)
- artist name: str (flattened)
- year: int | None
- country, label, catalognum, albumdisambig: str
- media: str
- disctotal: int | None
- comp: bool
- album_id: str | None (from external_ids)
- data_source: str

Helper function `display_artist(artists: list[ArtistRef]) -> str` bridges the gap.

## Module structure

```
teebs/autotag/
    __init__.py          # public API: tag_album, tag_item, Recommendation
    distance.py          # Distance class, string_dist, track_distance, album_distance
    match.py             # assign_items (LAP), recommendation, tag_album, tag_item
    weights.py           # default weight dict, VA_ARTISTS, thresholds
```

Four files. No config system yet — just a dict of weights with beets' defaults hardcoded. Config integration comes
later.

## Implementation steps

### 1. `weights.py` — constants

Copy beets' default distance weights, thresholds (strong=0.04, medium=0.25, gap=0.25), max_rec downgrades, and
VA_ARTISTS list.

~30 lines.

### 2. `distance.py` — scoring engine

Port the `Distance` class and all distance functions. Changes from beets:

- Remove dependency on beets `config` — take weights as a dict parameter (default to the beets defaults from
  weights.py).
- `string_dist()` is pure, copy as-is.
- `track_distance()` takes two objects with the track-level fields above. Use `display_artist()` to flatten artist
  lists.
- `album_distance()` (renamed from `distance()`) takes album-level fields plus the LAP-assigned pairs.
- Access external IDs via `external_ids.get(key)` instead of dedicated `mb_*` attributes.
- Drop `data_source` penalty logic initially (or keep it simple — penalty if source != preferred source).

~350 lines.

### 3. `match.py` — orchestration

Port `assign_items()`, `_recommendation()`, and the top-level `tag_album()` / `tag_item()` flows. Changes:

- `assign_items()` is nearly pure — just needs track_distance to build cost matrix. Minimal changes.
- `_recommendation()` is pure threshold logic, copy as-is.
- `tag_album()` simplification: remove the beets plugin system iteration. Instead, accept an iterable of candidates
  (AlbumInfo objects from whatever source). The caller is responsible for fetching candidates. This decouples the
  autotagger from metadata source plugins entirely.

Signature:

```python
def tag_album(
    items: Sequence[TrackInfo],
    candidates: Iterable[AlbumInfo],
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> Proposal:
```

~150 lines.

### 4. Metadata source interface

NOT part of the autotagger module. Define a protocol elsewhere:

```python
class MetadataSource(Protocol):
    def search_albums(
        self, artist: str, album: str, va: bool
    ) -> Iterator[AlbumInfo]: ...

    def search_tracks(
        self, artist: str, title: str
    ) -> Iterator[TrackInfo]: ...

    def album_by_id(self, id: str) -> AlbumInfo | None: ...
```

The import pipeline calls sources, collects candidates, passes them to `tag_album()`. Clean separation.

## What we're NOT porting

- Beets' config system integration (we pass dicts)
- Beets' plugin event hooks (`distances` listener that lets plugins modify scores)
- `preferred` media/country/original_year logic (can add later)
- The importer UI/interaction (separate concern)
- Singleton/track-level matching (port `tag_item` later, album-first)

## Dependencies to add

```
jellyfish >= 1.0
unidecode >= 1.3
lap >= 0.5.12
numpy >= 1.24
```

## Open questions

- ~~`data_source` field~~ **Resolved:** added `data_source: str = ""` to both Pydantic models (TrackInfo, AlbumInfo) and
  both ORM models (ItemORM, AlbumORM). Set by metadata sources on fetch, used in scoring, persisted to DB.
- **Config integration:** When teebs gets a config system, weights should be user-configurable. For now, hardcoded
  defaults are fine.
- **Penalty extensibility:** Beets lets plugins add custom distance penalties via the `distances` event. Do we need
  this? Probably not initially — keep it closed, open it when there's a real use case.
