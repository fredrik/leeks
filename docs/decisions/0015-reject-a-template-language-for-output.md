# 0015 — Reject a template language for output

Status: Decided (2026-06-13)

## Decision

`leek` will not have a format-string template language — no `leek list -f '$artist - $album'`, no `%if{}`, no functions,
no interpolation of literal text between fields. Output is controlled by two narrow, orthogonal choices instead:
*selection* (which fields print, [ADR 0016](0016-select-fields-with-fields.md)) and *shape* (which structured form,
[ADR 0017](0017-choose-output-shape-with-format.md)), both reading the typed projection
([ADR 0014](0014-render-output-from-a-typed-projection.md)).

The boundary is two things a template conflates. **Selection** — naming which fields to print — is a list of names.
**Interpolation** — the literal text, separators, and conditionals between fields — is the language: the parser, the
escaping, the functions all serve it. leek gives selection and withholds interpolation. A bespoke line with your own
punctuation is the shell's job: `leek list --format json | jq -r '...'`. leek emits clean typed data; string assembly
belongs to the tool built for it.

## Context

beets' `-f` is the scar tissue: it began as "let me pick a field" and grew into a DSL with its own escaping, functions
(`%if{}`, `%aunique{}`, `%the{}`, …), and bugs — a second runtime nobody set out to ship. Four costs make the no firm:

- **It is a second runtime** — an undesigned language embedded in a music tool, that every plugin must understand, grown
  by accretion.
- **It makes field names a permanent API.** Once `-f '$mb_albumid'` works, the internal field name is a public interface
  carried in shell history and scripts. beets' field names are sticky for this reason — a core of its 2010 names
  survives today (the set grew several-fold around them, a couple pluralised, so "sticky," not "frozen"). Templates are
  one of three things — with queries and configs — that make any rename break users.
- **It invites computation into the presentation layer.** A template that can branch moves logic into an untyped,
  untestable string the type checker never sees.
- **It forecloses honest typed output** ([ADR 0014](0014-render-output-from-a-typed-projection.md)): a template flattens
  every value to a string at the boundary. beets' JSON export rides `formatted()` for this reason, and its path-format
  engine shares the same template machinery, so a template bug reaches files on disk, not just a printed line.

The legitimate daily use behind `-f` — "show me field X across these results" — is selection, served by `--fields`.

## Alternatives considered

- **Ship a template language** — rejected: it buys bespoke one-liners at the cost of a second runtime, field names as a
  forever-API, and the foreclosure of typed output. Selection does not require it; interpolation is the shell's job.
- **Allow a sliver of interpolation** (a `--separator`, a join string) — rejected: the first literal-text-between-fields
  knob is the seed of the same language and invites the next. Hold the line at selection.

## Consequences

The no shapes `--fields` and `--format`: it is why those are a name list and a closed enum rather than a template.
