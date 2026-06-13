# 0014 — Render output from a typed projection

Status: Proposed (2026-06-13)

## Decision

Every way `leek` prints an entity — the human-readable table, the tab-separated record a pipe receives, and any future
structured shape (`--format json`, `csv`) — renders from a single **typed projection** of that entity: its real, typed
fields. A field's display string is *one rendering* of its value, never the value's only public form.

Two consequences are the decision:

- **No formatter is privileged.** The table and a JSON document read the same typed values through the same seam. They
  may differ in how they present a value — a duration shown as `3:21` to the eye, emitted as an integer of seconds to
  JSON — but they never disagree about what the value *is*, because neither is reading the other's string.
- **A null is not a fallback.** Because formatters render from typed values, "this field is genuinely empty" stays
  distinct from "show this stand-in instead" right up to the moment of display. The fallback (the unknown-artist bucket,
  [ADR 0010](0010-the-library-tree-is-for-humans.md)) is a *rendering choice a formatter makes*, not a string the data
  carries. JSON emits `null`; the table may italicise a bucket; the data underneath is the same honest absence.

This is the read-side analogue of the positions already settled: the database is the source of truth and the library
tree is its human projection ([ADR 0010](0010-the-library-tree-is-for-humans.md)); Pydantic models are the pipeline's
typed lingua franca, ORM rows are persistence only ([ADR 0001](0001-pydantic-pipeline-sqlalchemy-persistence.md)). The
typed projection extends that discipline to output: the typed value is the truth, every printed form is a projection of
it.

**Grammar is deferred to contact.** This record fixes only that the projection exists and is the single source every
formatter reads. The shape of the projection type, exactly which fields it exposes per entity, and the envelope a
structured format wraps them in are designed when the slice that builds them arrives — the same direction-now,
grammar-on-contact stance as [ADR 0012](0012-query-language-is-beets-inspired.md) and
[ADR 0013](0013-list-selects-its-entity-by-option.md). Nothing is built today.

## Context

The thread that forced this was output formatting for `leek list` — field selection and a machine-readable shape. Before
designing those, we examined how beets produces output, because beets is the scar tissue here.

beets has exactly one public view of a model's fields: `formatted()`, declared `Mapping[str, str]` — every value comes
back as a human-readable unicode string (`beets/dbcore/db.py`). The `-f '$artist - $album'` template language reads from
it; so does everything else. When structured output finally arrived years later — the `export` plugin — it had nowhere
typed to plug in: `beet export` builds its JSON from `dict(item.formatted(...))` (`beetsplug/info.py`), so the JSON
inherits the string flattening. Durations pass through `human_seconds_short`; a custom `ExportEncoder` exists *only* to
cope with dates, because by the time data reaches the encoder the types are already gone. The result is JSON whose
numbers are strings and whose absences are indistinguishable from fallbacks.

The lesson is not "beets bolted JSON on late." It is that **there was no typed seam to bolt onto.** The formatted string
was the only public form of a field, so honest structured output was impossible by construction — not a missing feature
but a foreclosed one. Deciding the seam now, before any formatter beyond the shipped two exists, is what keeps the
formatters that follow (selection, shape, discovery) small: each reads the projection, none re-invents field access.

## Alternatives considered

- **Render from formatted strings, as beets does** — every formatter reads a `Mapping[str, str]`. Simplest until the
  second audience appears; then it is a dead end. You cannot recover an integer, a real null, or a typed date from a
  string that already decided how to display it, and bolting a typed path on later means two field-access mechanisms
  that drift. This is the regret being avoided, named precisely so it is not re-walked.
- **Let each formatter read fields ad hoc** — the table pulls from the ORM, JSON from Pydantic, the pipe from somewhere
  else. No single definition of "the entity's renderable fields," so the table and JSON quietly disagree about what
  exists and what it is called — the same field-drift that makes beets' field set an archaeology dig. One seam, read by
  all, is the point.
- **Defer the whole question until `--format json` is built** — tempting, since nothing is built. But this principle
  constrains field selection, output shape, and field discovery *all at once*; it is the foundation the next three
  records rest on. Settling it now is what lets each of those be a small, contained decision rather than each
  re-litigating where values come from.
