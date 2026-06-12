# Glossary

The project's terms of art, pinned. This document is **normative**: when a doc, commit message, or conversation uses one
of these words to mean something else, that is a bug — fix the usage, or change the definition here deliberately.
Coining a new term of art means adding it here in the same change.

## The data model

- **Claim** — an assertion by a source about the music: `title = "Karma Police"`, `year = 1997`. Stored verbatim as a
  `source_values` row. A claim records only what the source actually said: disagreement and absence produce no claim
  (ADR 0008).
- **Measurement** — a fact about bytes we hold, locally recomputable, with no room for disagreement: bitrate, duration
  as decoded, sha256. Lives as columns on the file row, never in the source layer (ADR 0007).
- **Source** — a named origin of claims: `file_tags` today; `musicbrainz`, `path`, `user` later. Sources are layers;
  none ever overwrites another.
- **Analyzer** — a source whose claims are heuristic inferences from bytes (BPM detection, path parsing). Its claims
  carry confidence; deterministic computation from bytes is a measurement instead (ADR 0007).
- **Source layer** — the `sources` and `source_values` tables: the preserved, per-source record of everything every
  source has claimed.
- **Merged view** — the computed "effective" library: the albums/tracks/artists/genres tables that queries, the CLI, and
  the path scheme read. Derived from claims; never authoritative over them.
- **Scalar** — a single atomic value: one string, one number, one cell of one row. Album year is scalar; an album's
  genres (a set, via junction rows) and its artist (a foreign key) are relational, not scalar. Scalars can be merged by
  assigning a winning claim; relational fields must be merged by reconciling rows — a harder, still-open problem
  deferred until the second source forces it.
- **Merged column** — a scalar column in the merged view whose value `merge()` computes from the entity's claims (album
  title and year; track title and number). Relational fields are written directly at write time and are not merged
  columns.
- **Merge** — recomputing merged columns from claims. **Identity merge** is its degenerate form while exactly one source
  exists: each claim copies through. Strategies, priorities, and confidence arrive with the second source.
- **Fallback** (or **working value**) — the value filling a NOT NULL merged column when no claim exists: the directory
  name for an album title, the file stem for a track title, `Unknown Artist` for the shelf. Never recorded as a claim
  (ADR 0008).
- **Album** — today, a row in the albums table, which is a *release* (one specific edition). The album-as-concept is the
  *release group*, which arrives with MusicBrainz (ADR 0006). When the distinction matters, say release or release
  group.
- **Entity hierarchy** — release group → release → track/recording → file (core positions), realised as its data arrives
  (ADR 0006).

## The pipeline

- **Add pipeline** — what `leek add` runs: detect → assemble → refuse re-adds → write → copy → report.
- **Detection** — validating a human's claim that one directory is one album (ADR 0004). A validator, not a clusterer.
- **Assembly** — turning per-file claims into one `AlbumInfo`: album-level fields by consensus, tracks ordered by track
  number then filename.
- **Consensus** — unanimity-or-nothing among the files that speak: if tagged files disagree on a field, no claim is
  recorded (ADR 0008). Never plurality voting.
- **Write time** — the transaction in the add pipeline that creates merged-view rows, records claims, and runs merge.
  Fallbacks are applied at write time.
- **Copy time** — the step after write time when bytes enter the library: destination paths are derived from the (just
  merged) columns, files are copied, and each copy is measured. "Paths derive from metadata at copy time" means exactly
  this moment — and never again without `leek organize`.

## On disk

- **Library** — everything under the library root: the database (`leeks.db`) and the copied audio. Owned by leeks.
- **Library root** — `$LEEKS_ROOT` or `~/Music/leeks` until `leek init` exists.
- **Original** (or **source file**) — a file outside the library that `add` copies in. Never modified, never moved.
- **The scheme** — the path derivation rule: `<Album Artist>/<Year> <Album Title>/<NN> <Title>.<ext>`, with the
  omission, bucket, replacement, and collision rules of ADR 0010.
- **Shelf** — informally, an artist's directory under the root: where their albums sit.
- **Stale path** — a library path that no longer matches what the scheme would derive from current merged metadata.
  Stale is honest; `files.path` stays true, and `leek organize` reconciles on request.

## The process

- **Slice** — one roadmap increment: small enough to implement and verify in one session, always ending runnable.
- **Punt** — the recorded interim answer to an open question, so implementation never stalls. A punt is a placeholder
  with a name, not a decision.
- **Decision record** (ADR) — a numbered file in `docs/decisions/`, started from the template, recording a decision with
  its context and alternatives. Its `Status:` line is the one mutable line of the record and moves through Proposed →
  Decided | Declined → Deprecated | Superseded.
- **Landing** — Fredrik integrating a branch into main with a single `--no-ff` merge marker (`just land`).
- **The corpus** — the fixture metadata in `tests/fixtures/corpus.toml`: fictional artists and albums with documented,
  load-bearing quirks.
- **Materialise** — write a corpus album to disk as genuinely tagged audio files (`just materialise`, or the
  `materialise` fixture in tests).
- **Harness** — the tooling that lets behaviour be verified locally and fast; grown whenever a feedback loop feels slow
  or blind.
- **Verb** — a top-level `leek` command; the unit of user interface, curated in [verbs](verbs.md).
