# 0015 — Reject a template language for output

Status: Decided (2026-06-13)

## Decision

`leek` will not have a format-string template language — no `leek list -f '$artist - $album'`, no `%if{}`, no functions,
no interpolation of literal text between fields. Output is controlled by two narrow, orthogonal choices instead:
*selection* (which fields print, [ADR 0016](0016-select-fields-with-fields.md)) and *shape* (which structured form,
[ADR 0017](0017-choose-output-shape-with-format.md)), both reading the typed projection
([ADR 0014](0014-render-output-from-a-typed-projection.md)).

The boundary is precise: a template conflates two things, and the conflation *is* the language. **Selection** — naming
which fields to print — is a list of names, not a language. **Interpolation** — the literal text, separators, and
conditionals *between* fields — is the entire language: the parser, the escaping, the functions all exist to serve it.
leek gives selection and withholds interpolation. When you need a bespoke line with your own punctuation, the shell
composes it: `leek list --format json | jq -r '...'`. leek emits clean typed data; string assembly belongs to the tool
built for string assembly.

## Context

beets' `-f` is the scar tissue. It began as "let me pick a field" and grew, one reasonable commit at a time, into a DSL
with its own escaping, functions (`%if{}`, `%aunique{}`, `%the{}`, …), and bugs — a second runtime nobody set out to
ship, with the shape of its own history rather than of a decision. Three costs follow, and they are the reason for the
firm no:

- **It is a second runtime.** An undesigned language embedded in a music tool, that every plugin must then understand,
  that grows by accretion exactly the way the soul warns against.
- **It makes field names a permanent API.** The moment `-f '$mb_albumid'` works, the internal field name is a public
  interface carried in shell history and scripts. beets' field names are sticky for this reason — a verified core of its
  2010 names survives today (the set grew several-fold around them, and a couple were pluralised, so "sticky," not
  "frozen"). Templates are one of three things — alongside queries and configs — that make any rename break users.
- **It invites computation into the presentation layer.** Once the template can branch, logic moves into an untyped,
  untestable string that the type checker never sees.

The clinching cost is the one [ADR 0014](0014-render-output-from-a-typed-projection.md) records: a template flattens
every value to a string at the boundary, foreclosing honest typed output. beets proves it — its JSON export rides
`formatted()` because the template world *is* the string world, and the two never reconciled. And in beets the
path-format engine shares the same template machinery, so a template bug's blast radius includes files on disk, not just
a printed line. leek will never let the formatted string become a field's only public form.

The legitimate daily use behind `-f` — "show me field X across these results" — is *selection*, and it is served, by
`--fields`. Nothing real is lost.

## Alternatives considered

- **Ship a template language** — the thing rejected. It buys bespoke one-liners at the cost of a second runtime, field
  names as a forever-API, and the foreclosure of typed output. The 80% need (selection) does not require it, and the 20%
  (interpolation) is the shell's job.
- **Allow a sliver of interpolation** — say, a single `--separator` or a join string. This is the seed of the same
  language: the first literal-text-between-fields knob invites the second, and the conditional after that. Cleaner to
  hold the line at selection and let the shell interpolate.
- **Say nothing and decide on contact** — but the no *shapes* `--fields` and `--format`: it is why those are a name list
  and a closed enum rather than a template. Recording it now is what keeps the next two records small.
