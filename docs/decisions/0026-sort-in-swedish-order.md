# 0026 — Sort in Swedish order

Status: Decided (2026-06-14)

## Decision

Listings sort in Swedish order: case-insensitive, with `å ä ö` treated as distinct letters that come *after* `z`, in
that sequence. A pure-Python `sort_key` (`db.py`) backs a `SORT` collation registered on every connection, and every
`ORDER BY` in `library.py` uses it. Foreign diacritics (`é`, `ü`) are stripped so they sort with their base letter; the
three Swedish letters are parked just past `z` so a plain comparison shelves them last.

This refines the ordering half of [ADR 0021](0021-fold-case-and-accents-for-search-and-sort.md). Search is unchanged —
it still folds case *and* accents, so `asa` finds `Åsa`. Only sorting changes: 0021's folded collation put `Åsa` among
the A's, and this replaces it.

No new dependency: `sort_key` is `casefold` + a three-character mapping + diacritic stripping over `unicodedata`.

## Context

0021 used one `fold` for both search and sort. That was right for search — folding accents is a kindness to keyboards
without `å/ä/ö` — but wrong for sort. Folding made `Å` sort as `A`, so `leek list --artists` opened with `Åsa Vinterhök`
at the *top*. To a Swedish reader that is plainly broken: `å ä ö` are the last three letters of the alphabet, not
variants of `a`/`o`, and belong at the bottom of the shelf.

The fix is to recognise that search and sort want opposite things from accents — search erases them, sort honours them —
and give sorting its own key. Parking `å→{`, `ä→|`, `ö→}` (the codepoints just above `z`) makes an ordinary string
compare place them last and in order, while `NFC`-normalising first folds in decomposed (NFD) input and stripping the
remaining combining marks keeps foreign accents next to their base letters instead of scattering.

A locale-correct collator (ICU, via PyICU) was the obvious "proper" answer and was the original plan. But the outcome
asked for — `å < ä < ö`, after `z` — is fully met by the tailored key above, and ICU's genuine extras (`é`=`e` folding,
the older `v`=`w` equivalence) are marginal here: modern Swedish sorts `v` and `w` apart anyway, and the diacritic strip
already coalesces `é` with `e`. ICU would have made every developer and CI build a C extension against `libicu` to sort
a personal library. That trade — a heavy, build-fragile dependency for a sort refinement — lost against the project's
"don't add when you can delete."

## Alternatives considered

- **A locale-aware ICU collator (PyICU)** — the textbook-correct route, and what this record was first going to do. It
  needs `libicu` and `pkg-config` at build time (no wheel for the project's interpreter), pushing a system dependency
  onto every contributor and CI. The hand-rolled key delivers the requested order without it; ICU can come back if the
  library ever needs full locale collation for more than Swedish.
- **Codepoint order (the "simple" option first offered)** — casefold only, no remap, letting `å/ä/ö` fall past `z` by
  codepoint. It puts them last but in the wrong sequence: codepoints give `ä < å < ö`, not the Swedish `å < ä < ö`.
  Rejected for getting the order of the three wrong.
- **Keep 0021's folded sort** (`Åsa` among the A's) — rejected on contact: it reads as broken to a Swedish user, which
  is what prompted this record.

## Other languages

This key is a *Swedish tailoring*, and only that. Run it against another language and it is wrong in that language's
terms: German wants `ä ö ü` sorted with `a o u` (or as `ae oe ue`), not parked after `z`; Spanish wants `ñ` as its own
letter after `n`, where this strips it to `n`; Norwegian and Danish end with `æ ø å`, a different set in a different
order. There is no single ordering correct for every language at once — Unicode's language-neutral root groups accented
letters *with* their base, the opposite of what Swedish demands — so collation is inherently locale-relative: a library
sorts in *one* locale, the user's, not "internationally".

leeks commits to supporting every locale ([ADR 0027](0027-sort-and-match-in-the-users-locale.md)); this record is the
interim. The Swedish tailoring is hardcoded because the library has no locale setting yet, and the place a library's
locale belongs is the configuration seam leeks has deliberately punted. The seam here is deliberately narrow — one
`sort_key` function, one `create_collation` call, and collation happens at query time so nothing locale-specific is
persisted — so swapping this for a configured, ICU-backed collator later is purely additive: no migration, no stored
data to rewrite. That is the property that makes "Swedish now, every locale later" cheap rather than reckless.
