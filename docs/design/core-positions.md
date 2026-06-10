# Core positions

The engineering contract behind leeks. The [README](../../README.md) argues these positions; this document states them
as constraints. Code that violates one is wrong, however convenient.

## Never violate

**The album is the primary entity, top-down.** The album — a MusicBrainz *release group* — has its own identity,
metadata, and sources, independent of any file on disk. beets builds bottom-up from the file; leeks inverts that. The
album is never a label derived from grouping track tags.

**The entity hierarchy is release group → release → track/recording → file.** All four are modelled. A release is a
specific pressing or edition; a file is bytes on disk that realise a track. Artists are first-class rows, not strings in
tags.

**Metadata sources are layers, never overwrites.** File tags, MusicBrainz, Discogs, tracker upload metadata, manual
edits: each adds a layer, all are preserved. The library view is a merge on read; precedence rules are separate from
storage. No source ever destroys what another source said.

**The schema is normalised, with real foreign keys.** No denormalised flat table, no album data duplicated across track
rows. Album-level edits propagate to tracks by construction — this failure in beets is the founding annoyance of the
project.

**History is append-mostly.** Every mutation lands in a change log; prior states are reconstructible. A bad match must
be undoable.

**Originals are never modified.** Import copies files into the library; it never moves or rewrites the source. Tag
writing, renaming, and moving library files are explicit, separate actions — never a side effect of import or matching.

**Imports never block on matching.** Every file enters the library unconditionally; matching is a separate, retryable
step. The files that most need management are the ones with the worst metadata — gating them out at import defeats the
purpose.

## Architecture

The two-layer model — Pydantic v2 for the pipeline, SQLAlchemy 2.0 for persistence, mapped at the boundary — is
[ADR 0001](../adr/0001-pydantic-pipeline-sqlalchemy-persistence.md).
