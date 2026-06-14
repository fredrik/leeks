# 0012 — Base the query language on beets

Status: Decided (2026-06-13)

## Decision

When leeks grows querying beyond `leek list`'s bare substring terms (ADR 0011), the query language is
**beets-inspired**: it preserves the terse, guessable surface — bare terms, `field:value`, ranges, and the obvious
composition of them — that makes beets a joy to live with, and joy is a project requirement (project-principles).

This binds the direction, not the grammar. Which fields, which operators, how negation and OR and per-track search spell
out are deferred to the slice that builds them (ADR 0011's punt stands). What is settled is that the design starts from
beets' query surface rather than inventing a syntax or reaching for a general expression language.

Two constraints come with the inheritance, both from beets' scar tissue (ADR 0011 records them):

- **The grammar is a designed artifact, written down — it does not accumulate.** beets' language grew operator by
  operator until its semantics lived in the parser (a colon inside a search term silently becomes a field query; case
  rules differ between query types). leeks writes the grammar deliberately, once, against what real queries ask for.
- **It compiles to SQL over the typed, normalised schema — not over a stringly-typed substrate.** beets negotiates types
  at query time because everything is a string; leeks has real columns and foreign keys, so `year:2019..2021` is a typed
  comparison, not a string match.

## Context

ADR 0011 shipped `leek list` with bare substring terms and left open *how queries grow*, calling a field-qualified
language plausible but undesigned and declining to design it ahead of real use. That punt settled the floor without
settling the direction. beets' query language is a major part of why beets is pleasant to live with, and leeks — which
exists to fix beets' data model, not to discard what beets got right — inherits it. Recording the direction now keeps it
from being re-litigated each time querying comes up.

This changes nothing today: `leek list` keeps its bare terms, which are already a forward-compatible subset
(`leek list radiohead` means the same thing under any beets-style grammar).

## Alternatives considered

- **Leave the direction open (ADR 0011's punt, unmodified)** — rejected: it treats a settled preference as unsettled and
  invites the same conversation again.
- **A general expression language** (SQL-ish `WHERE`, or a query DSL) — rejected: more powerful, but it trades the
  guessable surface for one that has to be learned, and the guessable surface is the valuable part.
- **Design the full grammar now** — rejected: nothing yet shows which operators real leeks queries reach for, and the
  typed schema is still filling in.

## Consequences

Querying grows when a real query demands more than substring terms — plausibly with the second source, when there is
disagreement worth filtering on. The grammar itself stays deferred until then.
