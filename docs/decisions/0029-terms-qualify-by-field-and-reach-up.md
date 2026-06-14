# 0029 — Terms qualify by field and reach up the tree

Status: Decided (2026-06-14)

## Decision

`leek list` and `leek show` grow their query from bare substring terms (ADR 0011) into **field-qualified substring
terms**. The grammar, in one rule:

> A term is `[field:]value`. It matches case-insensitively, by substring. **Bare** (`radiohead`) fans across the
> subject's descriptive fields. **Qualified** (`title:karma`) matches the one named field. Terms still AND together (ADR
> 0011). `id:N` stays the one *exact* selector it already is (ADR 0020).

**Qualified terms name a field from the subject's own namespace.** The names a term may qualify by are exactly the names
`leek fields` lists and `--fields` selects (ADRs 0016, 0018) — one set of names, three uses: discover, select, filter. A
term naming a field outside that namespace fails loudly, listing the valid names, as `--fields` already does. leeks has
one typed projection (ADR 0014), so it has one namespace; beets kept query fields and template fields as
overlapping-but-different sets.

**Bare terms reach up the tree.** A bare term fans across the listed subject's *descriptive* fields, including the
fields it borrows from its parents across a foreign key:

- albums → artist, title, year *(unchanged from ADR 0011)*
- tracks → artist, album, title
- artists → name *(unchanged)*

So `leek list --tracks radiohead computer` returns the tracks of *OK Computer* — artist and album both matched, ANDed.
beets bought this convenience by denormalising — copying the album's fields onto every track row, the founding annoyance
this project exists to undo. leeks reaches at query time, over the real foreign keys, with the schema fully normalised
(core positions): a join, not a copy.

**The match is a substring; the value's type does not change that.** `year:1999` matches by substring like every other
term — for four-digit years, exact in practice. leeks introduces no typed comparison here, though the schema could carry
one. ADR 0012's typed example was the range `year:2019..2021`, and ranges are deferred (below); a plain `year:1999`
needs only the substring rule. Year earns a typed comparison when the range operator arrives, not before. `id:N` is the
sole exception: it is identity selection (ADR 0020), so it compares the integer primary key exactly, and bare terms
never fan across it.

**A set-valued field filters by membership.** `genre:folk` filters albums by genre. Genre is in the listable namespace
(ADR 0023: `genres`, a set held through the AlbumGenre junction), so the one-namespace rule makes it filterable too.
Both `genre:` and `genres:` work — the singular is an alias, `genres` stays the one name `leek fields` shows and
`--fields` selects. Because genre is relational the qualifier is a membership test — an EXISTS over the junction, not a
substring on a column — but the reach is still a query-time join, storage untouched. It is scoped to albums; a track
genre, reaching up to the album's, is the natural next step, deferred until wanted.

### Deferred, still on contact (ADR 0012)

Ranges (`year:1990..1999`), comparisons (`>`, `<`), negation (`-live`), alternation (OR), sort terms, and absence
queries (`year:` for "missing a year") are unbuilt. None is needed by the queries that forced this slice (`year:1999`,
`title:karma`, the cross-entity `--tracks radiohead computer`, `genre:folk`). Each arrives when a real query reaches for
it, extended deliberately and written down, not accumulating in the parser (ADR 0012). The substring grammar is a
forward-compatible subset of every one: `radiohead` and `title:karma` mean the same thing under any of them.

## Context

ADR 0011 shipped `list` with bare substring terms and punted on how queries grow. ADR 0012 settled the direction —
beets-inspired surface, compiled to SQL over the typed normalised schema — and ADR 0013 named the hard question it left
open: in a normalised world, does a `--tracks` term reach up to the album's artist? Both deferred the grammar to the
slice that builds it, when a real query demands more than substring terms.

A real query now does: `year:1999`, `genre:folk`, and `leek list --tracks radiohead computer` — the first two qualify a
term by a field, the third reaches across the tree. It asks for field qualification and cross-entity reach and nothing
else, so the slice designs only that. The reach resolves toward beets' convenience because a query surface should reason
from the user's mental model, and the user's track owns its artist and album. ADR 0013's objection — that cross-entity
matching in beets was a side effect of storage — is answered by making it explicit here: normalised data, an explicit
join. The duplication is what leeks rejected, not the matching.

## Alternatives considered

- **Keep bare terms local to the listed entity** — rejected on UX. The user neither sees nor cares that artist lives on
  another row; refusing `leek list --tracks radiohead computer` punishes them for an implementation detail, and the
  discipline that matters — normalised storage — is untouched by a query-time join.
- **Type the comparison now** (`year:1999` as integer equality, ranges and `>`/`<` alongside) — rejected: it builds
  operators no current query asks for and splits one rule (everything is substring) into two (text substring, number
  compared). Substring serves `year:1999` exactly; the typed comparison earns its place when ranges arrive.
- **A superset query namespace** (some fields queryable but not listable, beets' query-vs-template split) — rejected: it
  re-creates the two-namespace tangle the one typed projection avoids. If you can name a field, you can discover,
  select, and filter on it.
- **Design the whole grammar now** (negation, OR, ranges, sort) — rejected: nothing yet shows which of these real leeks
  queries reach for, the speculation ADRs 0011, 0012, and 0013 each declined.
