# 0006 — The entity hierarchy is realised as its data arrives

Status: Decided (2026-06-11)

## Decision

The core position "the entity hierarchy is release group → release → track/recording → file, all four are modelled"
describes the finished model. Each entity is modelled by the time the data that populates it exists. Slice 1 models
release (the `albums` table) → track → file, fed by file tags. Release groups, recordings, and works arrive with the
MusicBrainz slice — the first source that can distinguish them — via an Alembic migration that backfills the new
entities for libraries imported before it.

Core positions constrain the destination, not the order of construction. A slice violates one only by building something
the finished model forbids — a denormalised column, a source that overwrites another — not by leaving something the
finished model requires unbuilt.

## Context

The core position and the roadmap contradict each other on their face: "all four are modelled" sits under never-violate,
while the roadmap defers release groups and recordings to the matcher slice, per the principle of slicing by data
availability. File tags cannot distinguish a release from its release group, so modelling both in slice 1 yields
degenerate 1:1 rows with no data behind them. The backfill migration is needed regardless: dogfooding starts at slice 1,
so the MusicBrainz slice must upgrade already-imported libraries either way.

## Alternatives considered

- **Degenerate release-group rows from day one** — rejected: the 1:1 rows carry no information, and the MusicBrainz
  slice has to rewrite them when real groups appear.
- **Build the full hierarchy upfront** — rejected: front-loads tables, ORM models, and migrations that nothing populates
  for several slices, the detailed-plan-ahead-of-contact decay the project principles exist to prevent.
