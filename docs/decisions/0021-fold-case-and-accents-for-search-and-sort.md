# 0021 — Fold case and accents for search and sort

Status: Decided (2026-06-14)

## Decision

The library folds case and diacritics, the Unicode way, for two query-time concerns — **search** and **sort** — and
leaves **identity** alone. Concretely, the `connect` hook in `db.py`:

- overrides SQLite's `like` function so `icontains` matches ignoring case and accents — `åsa`, `Åsa`, and `asa` all find
  `Åsa Vinterhök`;
- registers a `FOLD` collation used by every `ORDER BY` in `library.py`, so accented names shelve among their base
  letters (`Åsa` among the A's) instead of past Z.

A single `fold` function — NFKD, strip combining marks, casefold — backs both; NFKD also makes a word match whichever
normalisation (NFC/NFD) it was stored in.

The builtin `NOCASE` collation is **not** overridden. The unique `Artist.name` and `Genre.name` columns keep using it,
so identity stays case-folded but accent-distinct: `Daft Punk` and `Daft punk` remain one artist, `Åsa` and `Asa` remain
two. No schema change, no migration.

## Context

SQLite's built-in `LIKE` operator and `NOCASE` collation understand case only for ASCII A–Z: they fold `V`/`v` but not
`Å`/`å`. So `leek list åsa` found nothing while `leek list Åsa` and `leek list vinter` both worked — a discrepancy that
surfaces the moment a library holds non-ASCII names, which a music organiser does on day one. The root cause is
ASCII-only defaults, so the fix lives where the connection is opened, not scattered through every query.

The stdlib `sqlite3` driver lets an application override both: `LIKE` dispatches to a function named `like` that
`create_function` can replace, and `create_collation` supplies named collations; `re` and `unicodedata` fold the Unicode
way. An overridden `LIKE` forgoes index use, which is irrelevant here — the queries already scan with a leading `%`, and
the library is personal-scale.

Folding accents (so `asa` finds `Åsa`) goes beyond case folding for anyone whose keyboard lacks å/ä/ö. It means sort no
longer follows Swedish alphabetisation (å/ä/ö last); folded order keeps accented names with their base letters,
consistent with search. Locale-correct collation is a larger, separate undertaking.

The constraint was the blast radius. The unique `Artist.name`/`Genre.name` columns use `NOCASE` for identity — the
find-or-create that decides whether two tagged spellings are the same artist. Overriding it would fold accents there
too, merging `Beyoncé` and `Beyonce` into one artist and requiring a `REINDEX` of existing libraries. That is a separate
identity decision, so search and sort fold while identity is left untouched.

## Alternatives considered

- **Override the builtin `NOCASE` globally** — least code, fixes search and sort in a line, but folds accents into
  identity: `Åsa`/`Asa` and `Beyoncé`/`Beyonce` collapse to one artist on `add`, and an existing index built under ASCII
  `NOCASE` needs a `REINDEX`. Merging artist identity across accents is a separate decision; the surgical split buys the
  requested behaviour without it.
- **A normalised, folded shadow column** indexed for search — carries a schema change, Alembic migration, and the
  discipline of syncing the column on every write, to buy index performance a personal library will never need.
- **The ICU extension**, a Unicode-aware `LIKE` — not bundled with the stdlib `sqlite3`, so it adds a build/deploy
  dependency to replace a dozen lines of Python.
- **Case only, no accent folding** — correct, but `asa` would still miss `Åsa`; rejected in favour of the more forgiving
  search.
