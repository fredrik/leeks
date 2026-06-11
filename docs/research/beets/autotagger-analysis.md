# Autotagger Isolation Analysis

The beets autotagger is ~550 lines across 3 files. It's tightly coupled to beets internals, but the **actual
algorithms** are surprisingly self-contained. Here's the decomposition:

## Component 1: String Distance (~70 lines)

**`distance.py:49-121`** — Completely isolatable.

- **Dependencies:** `jellyfish.levenshtein_distance`, `unidecode`
- **Algorithm:** Normalized Levenshtein with semantic adjustments:
  - Article relocation ("title, the" → "the title")
  - `&` → `and` normalization
  - Weighted pattern stripping (parentheticals ×0.3, feat. ×0.1, EP/single ×0.0, part markers ×0.2)
- **Isolation effort:** Trivial. Copy `_string_dist_basic()` + `string_dist()`, add two deps.

## Component 2: Distance Accumulator (~240 lines)

**`distance.py:124-368`** — The `Distance` class.

- **Beets coupling:** Only `config["match"]["distance_weights"]` — a dict of `{str: float}`
- **What it does:** Accumulates named penalties (0.0–1.0 each), weights them, normalizes to a single 0.0–1.0 score
- **Key insight:** This is just a **weighted scoring framework**. The penalty methods (`add`, `add_string`,
  `add_equality`, `add_ratio`, `add_number`, `add_priority`, `add_expr`) are generic.
- **Isolation effort:** Easy. Replace `config` access with a plain dict passed at construction.

## Component 3: Track Distance (~45 lines)

**`distance.py:395-440`** — `track_distance()`.

Compares one local item vs one candidate track on 7 dimensions:

