# Slice 2: `leek list --tracks` and `--artists`

ADR 0013 reopened `leek list`: albums stay the default subject, but options select other first-class entities. This plan
builds two of the three — `--tracks` and `--artists` (genres deferred until asked for). It is the read side only: two
new queries and CLI dispatch, no schema change. ADR 0013 left the per-subject detail to be "designed on contact"; this
plan is that contact, and settles it.

## Decisions

- **Track row is track-centric**: `# · title · artist · album`, no year. `artist` is the *album* artist — the shelf the
  track sits on; a track's own feat. credit is a `leek info` detail, not shown here.
- **`--artists` lists every artist row**, name only, case-folded — raw multi-artist credit strings (`… feat. …`)
  included, shown honestly as the unsplit data they are until artist-credit splitting refines them.
- **Terms narrow every subject, within-entity**: a `--tracks` term matches the track title, a `--artists` term the
  artist name. No cross-entity reach (a `--tracks` term does not reach the album artist) — deferred to the query grammar
  (ADRs 0012, 0013); the punt is recorded in the glossary's *Term* entry.
- A deliberate asymmetry: `--artists` surfaces the raw feat-credit row, while `--tracks` shows the album artist for that
  same track. They answer different questions — what the artists table holds vs. the tree walk — and both are honest
  about today's model.

## Verification

New behaviour, new tests, before the behaviour:

- `tests/test_list.py` — the query layer (`library.list_tracks`, `library.list_artists`):
  - an empty library lists no tracks and no artists;
  - the whole corpus's tracks come back grouped by album in exactly `list_albums`'s shelf order — the tree walk asserted
    as a property against the canonical order, not a frozen snapshot, so corpus growth never breaks it;
  - within Tape Hiss Archipelago, numbered tracks precede unnumbered, and the unnumbered pair holds assembly order
    (Sodium before Pylon — source filename, the tie-break `Track.id` carries);
  - the duplicate title "Glass Harbour" yields two distinct rows under their two albums; the feat track shows album
    artist "Tin Hatch Choir", not the credit string;
  - track terms match the title, are case-insensitive, treat LIKE metacharacters as literal, and do *not* reach the
    album artist (`tin hatch` finds no tracks);
  - artists are every row including the feat credit, in case-folded name order (Åsa after the ASCII names); an
    artistless album contributes no artist row; artist terms match the name (a substring reaches into the raw credit
    too).
- `tests/test_cli_list.py` — the surface:
  - `--tracks` prints one self-contained tab record per track (number/title/artist/album); the long-named album stays
    one greppable line, and `FORCE_COLOR=1` does not wrap it;
  - `--artists` prints one name per line;
  - empty-library and no-match notes go to stderr, exit 0, stdout clean, worded per subject;
  - `--tracks`/`--artists` are mutually exclusive (last wins); the options appear in `leek list --help`.
- `just check` green at every commit; dogfood against a materialised scratch library through the installed `leek`.

## Build

1. **The queries** — `library.list_tracks(terms) -> list[ListedTrack]` and
   `library.list_artists(terms) -> list[ListedArtist]`, beside `list_albums`. Tracks: `Track ⨝ Album ⟕ Artist` (album
   artist), tree-walk `ORDER BY` (shelf columns, `Album.id` for contiguity, track number NULLs-last, `Track.id`); terms
   as ANDed `Track.title.icontains`. Artists: `select(Artist)` ordered by name NOCASE; terms as ANDed
   `Artist.name.icontains`. Frozen dataclasses like `Listed`.
2. **The verb** — `leek list` gains mutually-exclusive `--tracks`/`--artists` via a shared `flag_value` destination
   (default albums) and dispatches. A shared `_emit` carries the empty-note-to-stderr / `isatty`→tab-records /
   tty→themed-table shape (lifted from the album path, unchanged); per-subject `record` and `table` helpers supply the
   fields and the themed columns. Unknown Artist still renders dim italic, shared between the album and track tables.
3. **Docs** — glossary extends *Term* and gains *Tree walk*; verbs.md's query open-question updated; this plan archives;
   journal entry.

## Punts

- **`--genres`** — ADR 0013's third subject, not asked for. The option mechanism and `_emit` accommodate it; genre order
  is still open.
- **Cross-entity term reach** (does `--tracks foo` match the album artist?) and **explicit mutual-exclusion errors** —
  deferred to the query grammar (ADRs 0012, 0013). Today a `--tracks` term matches the title only, and the last subject
  option on the line wins.
- **No new ADR** — ADR 0013 anticipated this contact-time design living in the slice plan; the decisions above are
  recorded here, in the glossary, and in the journal.
