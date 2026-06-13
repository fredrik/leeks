# Core positions

The engineering contract behind leeks. The [README](../../README.md) argues these positions; this document states them
as constraints. Code that violates one is wrong, however convenient.

## Never violate

**The album is the primary entity, top-down.** The album — a MusicBrainz *release group* — has its own identity,
metadata, and sources, independent of any file on disk. beets builds bottom-up from the file; leeks inverts that. The
album is never a label derived from grouping track tags.

**The entity hierarchy is release group → release → track/recording → file.** All four are modelled. A release is a
specific pressing or edition; a file is bytes on disk that realise a track. Artists are first-class rows, not strings in
tags. This describes the finished model: each entity is realised by the time the data that populates it exists
([ADR 0006](../decisions/0006-hierarchy-by-data-availability.md)).

**Metadata sources are layers, never overwrites.** File tags, MusicBrainz, Discogs, tracker upload metadata, manual
edits: each adds a layer, all are preserved. The library view is a merge on read; precedence rules are separate from
storage. No source ever destroys what another source said. The asymmetry is the test for every design choice: the merged
view is derived and rebuildable from claims, so corrupting it is an inconvenience — losing claims is data loss.

**Fetched payloads are kept.** When a source is fetched over the network, the raw response is stored alongside the
claims parsed from it. Mapping a new field is then a local re-extraction, never a re-fetch across the library — beets
made every new field a fresh round of `mbsync`, and `mbsync` is what clobbered edits. A cache is disposable; a payload
is not.

**Automation writes as its own source, never as the user.** Every automated writer — cron job, pipeline, agent — claims
under its own name (`cron:lastfm-sync`, `agent:genre-tagger`), with precedence below `user`, and the change log records
who wrote what; there are no anonymous writes. Automation can never clobber a human edit by construction, and a
misbehaving writer's whole contribution is dropped by dropping its source. Only `user`-wins is fixed; precedence among
the rest is merge policy, deliberately open.

**The schema is normalised, with real foreign keys.** No denormalised flat table, no album data duplicated across track
rows. Album-level edits propagate to tracks by construction — this failure in beets is the founding annoyance of the
project.

**History is append-mostly.** Every mutation lands in a change log; prior states are reconstructible. A bad match must
be undoable — and undo is forward motion: a compensating change appended to the log, never a rewrite. References to past
states stay valid forever.

**Originals are never modified.** Import copies files into the library; it never moves or rewrites the source. Tag
writing, renaming, and moving library files are explicit, separate actions — never a side effect of import or matching.

**Imports never block on matching.** Every file enters the library unconditionally; matching is a separate, retryable
step. The files that most need management are the ones with the worst metadata — gating them out at import defeats the
purpose.

**The library tree is for humans.** Paths derive from merged metadata at copy time and read like a record shelf — artist
/ year title / nn title ([ADR 0010](../decisions/0010-the-library-tree-is-for-humans.md)). Metadata changes never rename
files: paths go stale honestly, and reorganisation is an explicit action. The database is the source of truth; the tree
is its human-readable projection.

## Architecture

The two-layer model — Pydantic v2 for the pipeline, SQLAlchemy 2.0 for persistence, mapped at the boundary — is
[ADR 0001](../decisions/0001-pydantic-pipeline-sqlalchemy-persistence.md).

**Output renders from a typed projection.** Every way leek prints an entity — the human table, the piped record,
structured `--format` output — renders from the entity's real, typed fields, never from pre-stringified values. A
field's display string is one rendering among several, never its only public form: the table and JSON read the same
typed values, and which fields are renderable is defined once, not per formatter. This keeps a genuine null distinct
from a display fallback ([ADR 0010](../decisions/0010-the-library-tree-is-for-humans.md)) — absence is data, the
stand-in is a rendering choice. beets had only `formatted()`, a `Mapping[str, str]`, so even its JSON export rode the
human-readable string flattener and could never emit honest typed data; there was no typed seam to plug structured
output into ([ADR 0014](../decisions/0014-render-output-from-a-typed-projection.md)).

**One extension protocol.** A plugin is a source of claims behind one narrow protocol; MusicBrainz, Discogs, a path
parser, and a scrobble fetcher all fit it. Lifecycle hooks are presumed wrong until a real extension cannot be a source
— beets' plugin API grew by accretion, hook by hook, and the result constrained every core refactor for a decade.

The storage engine is an implementation detail, kept replaceable by discipline — see [portability](portability.md).
