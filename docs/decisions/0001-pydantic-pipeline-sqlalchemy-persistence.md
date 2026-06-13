# 0001 — Model the pipeline in Pydantic, persist in SQLAlchemy

Status: Decided (2026-06-10)

## Context

leeks moves metadata through a pipeline — tag reading, MusicBrainz lookups, matching, merging — and persists it in a
normalised relational schema. The same conceptual entities (album, track) appear in both worlds, which invites using one
set of classes for both.

That is the beets trap. When pipeline objects are database objects, business logic accretes on persistence classes,
objects are only valid inside a database session, and external candidates — a MusicBrainz release that may never enter
the library — have to be faked as library rows or handled by a parallel code path. The pipeline becomes untestable
without a database.

## Decision

Two layers, mapped at an explicit boundary, never mixed:

- **Pipeline:** Pydantic v2 models (`TrackInfo`, `AlbumInfo`) are the lingua franca. All matching, fetching, and merging
  logic speaks Pydantic. These objects are plain data — constructible anywhere, valid without a session, serialisable.
- **Persistence:** SQLAlchemy 2.0 ORM models, used only to read and write the database. They never travel through
  pipeline code and carry no business logic.

Mapper functions at the boundary convert between the two. Storage is a SQL database behind SQLAlchemy; every schema
change goes through an Alembic migration.

## Alternatives considered

- **One ORM layer for everything** (the beets model). Rejected: couples every pipeline step to a database session and
  reproduces the failure this project exists to fix.
- **Plain dataclasses or dicts for the pipeline.** Rejected: no validation or serialisation at the boundaries, where
  external sources hand us unreliable data. Pydantic earns its dependency there.
- **SQLModel** (one class that is both Pydantic and SQLAlchemy). Rejected: merges the layers back together, so the
  database schema and the pipeline shape can no longer evolve independently.

## Consequences

- Mapping code at the boundary is a permanent cost, accepted deliberately. Two definitions of related shapes must be
  kept in sync.
- The pipeline is testable without a database, and external candidates are first-class pipeline citizens whether or not
  they ever become library rows.
