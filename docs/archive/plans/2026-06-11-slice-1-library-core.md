# Slice 1: Library core — `leek add` (high level)

Music enters the database. This pass states intent, scope, verification, and the punts; the implementation map lives in
[the detail plan](2026-06-11-slice-1-library-core-detail.md).

## Intent

`leek add <dir>` ingests exactly one album (ADR 0004), non-interactively, recording what it knows. The write path goes
through the source layer from day one — file tags write `source_values` rows as the claims of the `file_tags` source,
and the merged view is computed from them, even though "computed" is an identity copy while file tags are the only
source. The discipline is the hard-to-retrofit part; the cleverness is not.

## Scope

In: the merged-view core for what file tags can populate — albums (releases), tracks, files, artists, genres — plus the
source layer (`sources`, `source_values`), the first Alembic migration, tag reading via mediafile, strict single-album
detection, copy-on-import, and the `leek add` command with output worth reading.

Out, per ADR 0006 and data availability: release groups, recordings, works (arrive with MusicBrainz), merge machinery,
confidence, pending changes and review (arrive with the second source), `source_matches`, tag write-back, path
templates, `leek import`. The change log also waits: slice 1 only ever creates — nothing is overwritten, so prior states
are trivially reconstructible — and the log machinery arrives with the first mutation that changes existing values.

## Verification

Verification leads; code follows. The fixture corpus (tagless FLAC/MP3 tones + `corpus.toml`) is already on this branch.
The slice's first build step combines them: a test harness that materialises any corpus album as a directory of
genuinely tagged audio files. Every pipeline behaviour is then asserted end-to-end through `leek add` against fixture
albums:

- Clean album: all rows present and consistent across files, tracks, albums, artists, `source_values`; originals
  untouched (byte-identical after import); copies exist under the library root; measurements populated.
- Sparse album (the corpus's *Tape Hiss Archipelago*): absent tags mean absent claims and NULL columns — never empty
  strings, never blocked ingestion.
- The raw multi-artist credit and the duplicate track title behave per the punts below.
- Strict detection refuses a directory that looks like several albums, naming what it saw.
- Re-running `add` on the same source refuses per the punt below, leaving the database unchanged.

`just check` green is the bar throughout, not at the end.

## Build order

1. Fixture harness — corpus loader and album materialiser (tag the tones from `corpus.toml`).
2. Schema — ORM models and Alembic migration 0001, with the database created at the library root.
3. Pipeline models — slice-sized `AlbumInfo` / `TrackInfo` (ADR 0001: Pydantic in the pipeline, ORM at rest).
4. Tag reading — mediafile → pipeline models; claims separated from measurements (ADR 0007).
5. Detection — the single-album validator (ADR 0004).
6. Write path — source_values, identity merge, copy-on-import, all in one transactional pipeline.
7. CLI — `leek add` wired through click, with a summary card that earns the joy requirement.
8. Docs — journal entry; archive this plan.

## Punts

Each open question gets an interim answer so implementation never stalls (project principle):

- **Re-add**: refuse when any of the directory's files match a known source path — "already added". Hashes and `--force`
  come with the real disambiguation design (ADR 0004 notes it).
- **Artists from raw strings**: one artist row per raw credit string, whole and unparsed ("Tin Hatch Choir feat. Vesna
  Holloway" is one artist for now). MusicBrainz refines credits in the matcher slice.
- **Library root**: hardcoded `~/Music/leeks`, overridable by one environment variable so tests can point elsewhere.
  Real configuration arrives when a second consumer needs it.
- **Copy layout**: dumb and stable, `album-<id>/<track>-<title>` under the root; `leek organize` renames later.
- **Singletons**: undecided in teebs, still undecided; excluded. `add` is single-album, so every track has an album —
  `tracks.album_id` is NOT NULL until singletons are designed.
- **Multi-disc albums**: the corpus has none, so the slice builds none. When a multi-disc fixture album joins the
  corpus, disc handling joins the schema.
