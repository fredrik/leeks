# 0023 — Render a set-valued field across formats

Status: Decided (2026-06-14)

## Decision

`genres` joins `leek list`'s field namespace as the first **set-valued** projection field. Two rulings, both meant to
set the precedent for set fields that follow (styles, moods):

**A set field is opt-in, not a default column.** A bare `leek list` stays the album's identity — artist, year, title —
and `genres` appears only when `--fields` names it (and in `leek fields`, which lists it). The shelf's default is
identity, kept lean; genre is descriptive, often absent, and variable in width, so it earns a place behind `--fields`
rather than widening every row.

**Each format renders the set in its own register, off one typed value.** The projection stays a real `list[str]` on the
row (ADR 0014); each formatter decides how to flatten it:

- **JSON** keeps it a real array — the structured shape is the home for structure, so a consumer reads the set without
  splitting a string.
- **Human** (the plain table and the piped line) joins with `, ` — the same reading form `leek show` already uses.
- **CSV/TSV** join with `; ` — one cell, a sub-delimiter distinct from CSV's comma, so the comma stays the column
  separator and a consumer can split the cell back into the set. This is best-effort: a flat format cannot nest, and a
  genre containing a literal `; ` would be ambiguous (none do, and the structured home for fidelity is JSON).

The renderers branch on the value being a list, not on the field name `genres`, so the next set-valued field inherits
all of this for free.

## Context

ADR 0022 made genre a set; `leek show` already displays the genres list, but `leek list` could not — `genres` was not in
its field namespace, and every `list` formatter reads `getattr(row, name)` and stringifies it. A `list[str]` fed
straight through would render as a Python repr (`['Ambient', 'Dub Techno']`) in the human and delimited shapes — ugly,
and in CSV a comma-laden cell the writer would quote into something no consumer expects. The field had to enter the
namespace, and each formatter had to learn how to flatten a set, before genre could appear on the shelf at all.

## Alternatives considered

- **A default genres column** — informative at a glance, but widens the default shelf and prints an empty cell for every
  untagged album. The shelf's job is identity; description is what `--fields` is for.
- **Refuse a set field in CSV/TSV** — honest that a flat format cannot carry a set faithfully, and it would steer the
  user to JSON. But a `; `-joined cell is useful far more often than it is ambiguous, and refusing turns a routine
  `--fields title,genres --format csv` into an error. Best-effort with a documented sub-delimiter beats a wall.
- **Join CSV with `, ` and lean on the csv writer's quoting** — the writer would quote the cell correctly, but a
  consumer then cannot tell a multi-value separator from a comma inside a single genre. The `; ` sub-delimiter keeps the
  two commas distinct.
