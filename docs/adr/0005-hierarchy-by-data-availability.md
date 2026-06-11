# 0005 — The entity hierarchy is realised as its data arrives

## Decision

The core position "the entity hierarchy is release group → release → track/recording → file, all four are modelled"
describes the finished model, and is read as: *each entity is modelled by the time the data that populates it exists*.
Slice 1 models release (the `albums` table) → track → file, fed by file tags. Release groups, recordings, and works
arrive with the MusicBrainz slice — the first source that can actually distinguish them — via an Alembic migration that
backfills the new entities for libraries imported before it.

Core positions constrain the destination, not the order of construction. A slice violates a core position only if it
builds something the finished model forbids — a denormalised column, a source that overwrites another — not if it has
yet to build something the finished model requires.

## Context

The core position and the roadmap contradicted each other on their face: "all four are modelled" sits under *never
violate*, while the roadmap defers release groups and recordings to the matcher slice, per the project principle of
slicing by data availability.

Resolving in the roadmap's favour costs nothing. File tags cannot distinguish a release from its release group, so
modelling both in slice 1 means degenerate 1:1 rows — pure ceremony with no data behind it. And the backfill migration
must be written regardless: dogfooding starts at slice 1, so the MusicBrainz slice has to upgrade already-imported
libraries whichever way this decision went.

## Alternatives considered

- **Degenerate release-group rows from day one** — a 1:1 row per release until MusicBrainz arrives. Keeps the schema
  shaped like the finished model, but the rows carry no information, every query joins through ceremony, and the
  MusicBrainz slice still has to rewrite them when real groups appear.
- **Build the full hierarchy upfront** — the literal reading. Front-loads tables, ORM models, and migrations that
  nothing populates or queries for several slices; exactly the detailed-plan-ahead-of-contact decay the project
  principles exist to prevent.
