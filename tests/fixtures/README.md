# Test fixtures

Two halves that combine into a tagged test library:

- `audio/generate.py` synthesizes tiny **tagless** audio files (FLAC and MP3 sine tones).
- `corpus.toml` is the **metadata corpus** those files are tagged with.

`materialise.py` is the combiner: the test suite imports it, and `just materialise [dest]` (or running the script
directly) writes the corpus as real tagged albums for playing with `leek` by hand.

## The corpus

Everything in `corpus.toml` is fictional — invented artists, albums, and titles chosen so tests never accidentally match
real MusicBrainz data. Four artists, five albums, twenty tracks:

| Artist                                                                       | Album                                  | Tracks | Tagging                |
| ---------------------------------------------------------------------------- | -------------------------------------- | ------ | ---------------------- |
| Tin Hatch Choir                                                              | Cartography for Sleepwalkers (2019)    | 5      | clean                  |
| Tin Hatch Choir                                                              | Salt Meridian (2022)                   | 4      | clean                  |
| Vesna Holloway                                                               | Paper Lung Atlas (2017)                | 4      | clean                  |
| Polder Arcade                                                                | Tape Hiss Archipelago                  | 4      | deliberately sparse    |
| The Extraordinarily Long-Winded Orchestral Collective of Greater Scandinavia | I Wrote My Heart in Beacon Code (2021) | 3      | clean, very long names |

## Schema

Readable with stdlib `tomllib`. A top-level `[[albums]]` array; each album has an inline `[[albums.tracks]]` array.

Album fields: `title`, `artist`, `year`, `genre`, `tracktotal`. Track fields: `title`, `track`, and an optional `artist`
that overrides the album artist for that track only (tracks without it inherit the album artist).

Sparse fields are **omitted entirely** — never present as empty strings. Consumers should treat a missing key as "this
tag is absent from the file".

## Deliberate quirks — do not "fix" these

The corpus exists to exercise the import pipeline's edge cases. Each quirk below is load-bearing; tests depend on it.

1. **Raw multi-artist credit** — *Lowland Frequencies* on *Salt Meridian* carries
   `artist = "Tin Hatch Choir feat. Vesna Holloway"`: a single raw string, exactly as a real file tag would hold it. It
   exercises artist-credit splitting. Do not normalise it into structured fields.
2. **Sparse album** — *Tape Hiss Archipelago* has no `year`, no `genre`, no `tracktotal`, and two tracks (*Sodium Light
   Study*, *Pylon Hum*) without `track` numbers. It represents the badly-tagged music a library organiser most needs to
   handle. Do not complete the missing fields.
3. **Duplicate track title** — *Glass Harbour* appears on both *Cartography for Sleepwalkers* and *Paper Lung Atlas*.
   Same title string, different songs. It exercises title-based matching that must not assume titles are unique. Do not
   rename either one.
4. **Extravagantly long strings** — *I Wrote My Heart in Beacon Code* by *The Extraordinarily Long-Winded Orchestral
   Collective of Greater Scandinavia* has a deliberately enormous artist name, a long album title, and long track titles
   — one (*I Couldn't Compete with the Fog*) carrying a curly apostrophe. It exercises text wrapping, truncation, and
   Unicode width in any human-facing output. Do not shorten the names or straighten the apostrophe.

The remaining albums are fully and cleanly tagged on purpose: they are the happy-path control group.
