# 0017 — Choose output shape with `--format`

Status: Decided (2026-06-13)

## Decision

`leek list --format <shape>` chooses the structured form output takes. `<shape>` is a **closed enum** — `json` first,
`csv` likely — never a template ([ADR 0015](0015-reject-a-template-language-for-output.md)). Each shape renders from the
typed projection ([ADR 0014](0014-render-output-from-a-typed-projection.md)), so JSON emits a real integer for a
bitrate, a real `null` for an absence — the honest typed output beets could never produce because it had no typed seam.

`--format` is *orthogonal* to `--fields` ([ADR 0016](0016-select-fields-with-fields.md)): `--fields` says *which* keys,
`--format` says *what shape*. They compose without either knowing about the other —
`leek list --tracks --fields artist,bitrate --format json` is the two axes meeting, and neither is privileged over the
table.

The shipped behaviour is the **default when `--format` is unset**: the `isatty` split stays — an aligned table to a
terminal, a tab-separated record to a pipe (ADR 0011). `--format` does not replace that automatic choice; it lets a
caller name an explicit shape when the default is not what they want (a script that wants JSON even into a pipe that
would otherwise get TSV, or onto a terminal).

**Grammar deferred to contact.** Which shapes the enum holds beyond `json`, the JSON envelope (array of objects vs. JSON
Lines), the CSV dialect and whether it carries a header, and how `--format` interacts with a non-TTY default are
designed when the slice arrives.

## Context

The need is machine consumption: feed `list` to `jq` or a script without parsing a human table or reverse-engineering
TSV. The shipped pipe format (tab-separated records) is the floor — fine for `grep`, but it cannot carry a typed value
or a nested one, and it re-poses the "parse my TSV" fragility for every consumer. A named structured shape, rendered
from typed values, removes the parsing dance and keeps types intact end to end. The enum is closed on purpose: the
moment "what shape" becomes user-authored, it is a template again.

## Alternatives considered

- **A format-string template** — rejected in [ADR 0015](0015-reject-a-template-language-for-output.md). It is the open
  version of this option and carries every cost recorded there; `--format` is the closed, typed answer.
- **Tab-separated records forever** — the current pipe behaviour, kept as the unset default but insufficient as the only
  structured output: no types, no nesting, every consumer re-parsing strings. JSON is the honest machine shape.
- **A separate verb — `leek export`** — beets' shape, and it scatters "the library, made visible" across two verbs that
  share all their machinery. `--format` keeps the concern on `list`; export is `dump`'s job, and `dump` is claims and
  history, not the merged view (verbs.md).
