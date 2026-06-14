# 0018 — Discover fields with `leek fields`

Status: Decided (2026-06-13)

Amended by [0019](0019-the-default-output-is-for-humans-not-parsers.md) (2026-06-13): the bare-names listing is human
output, not a scripting contract — scripts bind to `--format json`; the no-`isatty`-split observation stands.

## Decision

A new verb, `leek fields`, prints the field namespace a subject exposes — the discovery side of `--fields`
([ADR 0016](0016-select-fields-with-fields.md)). It selects its subject by option, mirroring `list`'s axis with the same
shared-`flag_value` "last option wins" semantics ([ADR 0013](0013-list-selects-its-entity-by-option.md)): `--albums`
(default), `--tracks`, `--artists`. `--genres` is unbuilt, for the same reason `list` left it out. It is one verb, one
concern (verbs.md): *what can be named*. It does not list the library (that is `list`) or examine an entity (that is
`info`); it reports the vocabulary, and `--fields` draws its selection from it, so the two always agree about what
exists.

Output is bare names, one per line, identical in a pipe and a TTY: the names are short reference data, so there is no
wrapping to fear and no `isatty` split. `--format json` is honoured for symmetry with `list`
([ADR 0017](0017-choose-output-shape-with-format.md)): it emits a JSON array of names. `leek fields` reads the same
`_FIELDS` map `--fields` validates against, so the pairing is structural, not a documented promise that could drift.

Names only, no types or descriptions. A field's type is in the typed projection
([ADR 0014](0014-render-output-from-a-typed-projection.md)), but the first need is "what can I name?", which a name list
answers. Types and descriptions stay deferred until a use asks for them — adding columns is easy later, un-adding a
shipped contract is not.

## Context

`--fields` ([ADR 0016](0016-select-fields-with-fields.md)) is only usable if you can find out what fields a subject has,
and the namespace is per subject (a track has `bitrate`; an artist has almost nothing). Without a discovery verb,
`--fields` is guesswork. beets answers this with `beet fields`. Adding a verb is a design decision (verbs.md), so it
gets this record and a row in the collection.

## Alternatives considered

- **No discovery verb — document the fields** — rejected: static docs drift from the code, and the namespace is per
  subject and grows as sources add claims. The tool reports its own vocabulary.
- **A `--list-fields` flag on `list`** — rejected: a flag doing a verb's job (ADR 0003), and it overloads `list`'s one
  concern with a second, "what can be named".
- **Fold it into `help`** — rejected: `help` is the reference for verbs; field names are data-shaped and subject-scoped,
  not command documentation.
