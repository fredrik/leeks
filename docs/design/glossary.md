# Glossary

The project's terms of art, pinned. This document is **normative**: when a doc, commit message, or conversation uses one
of these words to mean something else, that is a bug — fix the usage, or change the definition here deliberately.
Coining a new term of art means adding it here in the same change.

## The data model

- **Claim** — an assertion by a source about the music: `title = "Karma Police"`, `year = 1997`. Stored verbatim as a
  `source_values` row. A claim records only what the source actually said: disagreement and absence produce no claim
  (ADR 0008). Most fields are single-valued, but a field may be **set-valued** — genre, today — and a source then claims
  each value as its own row (ADR 0022). The schema enforces the difference: single-valued fields get one row per source,
  set-valued fields may repeat (ADR 0025).
- **Claim field** — a field a source can claim, declared once in the registry (`leeks/fields.py`) with its arity, the
  pipeline-model attribute it reads from, and its cast when it is a merged column. The write path, the merged columns,
  and the schema's arity enforcement all read from this one declaration (ADR 0025). Distinct from the display namespace
  `leek fields` exposes, which is a different list.
- **Measurement** — a fact about bytes we hold, locally recomputable, with no room for disagreement: bitrate, duration
  as decoded, sha256. Lives as columns on the file row, never in the source layer (ADR 0007).
- **Encoding** vs **medium** — two senses of the loose word "format", kept apart (ADR 0033). The **encoding**
  (FLAC/MP3/V0) is how the bytes are stored: a measurement, read from the file, never a claim. The **medium** (vinyl,
  CD, cassette — what MusicBrainz calls a release's format) is the release's physical form, which the bytes cannot
  reveal: a claim, asserted by a source like the path.
- **Source** — a named origin of claims: `file_tags` and `path` today; `musicbrainz`, `user` later. Each carries a
  **priority** that resolves the merge (ADR 0031); sources are layers, none ever overwrites another.
- **Analyzer** — a source whose claims are heuristic inferences from bytes (BPM detection, path parsing). Its claims
  carry confidence; deterministic computation from bytes is a measurement instead (ADR 0007).
- **Source layer** — the `sources` and `source_values` tables: the preserved, per-source record of everything every
  source has claimed.
- **Merged view** — the computed "effective" library: the albums/tracks/artists/genres tables that queries, the CLI, and
  the path scheme read. Derived from claims; never authoritative over them.
- **Scalar** — a single atomic value: one string, one number, one cell of one row. Album year is scalar; an album's
  genres (a set, via junction rows) and its artist (a foreign key) are relational, not scalar. Scalars are merged by
  assigning a winning claim (ADR 0031); relational fields are merged by reconciling the winning claim to a row. The
  artist foreign key does this now (ADR 0032); genre, a junction, waits for a second source to claim it.
- **Merged column** — a scalar column in the merged view whose value `merge()` computes from the entity's claims (album
  title, year, and medium; track title and number). A field earns one when a reader consumes it: medium became a merged
  column when `leek show` displayed it, while region and catalogue stay claim-only until a reader of their own (ADR
  0033/0034). A relational field is not a merged column: the artist foreign key is resolved by `merge()` to a row (ADR
  0032), and genre is still linked at write time until a source other than file_tags claims it.
- **Merge** — recomputing merged columns from claims: each column takes the value of the highest-priority source that
  claims it (ADR 0031). **Identity merge** is the degenerate case where one source claims a field — the value copies
  through. Claim **confidence** is recorded but does not yet enter resolution; richer strategies and the review queue
  arrive with the sources that force them.
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
  recorded (ADR 0008). Never plurality voting. For a set-valued field (genre), unanimity is on the whole set — the files
  must carry the identical set, else nothing (ADR 0022); union is the deferred, truer rule.
- **Write time** — the transaction in the add pipeline that creates merged-view rows, records claims, and runs merge.
  Fallbacks are applied at write time.
- **Copy time** — the step after write time when bytes enter the library: destination paths are derived from the (just
  merged) columns, files are copied, and each copy is measured. "Paths derive from metadata at copy time" means exactly
  this moment — and never again without `leek organize`.
- **Term** — one word of a `leek list` or `leek show` query, of the form `[field:]value`. Terms AND together and match
  case-insensitively, folding accents (ADR 0021), against data only — never display fallbacks (ADR 0011). A **bare**
  term substring-matches the subject's descriptive fields, reaching up the tree over the real foreign keys (ADR 0029):
  an album by its artist, title, or year; a track by its title and its album's artist and title; an artist by its name.
  A **qualified** `field:value` matches the one named field, drawn from the subject's namespace — the names
  `leek fields` lists and `--fields` selects; usually a substring, but a *membership* test for a set-valued field
  (`genre:`/`genres:` on an album, ADR 0023). `id:N` is the lone exact selector, naming one row by primary key (ADR
  0020). The reach is a query-time join, never denormalised storage (ADR 0029).

## On disk

- **Library** — everything under the library root: the database (`leeks.db`) and the copied audio. Owned by leeks.
- **Library root** — `$LEEKS_ROOT` or `~/Music/leeks` until `leek init` exists.
- **Original** (or **source file**) — a file outside the library that `add` copies in. Never modified, never moved.
- **The scheme** — the path derivation rule: `<Album Artist>/<Year> <Album Title>/<NN> <Title>.<ext>`, with the
  omission, bucket, replacement, and collision rules of ADR 0010.
- **Shelf** — informally, an artist's directory under the root: where their albums sit.
- **Shelf order** — artist (case-folded, Unknown Artist under U), then year with missing years last, then title: the
  order of the library tree and of `leek list` (ADR 0011). The listing and the tree never disagree.
- **Tree walk** — the order of `leek list --tracks`: shelf order by album, then within an album track number (unnumbered
  last), then assembly order — track number then filename, the tie-break `Track.id` already carries (assembly). A track
  listing thus reads as a depth-first walk of the library tree, extending shelf order's "the listing and the tree never
  disagree" to tracks (ADR 0013).
- **Stale path** — a library path that no longer matches what the scheme would derive from current merged metadata.
  Stale is honest; `files.path` stays true, and `leek organize` reconciles on request.

## The process

- **Effort** — a bounded push toward one goal: the unit of work we plan, branch, and land. One effort lives on one
  branch and one branch carries one effort — the terms are two views of the same thing, so "which branch?" and "which
  effort?" are the same question. Agnostic to kind: a feature, a fix, a doc pass, and a fixture addition are all
  efforts.
- **Slice** — one roadmap increment: small enough to implement and verify in one session, always ending runnable.
- **Punt** — the recorded interim answer to an open question, so implementation never stalls. A punt is a placeholder
  with a name, not a decision.
- **Decision record** (ADR) — a numbered file in `docs/decisions/`, started from the template, recording a decision with
  its context and alternatives. Its `Status:` line is the one mutable line of the record and moves through Proposed →
  Decided | Declined → Deprecated | Superseded.
- **Landing** — Fredrik integrating an effort into main with a single `--no-ff` merge marker (`just land`).
- **The corpus** — the fixture metadata in `tests/fixtures/corpus.toml`: fictional artists and albums with documented,
  load-bearing quirks.
- **Materialise** — write a corpus album to disk as genuinely tagged audio files (`just materialise`, or the
  `materialise` fixture in tests).
- **Harness** — the tooling that lets behaviour be verified locally and fast; grown whenever a feedback loop feels slow
  or blind.
- **Verb** — a top-level `leek` command; the unit of user interface, curated in [verbs](verbs.md).
