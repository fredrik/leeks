# 0012 — The query language is beets-inspired

Status: Decided (2026-06-13)

## Decision

When leeks grows querying beyond `leek list`'s bare substring terms (ADR 0011), the query language is
**beets-inspired**: it preserves the terse, guessable surface that makes beets a joy to use — bare terms, `field:value`,
ranges, and the obvious composition of them — because that surface is one of the things that makes beets a joy, and joy
is a project requirement, not a garnish (project-principles).

This decides the *direction*, not the grammar. The grammar is still designed when a real query forces it (ADR 0011's
punt stands): which fields, which operators, how negation and OR and per-track search spell out, are deferred to the
slice that builds them. What is settled now is that the design starts from beets' query surface as the thing to learn
from and preserve, rather than inventing a syntax or reaching for a general expression language.

Two constraints come with the inheritance, both from beets' scar tissue (ADR 0011 records them):

- **The grammar is a designed artifact, written down — it does not accumulate.** beets' language grew operator by
  operator until its semantics lived in the parser (a colon inside a search term silently becomes a field query; case
  rules differ between query types). leeks writes the grammar deliberately, once, against what real queries ask for.
- **It compiles to SQL over the typed, normalised schema — not over a stringly-typed substrate.** beets negotiates types
  at query time because everything is a string; leeks has real columns and foreign keys, so `year:2019..2021` is a typed
  comparison, not a string match. This is the half of beets' design leeks improves on rather than copies.

## Context

ADR 0011 shipped `leek list` with bare substring terms and explicitly left open *how queries grow*, calling a
field-qualified language plausible but undesigned and declining to design it ahead of real use. That punt deliberately
settled the floor without settling the direction.

The direction is now settled: beets' query language is a major part of why beets is pleasant to live with, and leeks —
which exists to fix beets' data model, not to discard what beets got right — should inherit that pleasure. Recording the
decision now keeps it from being re-litigated each time querying comes up, and gives the eventual query slice its
starting point. It changes nothing today: `leek list` keeps its bare terms, which are already a forward-compatible
subset (`leek list radiohead` means the same thing under any beets-style grammar).

The decision binds a direction, not a schedule. Querying grows when a real query demands more than substring terms —
plausibly with the second source, when there is disagreement worth filtering on.

## Alternatives considered

- **Leave the direction open (ADR 0011's punt, unmodified)** — defensible, but it treats a settled preference as
  unsettled. The maintainer has decided; an undecided record would invite the same conversation again.
- **A general expression language** (SQL-ish `WHERE`, or a query DSL) — more powerful, but it trades the terse,
  guessable surface for one that has to be learned. beets' lesson is that the guessable surface is the valuable part.
- **Design the full grammar now** — the speculation ADR 0011 declined for good reason; nothing yet shows which operators
  real leeks queries reach for, and the typed schema is still filling in. Direction now, grammar on contact.
