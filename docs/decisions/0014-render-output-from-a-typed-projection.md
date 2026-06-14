# 0014 — Render output from a typed projection

Status: Decided (2026-06-13)

## Decision

Every way `leek` prints an entity — the human-readable table, the tab-separated record a pipe receives, and any future
structured shape (`--format json`, `csv`) — renders from a single **typed projection** of that entity: its real, typed
fields. A field's display string is one rendering of its value, never the value's only public form.

- **No formatter is privileged.** Table and JSON read the same typed values through the same seam. They may present a
  value differently — a duration shown as `3:21` to the eye, emitted as an integer of seconds to JSON — but never
  disagree about what the value is, because neither reads the other's string.
- **A null is not a fallback.** "Genuinely empty" stays distinct from "show this stand-in instead" up to the moment of
  display. The fallback (the unknown-artist bucket, [ADR 0010](0010-the-library-tree-is-for-humans.md)) is a rendering
  choice a formatter makes, not a string the data carries. JSON emits `null`; the table may italicise a bucket; the data
  underneath is the same honest absence.

This is the read-side analogue of settled positions: the database is the source of truth and the library tree its human
projection ([ADR 0010](0010-the-library-tree-is-for-humans.md)); Pydantic models are the pipeline's typed lingua franca,
ORM rows persistence only ([ADR 0001](0001-pydantic-pipeline-sqlalchemy-persistence.md)). The typed value is the truth;
every printed form is a projection of it.

The record fixes only that the projection exists and is the single source every formatter reads. The projection type's
shape, which fields it exposes per entity, and the envelope a structured format wraps them in are designed when the
slice that builds them arrives — direction now, grammar on contact, as in
[ADR 0012](0012-query-language-is-beets-inspired.md) and [ADR 0013](0013-list-selects-its-entity-by-option.md).

## Context

Output formatting for `leek list` — field selection and a machine-readable shape — forced this. beets is the scar
tissue: it has one public view of a model's fields, `formatted()`, declared `Mapping[str, str]`, where every value
returns as a human-readable unicode string (`beets/dbcore/db.py`). The `-f '$artist - $album'` template language reads
from it, and so does everything else. When structured output arrived later as the `export` plugin, there was no typed
seam to plug into: `beet export` builds its JSON from `dict(item.formatted(...))` (`beetsplug/info.py`), inheriting the
string flattening. Durations pass through `human_seconds_short`; a custom `ExportEncoder` exists only to cope with
dates, because by the encoder the types are already gone. The JSON's numbers are strings and its absences are
indistinguishable from fallbacks — honest structured output was foreclosed by construction.

Deciding the seam now, before any formatter beyond the shipped two exists, keeps the formatters that follow (selection,
shape, discovery) small: each reads the projection, none re-invents field access.

## Alternatives considered

- **Render from formatted strings, as beets does** — every formatter reads a `Mapping[str, str]`. Rejected: you cannot
  recover an integer, a real null, or a typed date from a string that already decided how to display it, and a typed
  path bolted on later means two field-access mechanisms that drift. This is the beets regret being avoided.
- **Let each formatter read fields ad hoc** — table from the ORM, JSON from Pydantic, the pipe from somewhere else.
  Rejected: with no single definition of an entity's renderable fields, table and JSON drift on what exists and what it
  is called.
- **Defer the whole question until `--format json` is built** — rejected: the principle constrains field selection,
  output shape, and field discovery at once and is the foundation the next three records rest on. Settling it now lets
  each of those be a small, contained decision rather than re-litigate where values come from.
