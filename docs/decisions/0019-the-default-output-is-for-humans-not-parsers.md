# 0019 — The default output is for humans, not parsers

Status: Decided (2026-06-13)

## Decision

The default output — what `leek list` prints when `--format` is unset — is `human`, always, and it is **for reading,
never for parsing**. Its bytes are not a contract: the human formatter is free to change its columns, spacing,
adornment, and wording from one release to the next, because nothing is entitled to parse them. Machine consumption is
what `--format` is for ([ADR 0017](0017-choose-output-shape-with-format.md)); that is the whole division of labour.

The `isatty` boundary governs **presentation, not format**. A terminal gets the themed, aligned table; a pipe gets the
same `human` formatter rendered *plain* — no colour, no terminal-width alignment. Same formatter, two renderings — the
`ls`/`git` discipline, where colour and layout adapt to the tty but the format does not silently switch under you
(`git log` piped is still `git log`, not `--porcelain`; you ask for porcelain by name). `--format human` names this
default explicitly, so a script can force the readable shape into a pipe, or onto a terminal, when it wants it.

The machine formats are an explicit, opt-in set — never auto-selected by a pipe:

- **`json`** — the structured, typed, nestable shape; real integers, real `null`s
  ([ADR 0014](0014-render-output-from-a-typed-projection.md)). For programs (`jq`, anything that wants the types
  intact).
- **`csv`** — the spreadsheet lingua franca (Excel, Numbers, pandas). For "dump my library into a sheet."
- **`tsv`** — the shell-pipeline delimited shape; `cut -f2` just works.

A consumer reaches for one of these by name, and *that naming is what earns the stability contract*. A pipe selecting a
machine format on its own would invoke that contract by accident, which is exactly what we refuse.

This **revises the unset-default behaviour** recorded in [ADR 0011](0011-list-is-albums-in-shelf-order.md),
[ADR 0013](0013-list-selects-its-entity-by-option.md), and [ADR 0017](0017-choose-output-shape-with-format.md): the pipe
no longer receives a tab-separated *record*. That output was a machine format reached by accident; it becomes the plain
rendering of the human format, and TSV survives only as an explicit `--format tsv`. The rest of those records stands —
this changes one clause, the shape an unset `--format` sends to a pipe.

## Context

The thread is the default output's job. Fredrik's framing of why `human` is the right default: it is great *because* we
can print anything we want and not be beholden to parsability. That freedom is real, and it survives exactly as long as
nobody is entitled to parse the default. The shipped behaviour quietly spent it: a pipe got a tab-separated record, so
the moment `leek list | cut -f2` works out of the box, that column order is a frozen contract — invoked by accident,
owed forever, on output nobody deliberately asked to stabilise. The freedom Fredrik named and the auto-TSV pipe default
cannot both hold; this record keeps the freedom.

This is the same scar `--format` already steers by. beets had exactly one public view of a field — the formatted string
([ADR 0014](0014-render-output-from-a-typed-projection.md)) — so the human form and the machine form were never
separable, and structured output inherited the string flattening. The lesson generalises to the pipe: when the readable
output and the parseable output are the *same bytes*, the readable one cannot move without breaking a parser. Keeping
them distinct — human for eyes, named formats for machines — is what lets the human side stay free.

`isatty` is still the right signal, pointed at the right thing. It answers "is a person watching?", which is a question
about *presentation* — colour, alignment, width. It is not a proxy for "does the caller want a machine format," and the
shipped default conflated the two. A pipe means "strip the adornment," not "switch to a contract."

The human-plain rendering is plainer, but it is **still not a contract**: its stability is not promised either. A caller
that wants stable output uses `--format`. This binds every verb, with no exceptions. `leek fields`
([ADR 0018](0018-discover-fields-with-leek-fields.md)) looks like one — its bare-names listing is identical in a pipe
and a terminal — but that is because field names have *no presentation to strip*, so the plain and themed renderings
coincide; it is "presentation, not format" with nothing to vary, not a licence to parse. A script that wants the field
namespace uses `leek fields --format json`, the machine path 0018 already provides. This **corrects 0018's "stable for
scripting" framing** of that human listing: the no-`isatty`-split observation stands, but the human output is for
reading there too — the contract a script binds to is the JSON, never the bare-names default.

## Alternatives considered

- **Tab-separated record on a pipe** — the shipped default ([ADRs 0011](0011-list-is-albums-in-shelf-order.md),
  [0013](0013-list-selects-its-entity-by-option.md), [0017](0017-choose-output-shape-with-format.md)). Convenient —
  `leek list | awk` just works with no flag — but the convenience *is* the trap: it is a parse contract reached by
  accident, and it makes TSV, not human, the thing on the wire. The eight characters of `--format tsv` buy a deliberate
  contract instead of an accidental one.
- **JSON on a pipe** — the same flaw as auto-TSV with a bigger blast radius: it also surprises `| less` and `| grep`
  with a shape no one asked for, and commits us to the JSON envelope's stability by accident rather than by request.
- **No split at all — same output to terminal and pipe** — either loses the themed table (plain everywhere) or ships
  colour codes and width-padding into pipes (table everywhere). The split is good; it just has to be presentation-only,
  not a format switch.
- **Drop `tsv`, keep `csv` + `json`** — declined. In this domain the data is comma-heavy and tab-clean — artist credits,
  titles, `feat.` lists carry commas constantly and tabs almost never — so `tsv` is the *cleaner* delimited output and
  `cut -f` works without quoting. If either delimited format were on the bubble it would be `csv`, justified only by
  spreadsheet import; both earn their place because they serve different consumers (a shell pipeline vs. a sheet).

## Grammar deferred to contact

Exactly what `human`-plain strips versus keeps (colour and width-alignment, certainly; whether any structural adornment
survives), and the machine dialects already deferred by [ADR 0017](0017-choose-output-shape-with-format.md) — the JSON
envelope, the CSV/TSV header and quoting rules — are designed when the slice arrives. This record fixes only the
division: the default is for humans and is not a contract; machines ask by name.