| Dimension       | Method                     | Weight (default) |
| --------------- | -------------------------- | ---------------- |
| track_length    | ratio (grace=10s, max=30s) | 2.0              |
| track_title     | string_dist                | 3.0              |
| track_artist    | string_dist (VA-aware)     | 2.0              |
| track_index     | exact match                | 1.0              |
| track_id (MBID) | exact match                | 5.0              |
| medium (disc#)  | exact match                | 1.0              |
| data_source     | plugin penalty             | 2.0              |

**Coupling:** Reads from beets `Item` model (`.title`, `.artist`, `.length`, `.track`, `.disc`, `.mb_trackid`). Needs an
interface/protocol, not the actual `Item` class.

## Component 4: Album Distance (~100 lines)

**`distance.py:443-556`** — `distance()`.

Compares local items (as a group) vs one candidate album on 11 dimensions plus per-track distances:

| Dimension            | Weight |
| -------------------- | ------ |
| artist               | 3.0    |
| album                | 3.0    |
| media                | 1.0    |
| mediums (disc count) | 1.0    |
| year                 | 1.0    |
| country              | 0.5    |
| label                | 0.5    |
| catalognum           | 0.5    |
| albumdisambig        | 0.5    |
| album_id (MBID)      | 5.0    |
| tracks (aggregate)   | 2.0    |
| missing_tracks       | 0.9    |
| unmatched_tracks     | 0.6    |
| data_source          | 2.0    |

**Coupling:** Uses `get_most_common_tags(items)` to extract consensus metadata from local files. Uses
`config["match"]["preferred"]` for media/country/year preferences.

## Component 5: LAP Assignment (~30 lines)

**`match.py:75-104`** — `assign_items()`.

- **Dependencies:** `lap` (Jonker-Volgenant solver), `numpy`
- **Algorithm:** Build M×N cost matrix of `track_distance()` values, solve with `lap.lapjv(extend_cost=True)` for
  non-square matrices
- **Returns:** `(matched_pairs, extra_items, extra_tracks)`
- **Isolation effort:** Trivial. The function is already self-contained — just needs `track_distance()`.

## Component 6: Candidate Evaluation & Ranking (~100 lines)

**`match.py:124-325`** — `_recommendation()`, `_add_candidate()`, `tag_album()`.

- `_add_candidate()`: filters (no tracks, duplicates, required tags), calls `assign_items()` + `distance()`, stores
  result
- `_recommendation()`: threshold-based (strong < 0.04, medium < 0.25, gap ≥ 0.25) with per-penalty max-rec downgrades
- `tag_album()`: orchestrates ID-based search → metadata search → candidate evaluation → sort → recommend

**Coupling:** `metadata_plugins.candidates()` (the metadata source interface), `config["import"]["timid"]`,
`config["match"]` thresholds.

______________________________________________________________________

## Isolation Plan

### Phase 1: Pure Algorithm Library (no beets deps)

Create a standalone `teebs.autotag` package with:

```
teebs/autotag/
    __init__.py
    similarity.py    # string_dist (from distance.py:49-121)
    scoring.py       # Distance class + track_distance + album_distance
    assignment.py    # LAP solver wrapper (assign_items)
    ranking.py       # recommendation + candidate evaluation
    types.py         # Protocol classes / Pydantic models for inputs
```

**Key design decisions:**

1. **Use Protocols instead of beets Item/AlbumInfo.** Define what the matcher *needs*:

   ```python
   class LocalTrack(Protocol):
       title: str
       artist: str
       length: float
       track: int | None
       disc: int | None
       mb_trackid: str | None
   ```

   Your teebs `TrackInfo` Pydantic model already satisfies most of this.

1. **Weights as a dataclass, not config.** Replace all `config["match"]` reads with a `MatchConfig` object:

   ```python
   @dataclass
   class MatchConfig:
       distance_weights: dict[str, float]  # 20 keys
       strong_rec_thresh: float = 0.04
       medium_rec_thresh: float = 0.25
       rec_gap_thresh: float = 0.25
       track_length_grace: float = 10.0
       track_length_max: float = 30.0
       preferred_media: list[str] = field(default_factory=list)
       preferred_countries: list[str] = field(default_factory=list)
       preferred_original_year: bool = False
       required: list[str] = field(default_factory=list)
       ignored: list[str] = field(default_factory=list)
   ```

1. **Candidate source as a callable.** Instead of `metadata_plugins.candidates()`:

   ```python
   CandidateSource = Callable[[str, str, bool], Iterable[AlbumCandidate]]
   ```

   MusicBrainz, Discogs, etc. each implement this interface.

1. **Drop `data_source` penalty** initially. With a single source (MusicBrainz), it's irrelevant.

### Phase 2: Adapt to teebs Data Model

Map between your Pydantic models and the matcher's Protocol types:

| Beets concept            | teebs equivalent                                           |
| ------------------------ | ---------------------------------------------------------- |
| `Item.artist` (string)   | `item.artist_credits[0].name` or `display_artist()`        |
| `Item.mb_trackid`        | `item.external_ids.get("musicbrainz:recording")`           |
| `Item.mb_albumid`        | `album.external_ids.get("musicbrainz:release")`            |
| `AlbumInfo.va` (bool)    | `album.comp` or detect from artist_credits                 |
| `get_most_common_tags()` | New utility that extracts consensus from `list[TrackInfo]` |

### Phase 3: MusicBrainz Integration

Implement the `CandidateSource` callable for MusicBrainz. This is the **other** hard part — beets' MB plugin handles
rate limiting, release group dedup, multi-format releases, etc. But that's a separate concern from the matching
algorithm.

______________________________________________________________________

## Dependency Budget

| Dep         | Purpose                         | Size                    |
| ----------- | ------------------------------- | ----------------------- |
| `jellyfish` | Levenshtein distance            | Tiny C extension        |
| `unidecode` | Unicode → ASCII transliteration | ~1MB data               |
| `lap`       | Jonker-Volgenant LAP solver     | Small C extension       |
| `numpy`     | Cost matrix for LAP             | Already needed by `lap` |

All four are pure algorithm libraries with no framework coupling.

______________________________________________________________________

## What You Can Skip

- **`AttrDict` / `Info` base class** — beets' dict-as-object pattern. Your Pydantic models are better.
- **`correct_list_fields()`** — beets legacy for syncing scalar/list artist fields. Your normalized artist model doesn't
  need it.
- **`MEDIA_FIELD_MAP`** — field renaming between beets' internal and MediaFile names. Irrelevant with a clean data
  model.
- **Plugin event hooks** (`plugins.send("album_matched")`) — add later when you have a plugin system.
- **Color/display formatting** on Distance — UI concern, not algorithm.
