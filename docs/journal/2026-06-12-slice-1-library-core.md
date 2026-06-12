# Slice 1: music enters the database

Session record, 2026-06-11 to 2026-06-12. The slice was talked through before it was planned, planned in two passes
before it was built, and built verification-first on the `leek-add` branch. Four ADRs and a fixture corpus came out of
the design conversation; the slice itself landed as seven implementation commits, each leaving `just check` green.

## The design conversation

The slice began as a discussion of what slice 1 *wants to be*, which produced decisions that outlive it:

- **ADR 0004** — `leek add` ingests exactly one album, non-interactively. Fredrik's decision; it turned the album-birth
  heuristic from a clusterer into a validator of a human's claim.
- **ADR 0005** — `leek import` ingests a set of albums and owns album-boundary detection. First drafted as "and is
  interactive"; reworked when Fredrik observed the durable decision is the scope, not the interaction model.
- **ADR 0006** — the entity hierarchy is realised as its data arrives. Resolved an apparent contradiction between
  core-positions ("all four are modelled", never-violate) and the roadmap (release groups arrive with MusicBrainz);
  core-positions gained its anchoring sentence.
- **ADR 0007** — the source layer stores claims, not measurements. Refined twice in conversation: measurements attach to
  byte-sets (album ReplayGain, later, is a set-level measurement), and computed-from-bytes is not sufficient — heuristic
  analysis (BPM detection) is a claim by an analyzer source.

## What was built

The fixture corpus came first (landed separately as `Add basic fixtures`): a generator for tagless FLAC/MP3 tones plus
`corpus.toml` — three fictional artists, four albums, seventeen tracks, with documented load-bearing quirks. The slice
then followed the plan's build order:

| Step       | What                                                                                              |
| ---------- | ------------------------------------------------------------------------------------------------- |
| Harness    | `materialise` combines tones with corpus metadata into genuinely tagged albums                    |
| Schema     | Nine tables; migration 0001 hand-written, held in lockstep with the ORM by a parity test          |
| Models     | `AlbumInfo`/`TrackInfo` carry claims only; `FileFacts` carries measurements, separately           |
| Tags       | mediafile reading; assembly by consensus, per-track artist only as override                       |
| Detect     | The single-album validator; refusals name what they saw and point at `leek import`                |
| Write path | Claims → `source_values`, merged columns through the `merge()` seam, copy-on-import with rollback |
| CLI        | `leek add` with a summary card; refusals as clean errors                                          |

Verified end to end through the installed `leek` binary against a materialised album: card printed, re-add refused,
copies laid out as `album-1/01-meridian-line.flac`, fourteen claims in `source_values`.

## Judgement calls the plan did not dictate

- NOT NULL fallbacks (directory name for album title, file stem for track title) are applied to merged columns at write
  time and are **never recorded as claims** — the claim layer stays honest.
- `assemble` lifts the artist to album level by consensus (albumartist tags first, unanimous artist tags second);
  per-track artist claims exist only as overrides.
- Conflicting album-level tags (e.g. two different years) yield **no claim** rather than a guess: consensus means
  unanimity among the files that speak.
- Track ordering is track-number-then-filename with unnumbered tracks last, read literally from the plan; the sparse
  album therefore orders 1, 4, then the unnumbered pair by filename.
- Constraint names follow a SQLAlchemy naming convention from day one, so future SQLite batch migrations can refer to
  them.
- The Alembic environment lives at `src/leeks/migrations/`, not the plan's root-level `migrations/` — a deliberate
  deviation: package-local migrations survive leeks shipping as a wheel; a repo-root directory does not.

## The parity twin

As an experiment in documentation sufficiency, a zero-context agent implemented the same two plan documents
independently (branch `leek-add-plan`), and each side reviewed the other. The designs converged almost line for line —
module names, schema, the merge() seam, even the commit shape — confirming the documents carried the design. The
divergences clustered exactly where the plan was ambiguous or silent, and both reviews recommended landing this branch
and porting the twin's diffs, which was done: foreign-key enforcement (the twin's catch — SQLite defaults it off), a
copy-failure rollback test (the twin treated the plan's test list as a floor; this side had anchored on it as a spec),
enum CHECK constraints, lazy CLI imports, and named re-add refusals.

The experiment exposed two genuine design forks — untagged-album handling and consensus semantics — both documentation
holes: the rules had lived only in conversation. Fredrik ruled on both (this branch's behaviour stands: fallbacks are
never claims, consensus is unanimity-or-nothing) and added a third decision the discussion surfaced: the path is a
source — directory names like `The Avalanches - Since I Left You (2001) [FLAC] {...}` carry release-level metadata that
enters as analyzer claims once merge machinery can host a second source. All three are recorded as
[ADR 0008](../adr/0008-claims-record-what-sources-say.md).

## The credits table, and what the experiment could not see

After three review rounds, Fredrik caught what none of them did: the `artist_credits` table was day-one ceremony — its
`role` column fully determined by which FK was set, its `position` always 0 — inherited by the detail plan from the
teebs data model and faithfully built by both twins. Dropped in favour of direct artist links (ADR 0009); the credits
table returns with MusicBrainz. The methodological lesson: parity twins detect *ambiguity* in a plan, not *error* in it
— anchoring that lives in the plan itself is invisible to the experiment. Recorded as a project principle: teebs is
precedent, not blueprint.

## From database dump to record shelf

First real use raised the right question: Fredrik found `album-1/` in `~/Music/leeks` and asked what it was. The
dumb-layout punt died on contact with dogfooding — the tree is part of the product. ADR 0010 followed:
`<Album Artist>/<Year> <Album Title>/<NN> <Title>.<ext>` derived from merged columns at copy time, omission for missing
optional components, the `Unknown Artist` bucket, replacement over slugging, case-folded collision handling, and the
rule that metadata changes never rename — `leek organize` reconciles stale paths explicitly, and tag write-back (a
different blast radius: it changes bytes, breaking hashes and seeded torrents) becomes its own verb. Artist and genre
identity fold case (NOCASE; first-seen spelling displays, claims stay verbatim; aliases later). `leek init` joined the
roadmap to retire the hardcoded root.

The same conversation produced two new living design docs: [verbs](../design/verbs.md) — the collection of verbs as a
curated interface, with tag write-back deliberately unnamed — and the normative [glossary](../design/glossary.md), born
from the observation that "consensus" had already drifted into two implementations, pinning copy time, merged columns,
scalar, and the rest of the project's vocabulary.

## Open ends

The punts still standing: re-add disambiguation (`--force`, hashes), raw artist strings awaiting MusicBrainz, the
hardcoded root (until `leek init`), singletons excluded, multi-disc deferred until the corpus grows a multi-disc album.
The dumb-copy-layout punt is retired by ADR 0010.
