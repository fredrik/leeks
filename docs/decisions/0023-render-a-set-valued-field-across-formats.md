# 0023 — Render a set-valued field across formats

Status: Decided (2026-06-14)

## Decision

`genres` joins `leek list`'s field namespace as the first **set-valued** projection field. Two rulings, both meant to
set the precedent for set fields that follow (styles, moods):

**A set field is opt-in, not a default column.** A bare `leek list` stays the album's identity — artist, year, title —
and `genres` appears only when `--fields` names it (and in `leek fields`, which lists it). Genre is descriptive, often
absent, and variable in width, so it sits behind `--fields` rather than widening every row.

**Each format renders the set in its own register, off one typed value.** The projection stays a real `list[str]` on the
row (ADR 0014); each formatter flattens it:

- **JSON** keeps it a real array, so a consumer reads the set without splitting a string.
- **Human** (the plain table and the piped line) joins with `, `, the form `leek show` already uses.
- **CSV/TSV** join with `; `, a sub-delimiter distinct from CSV's comma, so the comma stays the column separator and a
  consumer can split the cell back into the set. Best-effort: a flat format cannot nest, and a genre containing a
  literal `; ` would be ambiguous (none do; JSON is the structured home for fidelity).

The renderers branch on the value being a list, not on the field name `genres`, so the next set-valued field inherits
this for free.

## Context

ADR 0022 made genre a set; `leek show` already displays the genres list, but `leek list` could not — `genres` was not in
its field namespace, and every `list` formatter reads `getattr(row, name)` and stringifies it. A `list[str]` fed
straight through would render as a Python repr (`['Ambient', 'Dub Techno']`) in the human and delimited shapes — ugly,
and in CSV a comma-laden cell the writer would quote into something no consumer expects. The field had to enter the
namespace, and each formatter had to learn how to flatten a set, before genre could appear on the shelf at all.

## Alternatives considered

- **A default genres column** — rejected because it widens the default shelf and prints an empty cell for every untagged
  album; the shelf's job is identity, and description is what `--fields` is for.
- **Refuse a set field in CSV/TSV** — rejected because it turns a routine `--fields title,genres --format csv` into an
  error; a `; `-joined cell is useful far more often than it is ambiguous.
- **Join CSV with `, ` and lean on the csv writer's quoting** — rejected because the consumer then cannot tell a
  multi-value separator from a comma inside a single genre. The `; ` sub-delimiter keeps the two commas distinct.
