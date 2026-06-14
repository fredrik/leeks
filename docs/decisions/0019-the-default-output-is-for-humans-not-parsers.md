# 0019 — The default output is for humans, not parsers

Status: Decided (2026-06-13)

## Decision

The default output — what `leek list` prints when `--format` is unset — is `human`, always, and it is for reading, never
for parsing. Its bytes are not a contract: the human formatter may change its columns, spacing, adornment, and wording
between releases, because nothing is entitled to parse them. Machine consumption is what `--format` is for
([ADR 0017](0017-choose-output-shape-with-format.md)).

`isatty` governs presentation, not format. A terminal gets the themed, aligned table; a pipe gets the same `human`
formatter rendered plain — each row's fields via `_display_cell`, space-joined, absent values dropped, one line per
record, never wrapped, no colour, no width-alignment. Same formatter, two renderings — the `ls`/`git` discipline, where
layout adapts to the tty but the format does not silently switch (`git log` piped is still `git log`, not
`--porcelain`). `--format human` is a named value in the enum, so a script can force the readable shape either way; it
changes nothing a bare `leek list` does not.

The machine formats are an explicit, opt-in set, never auto-selected by a pipe. A consumer reaches for one by name, and
that naming is what earns the stability contract:

- **`json`** — structured, typed, nestable; real integers, real `null`s
  ([ADR 0014](0014-render-output-from-a-typed-projection.md)). For programs that want the types intact.
- **`csv`** — the spreadsheet lingua franca (Excel, Numbers, pandas). Carries a header row, because spreadsheets expect
  named columns.
- **`tsv`** — the shell-pipeline delimited shape; `cut -f2` reads data from line one, so it carries no header. Only the
  flat verbs (`list`) offer `csv`/`tsv`.

For both delimited formats, values go through `csv.writer`, so a comma or quote in a title is quoted and parses back
intact; a cell renders the typed value stringified, and a genuine absence is the empty string, never the
`Unknown Artist` human fallback ([ADR 0014](0014-render-output-from-a-typed-projection.md)).

This revises the unset-default behaviour in [ADR 0011](0011-list-is-albums-in-shelf-order.md),
[ADR 0013](0013-list-selects-its-entity-by-option.md), and [ADR 0017](0017-choose-output-shape-with-format.md): a pipe
no longer receives a tab-separated record — that was a machine format reached by accident. It becomes the plain
rendering of the human format; TSV survives only as explicit `--format tsv`. The rest of those records stands; this
changes one clause. It likewise corrects 0018's "stable for scripting" framing of `leek fields`'
([ADR 0018](0018-discover-fields-with-leek-fields.md)) bare-names listing: that listing has no presentation to strip, so
it is identical in a pipe and a terminal — but it is human output too, and the contract a script binds to is
`leek fields --format json`, never the bare-names default.

## Context

The default output is great because we can print anything and not be beholden to parsability — a freedom that survives
exactly as long as nobody is entitled to parse the default. The shipped behaviour spent it: a pipe got a tab-separated
record, so `leek list | cut -f2` working out of the box froze that column order into a contract nobody asked to
stabilise. The freedom and the auto-TSV pipe default cannot both hold; this record keeps the freedom.

This is the scar `--format` already steers by: beets had one public view of a field — the formatted string
([ADR 0014](0014-render-output-from-a-typed-projection.md)) — so human and machine forms were never separable, and
structured output inherited the string flattening. When the readable output and the parseable output are the same bytes,
the readable one cannot move without breaking a parser.

`isatty` answers "is a person watching?", a question about presentation — colour, alignment, width — not a proxy for
"does the caller want a machine format." A pipe means "strip the adornment," not "switch to a contract." The human-plain
rendering is plainer but still not a contract; a caller that wants stable output uses `--format`, and this binds every
verb.

## Alternatives considered

- **Tab-separated record on a pipe** — the shipped default ([ADRs 0011](0011-list-is-albums-in-shelf-order.md),
  [0013](0013-list-selects-its-entity-by-option.md), [0017](0017-choose-output-shape-with-format.md)). Rejected:
  convenient, but a parse contract reached by accident, and it puts TSV, not human, on the wire. `--format tsv` buys a
  deliberate contract instead.
- **JSON on a pipe** — rejected: the same flaw with a bigger blast radius, surprising `| less` and `| grep` with a shape
  no one asked for and committing the JSON envelope's stability by accident.
- **No split at all — same output to terminal and pipe** — rejected: either loses the themed table (plain everywhere) or
  ships colour codes and width-padding into pipes (table everywhere). The split is right; it just has to be
  presentation-only.
- **Drop `tsv`, keep `csv` + `json`** — declined: the data is comma-heavy and tab-clean (artist credits, titles, `feat.`
  lists carry commas constantly and tabs almost never), so `tsv` is the cleaner delimited output and `cut -f` works
  without quoting. Both delimited formats serve different consumers — a shell pipeline vs. a sheet.

## Consequences

What `human`-plain strips versus keeps beyond colour and width-alignment (whether any structural adornment survives),
and the JSON envelope's shape ([ADR 0017](0017-choose-output-shape-with-format.md)), are designed when those slices
arrive. `show`'s view is nested (album → tracks → files), so it offers only `human` and `json`; the delimited shapes are
tabular and belong to the flat verbs.
