# 0017 — Choose output shape with `--format`

Status: Decided (2026-06-13)

Amended by [0019](0019-the-default-output-is-for-humans-not-parsers.md) (2026-06-13): an unset `--format` sends a pipe
the human format rendered plain, not a tab-separated record; the division of labour this record draws still stands.

## Decision

`leek list --format <shape>` chooses the structured form output takes. `<shape>` is a closed enum — `json` first, `csv`
likely — never a template ([ADR 0015](0015-reject-a-template-language-for-output.md)). Each shape renders from the typed
projection ([ADR 0014](0014-render-output-from-a-typed-projection.md)), so JSON emits a real integer for a bitrate and a
real `null` for an absence.

`--format` is orthogonal to `--fields` ([ADR 0016](0016-select-fields-with-fields.md)): `--fields` says which keys,
`--format` says what shape, and they compose without either knowing about the other
(`leek list --tracks --fields artist,bitrate --format json`).

When `--format` is unset, the `isatty` split stays: an aligned table to a terminal, a tab-separated record to a pipe
(ADR 0011). `--format` does not replace that automatic choice; it lets a caller name an explicit shape when the default
is not what they want — JSON onto a terminal, or into a pipe that would otherwise get TSV.

## Context

The need is machine consumption: feed `list` to `jq` or a script without parsing a human table or reverse-engineering
TSV. The shipped tab-separated pipe format is fine for `grep` but carries no typed or nested value, and re-poses the
"parse my TSV" fragility for every consumer. A named structured shape, rendered from typed values, keeps types intact
end to end. The enum is closed because user-authored "what shape" is a template again.

## Alternatives considered

- **A format-string template** — rejected in [ADR 0015](0015-reject-a-template-language-for-output.md). It is the open
  version of this option and carries every cost recorded there; `--format` is the closed, typed answer.
- **Tab-separated records forever** — the current pipe behaviour, kept as the unset default but insufficient as the only
  structured output: no types, no nesting, every consumer re-parsing strings. JSON is the honest machine shape.
- **A separate verb — `leek export`** — rejected: it scatters "the library, made visible" across two verbs that share
  all their machinery. `--format` keeps the concern on `list`; `dump` is claims and history, not the merged view
  (verbs.md).

## Consequences

The enum's shapes beyond `json`, the JSON envelope (array of objects vs. JSON Lines), the CSV dialect and whether it
carries a header, and how `--format` interacts with a non-TTY default are all open, designed when the slice arrives.
