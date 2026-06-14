# 0029 — Terms qualify by field and reach up the tree

Status: Decided (2026-06-14)

## Decision

`leek list` and `leek show` grow their query from bare substring terms (ADR 0011) into **field-qualified substring
terms**. The grammar, in one rule:

> A term is `[field:]value`. It matches case-insensitively, by substring. **Bare** (`radiohead`) fans across the
> subject's descriptive fields. **Qualified** (`title:karma`) matches the one named field. Terms still AND together (ADR
> 0011). `id:N` stays the one *exact* selector it already is (ADR 0020).

This settles, in turn, several questions ADRs 0012 and 0013 deferred to "the slice that builds them":

**Qualified terms name a field from the subject's own namespace.** The names a term may qualify by are exactly the names
`leek fields` lists and `--fields` selects (ADRs 0016, 0018) — one set of names, now three uses: discover it, select it,
filter on it. A term naming a field outside that namespace fails loudly, listing the valid names, the same way
`--fields` already rejects an unknown field. beets kept its query fields and its template fields as
overlapping-but-different sets, and flexible attributes blurred the line further; leeks has one typed projection (ADR
0014), so it has one namespace.

**Bare terms reach up the tree.** A bare term fans across the listed subject's *descriptive* fields, and those include
the fields it borrows from its parents across a foreign key:

- albums → artist, title, year *(unchanged from ADR 0011)*
- tracks → artist, album, title
- artists → name *(unchanged)*

So `leek list --tracks radiohead computer` returns the tracks of *OK Computer* — artist and album both matched, ANDed —
which is what anyone picturing a track expects, because in the user's head a track *contains* its artist and its album.
This is beets' convenience, and we keep it deliberately. The crucial line is *where* the reach lives: beets bought it by
**denormalising** — copying the album's fields onto every track row — and that duplication is the founding annoyance
this project exists to undo. leeks reaches at **query time**, over the real foreign keys, with the schema fully
normalised (core positions). Convenience in the surface; honesty in the storage. The reach is a join, not a copy.

**The match is a substring, and the value's type does not yet change that.** `year:1999` matches by substring like every
other term — which, for four-digit years, is exact in practice. leeks does *not* introduce a typed comparison here, even
though the schema could support one. ADR 0012's typed example was `year:2019..2021`, a **range**, and ranges are
deferred (below); a plain `year:1999` needs nothing more than the substring rule. When the range operator arrives on
contact, *that* is the moment year earns a typed comparison — not before. `id:N` is the sole exception: it is identity
selection (ADR 0020), so it compares the integer primary key exactly, and bare terms never fan across it.

**A set-valued field filters by membership.** `genre:folk` filters albums by genre. Genre entered the *listable*
namespace in ADR 0023 (`genres`, a set held through the AlbumGenre junction), so the one-namespace rule requires it be
*filterable* too — so it is, rather than left as a gap. Both `genre:` and `genres:` work: the singular is an alias,
while `genres` stays the one name `leek fields` shows and `--fields` selects. Because genre is relational, the qualifier
is a *membership* test — an EXISTS over the junction, not a substring on a column — but the reach to the genre table is
still a query-time join, storage untouched. It is scoped to albums, where genre is listable; giving *tracks* a genre —
reaching up to the album's, and listing it — is the natural next step, deferred until wanted.

### Deferred, still on contact (ADR 0012)

Ranges (`year:1990..1999`), comparisons (`>`, `<`), negation (`-live`), alternation (OR), sort terms, and absence
queries (`year:` for "missing a year") are all unbuilt. None is needed by the queries that forced this slice
(`year:1999`, `title:karma`, the cross-entity `--tracks radiohead computer`, and `genre:folk`). Each arrives when a real
query reaches for it, and the grammar is extended deliberately, written down — it does not accumulate in the parser (ADR
0012). The substring grammar is a forward-compatible subset of every one of these: `radiohead` and `title:karma` mean
the same thing under any of them.

## Context

ADR 0011 shipped `list` with bare substring terms and explicitly punted on how queries grow. ADR 0012 settled the
*direction* — beets-inspired surface, compiled to SQL over the typed normalised schema — and ADR 0013 named the one hard
question that direction left open: in a normalised world, does a `--tracks` term reach up to the album's artist? Both
records deferred the grammar itself to "the slice that builds it, when a real query demands more than substring terms."

A real query now does. The maintainer wants `year:1999`, `genre:folk`, and `leek list --tracks radiohead computer` — the
first two qualify a term by a field, the third reaches across the tree. That is the contact ADRs 0012 and 0013 were
waiting for, and it is small: it asks for field qualification and cross-entity reach, and for nothing else. Designing
only what the query forces keeps faith with "direction now, grammar on contact" while finally answering 0013's question.

The reach question resolved toward beets' convenience, but for a sharper reason than convenience: a query surface should
reason from the user's mental model, and the user's track owns its artist and album. The objection in ADR 0013 — that
cross-entity matching in beets was "a side effect of storage" — is answered by making it *not* a side effect of storage
here: the data stays normalised and the reach is an explicit join. The half of beets we rejected was the duplication,
not the matching.

## Alternatives considered

- **Keep bare terms local to the listed entity** — the position this record's author first argued: reason from the
  schema, not the file, and don't let a track pretend to own an artist. It lost on UX. The user neither sees nor cares
  that artist lives on another row; refusing `leek list --tracks radiohead computer` punishes them for an implementation
  detail. The discipline that actually matters — normalised storage — is untouched by a query-time join.
- **Type the comparison now** (`year:1999` as integer equality, ranges and `>`/`<` alongside) — more faithful to ADR
  0012's typed-schema promise, and the schema could carry it. But it builds operators no current query asks for, and it
  splits one simple rule (everything is substring) into two (text substring, number compared). Substring serves
  `year:1999` exactly; the typed comparison earns its place when ranges arrive, and not as speculation before.
- **A superset query namespace** — let some fields be queryable but not listable (beets' query-vs-template split). It
  re-creates the two-namespace tangle leeks avoids by having one typed projection. If you can name a field, you can
  discover, select, and filter on it; no field is queryable-but-invisible.
- **Design the whole grammar now** (negation, OR, ranges, sort) — the speculation ADRs 0011, 0012, and 0013 each
  declined for good reason. Nothing yet shows which of these real leeks queries reach for. Grammar on contact.
