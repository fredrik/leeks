# 0021 — Fold case and accents for search and sort

Status: Decided (2026-06-14)

## Decision

The library folds case and diacritics, the Unicode way, for two query-time concerns — **search** and **sort** — and
leaves **identity** alone. Concretely, the `connect` hook in `db.py`:

- overrides SQLite's `like` function so `icontains` matches ignoring case and accents — `åsa`, `Åsa`, and `asa` all find
  `Åsa Vinterhök`;
- registers a `FOLD` collation used by every `ORDER BY` in `library.py`, so accented names shelve among their base
  letters (`Åsa` among the A's) instead of past Z.

A single `fold` function — NFKD, strip combining marks, casefold — backs both, and dissolving to NFKD also makes a word
match whichever normalisation (NFC/NFD) it was stored in.

Crucially, the builtin `NOCASE` collation is **not** overridden. The unique `Artist.name` and `Genre.name` columns keep
leaning on it, so identity stays case-folded but accent-distinct: `Daft Punk` and `Daft punk` remain one artist, while
`Åsa` and `Asa` remain two. No schema change, no migration.

## Context

SQLite's built-in `LIKE` operator and `NOCASE` collation only understand case for ASCII A–Z. They fold `V`/`v` but not
`Å`/`å`. So `leek list åsa` found nothing while `leek list Åsa` and `leek list vinter` both worked — a discrepancy that
surfaces the moment a library holds non-ASCII names, which a music organiser does on day one.

The honest root cause is "SQLite's defaults are ASCII-only," so the fix lives where the connection is opened, not
scattered through every query. The stdlib `sqlite3` driver lets an application override both: `LIKE` dispatches to a
function named `like` that `create_function` can replace, and `create_collation` can supply named collations. Python's
`re` and `unicodedata` fold the Unicode way for free. The cost is that an overridden `LIKE` forgoes index use, which is
irrelevant here — the queries already scan with a leading `%`, and the library is personal-scale.

Folding accents (so `asa` finds `Åsa`) was a deliberate kindness to anyone whose keyboard lacks å/ä/ö, beyond plain case
folding. It does mean sort order no longer follows Swedish alphabetisation (å/ä/ö last); folded order keeps accented
names with their base letters, predictable and consistent with search. Locale-correct collation is a larger, separate
undertaking if it ever earns its keep.

The sharp edge was the *blast radius* of folding. `NOCASE` is one name, and the unique `Artist.name`/`Genre.name`
columns use it for identity — the find-or-create that decides whether two tagged spellings are the same artist.
Overriding `NOCASE` would have silently folded accents *there too*, merging `Beyoncé` and `Beyonce` into one artist and
requiring a `REINDEX` of existing libraries. That is a real identity decision, separate from the search convenience the
bug report asked for, so search and sort fold while identity is left untouched — accent-folding identity can be its own
record if it ever earns one.

## Alternatives considered

- **Override the builtin `NOCASE` globally** — one concept, the least code, and it fixes search and sort in a line. But
  it folds accents into *identity*: `Åsa`/`Asa` and `Beyoncé`/`Beyonce` collapse to one artist on `add`, and an existing
  on-disk unique index built under ASCII `NOCASE` needs a `REINDEX` to stay consistent. Merging artist identity across
  accents is a heavier, separate decision; the surgical split above buys the requested behaviour without it.
- **A normalised, folded shadow column** indexed for search — the textbook scale answer. It carries a schema change,
  Alembic migration, and the discipline of keeping the column in sync on every write, to buy index performance a
  personal library will never need.
- **The ICU extension**, which provides a Unicode-aware `LIKE` — not bundled with the stdlib `sqlite3`, so it adds a
  build/deploy dependency to replace a dozen lines of Python.
- **Case only, no accent folding** — correct but less kind; `asa` would still miss `Åsa`, exactly the friction a
  non-native hits. Rejected in favour of the more forgiving search.
