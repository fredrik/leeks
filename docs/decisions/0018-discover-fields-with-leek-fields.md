# 0018 — Discover fields with `leek fields`

Status: Decided (2026-06-13)

## Decision

A new verb, `leek fields`, prints the field namespace a subject exposes — the discovery side of `--fields`
([ADR 0016](0016-select-fields-with-fields.md)). It selects its subject by option, mirroring `list`'s axis
([ADR 0013](0013-list-selects-its-entity-by-option.md)): `leek fields --tracks`, `--artists`, `--genres`, `--albums`,
defaulting to albums. Each prints the names `--fields` can name for that subject, read from the same typed projection
every formatter reads ([ADR 0014](0014-render-output-from-a-typed-projection.md)).

The pairing is the point: `--fields` is *selection*, `leek fields` is the *namespace* that selection draws from, and
they share the subject axis so the two always agree about what exists. Without it, `--fields` is guesswork — you would
have to already know the names, beets' situation, where the field set is an archaeology dig.

This is one verb, one concern (verbs.md): *what can be named*. It does not list the library (that is `list`) or examine
an entity (that is `info`); it reports the vocabulary.

**Grammar deferred to contact.** Its own output shape (it should plausibly honour `--format` like any listing), whether
each field carries a one-line description or a type, and how the subjects' namespaces overlap are designed when the
slice arrives.

## Context

`--fields` ([ADR 0016](0016-select-fields-with-fields.md)) is only usable if you can find out what fields a subject has,
and the namespace is per subject (a track has `bitrate`; an artist has almost nothing). beets answers this with
`beet fields`; the need is real and the verb is the natural home. Adding a verb is a design decision (verbs.md), so it
gets this record and a row in the collection.

## Alternatives considered

- **No discovery verb — document the fields** — static docs drift from the code, and the namespace is per subject and
  will grow as sources add claims. The tool should report its own vocabulary, the way it reports its own version.
- **A `--list-fields` flag on `list`** — a flag doing a verb's job (ADR 0003), and it overloads `list`'s one concern
  ("the library, made visible") with a second ("what can be named"). A small verb is cleaner than a flag that changes
  what `list` is for.
- **Fold it into `help`** — `help` is the reference for *verbs*; field names are data-shaped and subject-scoped, not
  command documentation. They belong with the data, behind their own verb.
