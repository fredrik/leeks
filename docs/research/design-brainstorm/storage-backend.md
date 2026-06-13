# ADR 0001: Storage backend — SQLite default, Postgres supported, dump as canonical interchange

- **Status:** Never adopted — preserved as research. The ADR numbering predates `docs/decisions/` and collides with it;
  see the [README](README.md) for what was distilled and where.
- **Date:** 2026-06-10
- **Amended by:** [actors-capabilities.md](actors-capabilities.md) (same provenance)

## Context

leeks persists a normalised relational schema (release group → release → medium → track, plus immutable metadata layers
and an append-only event log) through SQLAlchemy 2.0 and Alembic. The workload is read-heavy and append-mostly, at
trivial scale for any relational engine. The library belongs to a single person but is accessed by multiple concurrent
actors — the human, cron jobs, ingest pipelines, and AI agents — possibly from different hosts (see ADR 0003).

Two forces pull in opposite directions:

1. **Local-first is the product.** The target audience installs a CLI (`uv tool install leeks`) and expects zero
   daemons. The library should travel with the collection: rsyncable, restorable with `cp`, filesystem-snapshottable.
2. **The reference deployment is already multi-host.** The library lives on one machine and is consumed from others over
   a network mount. SQLite on NFS/SMB is outside its safe envelope: advisory locking is unreliable on network
   filesystems and corruption is a real risk. The VFS daemon and the CLI cannot be assumed to share a host with the
   database.

A third force is non-negotiable project philosophy: the library must never be locked to a storage engine. Portability is
a feature, not an aspiration.

## Decision

1. **SQLite is the default and reference backend.** WAL mode, STRICT tables, `foreign_keys=ON` enforced per connection.
   The quickstart and all default documentation assume SQLite and nothing else.

2. **PostgreSQL is a supported backend**, selected by connection URL via pydantic-settings
   (`LEEKS_DB=sqlite:///… | postgresql+psycopg://…`), using psycopg 3.

3. **Portability is enforced by CI, not convention.** The full test suite and every Alembic migration run against both
   engines from the first migration (Postgres via testcontainers). A change that passes on one engine and fails on the
   other does not merge.

4. **`leek dump` / `leek load` define the canonical interchange format**: a deterministic, ordered text serialisation of
   the entire library — entities, layers, events. The database is a rebuildable index of the dump; the dump is the
   portable artifact, the backup format, and the migration path between backends:

   ```sh
   leek dump | LEEKS_DB=postgresql+psycopg://nas/leeks leek load
   ```

## Discipline

The constraints that make decision 3 hold:

- SQLAlchemy Core/ORM constructs only in core paths; raw SQL must be dialect-gated and mirrored on both engines.
- Join tables, never `ARRAY` or other Postgres-only types in the core schema.
- JSON through the SQLAlchemy `JSON` type only (JSON1 / jsonb underneath); no engine-specific JSON operators in core
  queries.
- Datetimes stored as UTC through a `TypeDecorator`; SQLite has no native datetime type.
- Alembic migrations use `batch_alter_table` to survive SQLite's crippled `ALTER TABLE`.
- Matching stays in-process (jellyfish / lap / numpy); no `pg_trgm`, no engine FTS in core.
- Change notification behind one interface: `PRAGMA data_version` polling on SQLite, `LISTEN/NOTIFY` on Postgres.

## Alternatives considered

- **SQLite only.** Simplest, but the reference deployment already violates its safe envelope. Workarounds either fork
  state (per-client DB copies) or invent a network protocol that Postgres already is.
- **Postgres only.** Kills local-first and zero-dependency install; wrong audience.
- **SQLite + Litestream/LiteFS.** Solves replication and backup, not multi-host concurrent access.
- **Hand-rolled SQL per engine.** Maximal control, double maintenance, rejected.
- **Daemon-mediated access** (clients never touch the DB, all access through a leeks daemon). Originally deferred;
  adopted as the plan of record by ADR 0003. Metadata-writing clients still need a database connection until that API
  exists, and Postgres covers the gap while remaining useful after.

## Consequences

**Positive.** The engine becomes an implementation detail. The dump is the open format, consistent with the project
manifesto. Backend migration is a shell pipeline. CI catches dialect drift before it compounds. The multi-host topology
is supported from day one.

**Costs.** Double the CI surface. Core SQL is lowest-common-denominator forever. Contributors must internalise the
discipline list. The dump format becomes a versioned compatibility surface.

**Neutral.** Postgres is documented under advanced/multi-host setup only; the default experience never mentions it.

## Follow-up

The dump serialisation is load-bearing well beyond backup: it is the same canonical text rendering used by `leek show`,
`leek diff`, `leek edit`, and the VFS `.release.yaml` sidecar. Field ordering, determinism, provenance representation,
and round-trip guarantees need their own spec — ADR 0002.
