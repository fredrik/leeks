# Test fixtures

Two halves that combine into a tagged test library:

- `audio/generate.py` synthesizes tiny **tagless** audio files (FLAC and MP3 sine tones), each a distinct frequency and
  a distinct duration (cycling 1, 2, 4, 8 seconds) so materialised albums carry varied track lengths.
- `corpus.toml` is the **metadata corpus** those files are tagged with.

`materialise.py` is the combiner: the test suite imports it, and `just materialise [dest]` (or running the script
directly) writes the corpus as real tagged albums for playing with `leek` by hand.

## The corpus

Everything in `corpus.toml` is fictional — invented artists, albums, and titles chosen so tests never accidentally match
real MusicBrainz data. Six artists, seven albums, twenty-nine tracks:

| Artist                                                                       | Album                                  | Tracks | Tagging                |
| ---------------------------------------------------------------------------- | -------------------------------------- | ------ | ---------------------- |
| Tin Hatch Choir                                                              | Cartography for Sleepwalkers (2019)    | 5      | clean                  |
| Tin Hatch Choir                                                              | Salt Meridian (2022)                   | 4      | clean                  |
| Vesna Holloway                                                               | Paper Lung Atlas (2017)                | 4      | clean                  |
| Polder Arcade                                                                | Tape Hiss Archipelago                  | 4      | deliberately sparse    |
| The Extraordinarily Long-Winded Orchestral Collective of Greater Scandinavia | I Wrote My Heart in Beacon Code (2021) | 3      | clean, very long names |
| Åsa Vinterhök                                                                | Vägen åter till sjön (2020)            | 5      | clean, non-ASCII       |
| Cordel Vane                                                                  | Saltmarsh Telemetry (2021)             | 4      | clean, multiple genres |

## Schema

Readable with stdlib `tomllib`. A top-level `[[albums]]` array; each album has an inline `[[albums.tracks]]` array.

Album fields: `title`, `artist`, `year`, `genre`, `tracktotal`, and `format` (optional; `"flac"` or `"mp3"`, defaults to
`"flac"`). Every track in an album materialises in that single format — a real album is one format. The corpus as a
whole exercises both FLAC and MP3 by assigning different formats across albums. `genre` is a string for one genre or a
**list** for several; a list writes one genre tag per entry, the same set onto every track. Track fields: `title`,
`track`, and an optional `artist` that overrides the album artist for that track only (tracks without it inherit the
album artist).

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

5. **Non-ASCII and typography** — *Vägen åter till sjön* by *Åsa Vinterhök* is the encoding specimen, the bug class a
   library organiser hits the moment it writes non-ASCII to a path or reads it back. The artist and album carry å/ä/ö
   onto the directory paths; each track then isolates one rendering hazard:

   1. *Förlorad i snön* is authored in **NFD (decomposed)** form — every å/ä/ö is a base letter plus a combining
      diacritic, not a precomposed codepoint (the album title, by contrast, is precomposed NFC). This is the macOS/APFS
      normalisation trap: a path written in one form reads back in another. The decomposed bytes live in `corpus.toml`
      and survive into the file tag, so the specimen is deterministic regardless of filesystem. Do not precompose it.
   2. *Vi kallade det ”hem”* uses **Swedish typographic quotes** — U+201D (right double quotation mark) on *both* sides,
      the genuine Swedish convention, not a matched `“…”` pair. It catches renderers that assume curly quotes nest.
   3. *Mörker — ljus* uses an **em dash** (U+2014) as separator, not a hyphen-minus.
   4. *Och så vidare…* ends with an **ellipsis** as one glyph (U+2026), not three full stops.
   5. *ÅTERSKEN ÖVER ÄNGEN* is all **uppercase diacritics** (Å/Ä/Ö), for casefolding and width.

   Punctuation is deliberately limited to those three marks — enough to expose the hazards without becoming a Unicode
   torture test. Do not normalise, straighten, de-accent, or ASCII-fold any of it.

6. **Multiple genres** — *Saltmarsh Telemetry* by *Cordel Vane* carries three genres (Ambient, Dub Techno, Field
   Recording), every track tagged with the identical set. Genre is the one field a source asserts as a *set*, not a
   scalar (ADR 0022): it materialises as several genre tags per file, lands as one claim per genre, and is the data
   `leek show`'s genres list exists to display. Keep all tracks' genres identical — whole-set consensus claims nothing
   when files disagree — and do not collapse the set into one delimited string.

The remaining albums are fully and cleanly tagged on purpose: they are the happy-path control group.
