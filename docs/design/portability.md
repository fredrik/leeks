# Portability

The library is never locked to a storage engine, and never locked to leeks. Two artifacts carry that promise: a
discipline that keeps the SQL portable, and a dump that makes the database itself replaceable.

## The engine is an implementation detail

SQLite is the product: local-first, zero daemons, a library that travels with the collection and restores with `cp`.

A second engine (Postgres) is deliberately **not** built now. Its trigger is topology, not scale — the day the database
and its clients genuinely live on different hosts, SQLite over a network mount is outside its safe envelope and the
question reopens. Until that deployment is real, a Postgres CI leg is a permanently doubled surface bought against a
hypothesis, and we decline it.

What we adopt instead is the discipline that keeps the door open, because dialect drift compounds silently and is
miserable to unwind:

- SQLAlchemy constructs only in core paths; any raw SQL is dialect-gated and justified where it sits.
- Junction tables, never engine-specific types (no `ARRAY`); the schema already works this way (`album_genres`).
- JSON columns, when they arrive, go through the SQLAlchemy `JSON` type only — no engine-specific JSON operators in core
  queries.
- Datetimes are UTC before they reach the database (today normalised by hand at write time; a `TypeDecorator` when the
  call sites multiply).
- Alembic migrations use `batch_alter_table`, which survives SQLite's crippled `ALTER TABLE`.
- Matching stays in-process (jellyfish, lap, numpy) — no engine FTS, no `pg_trgm`, in core paths.

A rule may be broken only knowingly, in a dialect-gated spot, with the portable fallback written down.

## The dump is the canonical interchange

`leek dump` and `leek load` (verbs, later) serialise the library to deterministic, ordered text and rebuild it. The dump
is the backup format, the portable artifact, and — should a second engine ever arrive — the migration path between
backends, as a shell pipeline.

The dump serialises **claims and history, never the merged view**. A dump of merged values would freeze today's merge
policy into the data; a dump of claims survives any future change to precedence. The merged view is recomputed on load —
the database is a rebuildable index of the dump, which is the core-positions asymmetry (losing the merged view is an
inconvenience; losing claims is data loss) carried to its conclusion.

Determinism makes the dump diffable, which is worth designing for: the same canonical rendering has four more would-be
consumers waiting in the [brainstorm research](../research/design-brainstorm/README.md) (diff, show/edit, a VFS sidecar,
proposal payloads). When the first consumer arrives, the rendering gets a spec; the dump's format is a versioned
compatibility surface from its first release.
