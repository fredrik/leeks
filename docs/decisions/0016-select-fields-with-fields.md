# 0016 — Select fields with `--fields`

Status: Decided (2026-06-13)

## Decision

`leek list --fields a,b,c` chooses which fields print. It is *selection, not interpolation*
([ADR 0015](0015-reject-a-template-language-for-output.md)): a list of field names, nothing between them. leek owns the
layout — the chosen fields become columns to the eye, keys to a structured shape — exactly as the curated default view
does; the user names *what*, not *how*.

What this record settles:

- **It reads the typed projection** ([ADR 0014](0014-render-output-from-a-typed-projection.md)). A selected field is the
  entity's real, typed value; a duration stays a duration, an absence stays null. `--fields` chooses keys off the
  projection, it does not pre-stringify.
- **Field order is column order.** `--fields title,artist` prints title then artist.
- **It replaces the curated default columns, not extends them.** You asked for exactly these; you get exactly these,
  plain — the per-field styling of the default view (the italic unknown-artist bucket,
  [ADR 0010](0010-the-library-tree-is-for-humans.md)) belongs to the curated view, not to this utilitarian one. If the
  *default* columns feel wrong, that is a default-columns decision, not a reason to type `--fields` every time.
- **The namespace is per subject.** `--fields` means something only alongside a subject
  ([ADR 0013](0013-list-selects-its-entity-by-option.md)): a track has `bitrate`, an artist has almost nothing. What
  names are valid for each subject is discoverable on its own ([ADR 0018](0018-discover-fields-with-leek-fields.md)).
- **An entity's own fields only.** `--fields artist` on `--tracks` is the *track's* artist. Whether a track may select
  its album's fields — reaching *up* the tree — is the same cross-entity-reach question the query grammar already defers
  ([ADR 0012](0012-query-language-is-beets-inspired.md), [ADR 0013](0013-list-selects-its-entity-by-option.md)).
  `--fields` does not pre-empt it.

**Grammar deferred to contact.** The error a bad field name produces (the intent: loud, listing valid names, never a
silent skip), whether a TTY view grows a header row, and whether the option earns a short `-f` are designed when the
slice arrives.

## Context

The daily use of beets' `-f` is inspection — `beet ls -f '$path'`, `-f '$bitrate'` — and that use is *selection* with
the interpolation engine idling. `--fields` keeps that workflow whole while
[ADR 0015](0015-reject-a-template-language-for-output.md) drops the language around it. It is the breadth counterpart to
`info`'s depth: chosen columns *across* a result set, not one entity examined.

## Alternatives considered

- **A template string** — rejected wholesale in [ADR 0015](0015-reject-a-template-language-for-output.md); `--fields` is
  the selection half kept after the interpolation half is discarded.
- **Extend the default columns rather than replace them** — surprising: `--fields bitrate` would then print the curated
  view *plus* bitrate, and there would be no way to ask for bitrate alone. Replacement is the predictable contract.
- **Put field selection on `info`, not `list`** — `info` is one entity in depth; selecting columns across many rows is
  breadth, which is `list`'s concern. Selection belongs where the rows are.
