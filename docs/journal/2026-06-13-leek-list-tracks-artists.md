# `leek list` learns to list tracks and artists

Session record, 2026-06-13, on the `list-tracks-artists` branch. ADR 0013 had just reopened `leek list` — albums stay
the default, but options select other first-class entities — leaving the per-subject detail "to be designed on contact,
when the slice that builds these options arrives." This is that slice, for two of the three subjects: `--tracks` and
`--artists`. Genres were not asked for and wait.

## The design

Three forks were genuinely Fredrik's to call, and two went somewhere I would not have defaulted:

- **Track row.** Track-centric — number, title, artist, album, no year — over a shelf-mirroring layout that would have
  led with artist and year. The rows are still tree-walk-ordered (grouped by album in shelf order); the columns just
  lead with the song. The artist shown is the *album* artist, the shelf the track sits on; a track's own feat. credit is
  a `leek info` detail.
- **`--artists`.** Every row of the artists table, name only — including the raw multi-artist credit strings
  (`Tin Hatch Choir feat. Vesna Holloway`) that live there until artist-credit splitting refines them. The honest view
  of what the table holds, warts shown, rather than the tidier "album artists only" with a count.
- **Terms.** They narrow every subject now, within-entity: a `--tracks` term matches the track title, a `--artists` term
  the artist name. No cross-entity reach — `--tracks "tin hatch"` finds nothing — because whether a track term reaches
  up to the album artist is exactly the question ADR 0013 deferred to the query grammar. The punt is recorded in the
  glossary's *Term* entry, the way ADR 0011's bare-term floor was.

A deliberate asymmetry falls out of the first two choices, and it is the honest one: `--artists` shows the raw feat
credit as a row, while `--tracks` shows the album artist for the very track that carries that credit. The two answer
different questions — what the artists table holds, versus the depth-first walk of the tree — and the model genuinely is
in that in-between state until credits are split.

## What was built

Two queries beside `list_albums`, same shape: one SQL statement over the merged view, terms as ANDed case-insensitive
`icontains` with autoescape, the order in the `ORDER BY`. The track order is the **tree walk** (new glossary term):
album shelf order, then `Album.id` to keep one album's tracks contiguous when two share shelf coordinates, then track
number with unnumbered last, then `Track.id`. The last key is the quiet pleasing part — `Track.id` is assembly order
(track number then source filename, `tags.assemble`), so it already *is* the filename tie-break, materialised; no file
join needed. It can diverge from on-disk destination-filename order only for unnumbered tracks, and a comment says so.

The CLI grew a shared `_emit` that carries the shape every subject prints — empty note to stderr at exit 0, one
tab-separated record per row into a pipe, the themed table only for a real tty (`isatty`, not `is_terminal`, the slice-2
lesson) — with per-subject `record` and `table` helpers. The album path moved into it unchanged, so its tests and its
scriptability contract held. Mutual exclusion is a shared `flag_value` destination; the last option wins, which is all
ADR 0013 asks for until the grammar designs explicit errors.

Tests arrived first, eighteen new across the two layers, ordering asserted as a property against the canonical shelf
order rather than a frozen sequence — the slice-2 lesson that a test which breaks on a corpus addition is a chore.

## Dogfooding

Materialised the corpus to a scratch library through the installed `leek`. The tree walk held — Tape Hiss Archipelago
led with its numbered tracks then the unnumbered pair in assembly order, Sodium before Pylon — `wc -l` counted
twenty-five track lines, and the long-named album's track stayed one greppable record (`od -c` confirmed three single
tabs, four fields). `--artists` listed all six rows with the feat credit, Åsa last. `--tracks "tin hatch"` found nothing
and said so on stderr; the feat track read as "Tin Hatch Choir". The themed tables rendered through a pseudo-tty.

## Second look

Seeing it live, Fredrik called the asymmetry what it was — inconsistent: `--artists` shows
`Tin Hatch Choir feat. Vesna Holloway` as a row, but `--tracks` showed the same track (Lowland Frequencies) under the
album artist `Tin Hatch Choir`. The root is the unsplit-credit wart — that string is a credit, not an artist, squatting
in the artists table until splitting (ADR 0009) — which the listings cannot fix, only present. Of the two ways to agree,
we took the one that hides nothing and matches the surface-it-honestly choice already made for `--artists`: `--tracks`
now shows the **effective** artist — the track's own credit when it overrides, else the album artist — while still
sorting by album artist, so the override displays under its album's shelf. The two views agree, and compilations (real
per-track artists, not just feat. strings) will surface in both. `ListedTrack.artist` became a `coalesce` over two
artist joins, the album artist aliased apart from the track artist. The same pass added `--albums` as an explicit alias
for the default, since reaching for it and getting "No such option" is a small papercut.

A last presentation pass before landing settled the columns so the three subjects read in one consistent left-to-right
order, artist first: `--albums` is artist · year · album (the track count dropped — `Listed.tracks` and its `count()`
went with it), `--tracks` is artist · album · number · title, and `--artists` is just the name.

## Open ends

`--genres` is the third subject ADR 0013 named and this slice did not build; the option mechanism is ready for it, but
genre order is still open. The cross-entity term reach and explicit mutual-exclusion errors stay deferred to the query
grammar. None of these blocks anything — the breadth view across tracks and artists is now real and dogfoodable.
