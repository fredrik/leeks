# 0026 — Sort in Swedish order

Status: Decided (2026-06-14)

## Decision

Listings sort in Swedish order: case-insensitive, with `å ä ö` distinct letters that sort after `z` in that sequence. A
pure-Python `sort_key` (`db.py`) backs a `SORT` collation registered on every connection; every `ORDER BY` in
`library.py` uses it. The key casefolds, NFC-normalises, maps `å→{`, `ä→|`, `ö→}` (the codepoints just past `z`) so a
plain compare shelves them last and in order, and strips remaining combining marks so foreign diacritics (`é`, `ü`) sort
with their base letter. No new dependency: `casefold` plus a three-character mapping plus diacritic stripping over
`unicodedata`.

This refines the ordering half of [ADR 0021](0021-fold-case-and-accents-for-search-and-sort.md). Search is unchanged: it
still folds case and accents, so `asa` finds `Åsa`. Only sorting changes.

## Context

0021 used one `fold` for both search and sort. Folding accents is right for search and wrong for sort: it made `Å` sort
as `A`, so `leek list --artists` opened with `Åsa Vinterhök` at the top, which reads as broken to a Swedish user —
`å ä ö` are the last three letters of the alphabet, not variants of `a`/`o`. Search and sort want opposite things from
accents, so sorting gets its own key.

## Alternatives considered

- **A locale-aware ICU collator (PyICU)** — rejected: it needs `libicu` and `pkg-config` at build time (no wheel for the
  project's interpreter), a system dependency on every contributor and CI for a sort refinement. Its genuine extras over
  the hand-rolled key are marginal here — the diacritic strip already coalesces `é` with `e`, and modern Swedish sorts
  `v` and `w` apart. ICU can return if the library ever needs full locale collation.
- **Codepoint order** — casefold only, no remap. Parks `å ä ö` past `z` but in the wrong sequence: codepoints give
  `ä < å < ö`, not Swedish `å < ä < ö`.
- **Keep 0021's folded sort** (`Åsa` among the A's) — rejected: reads as broken to a Swedish user, which prompted this
  record.

## Consequences

The key is a Swedish tailoring and is wrong in other languages' terms: German sorts `ä ö ü` with `a o u`, Spanish wants
`ñ` after `n` (this strips it to `n`), Norwegian and Danish end `æ ø å`. No single ordering is correct for every
language, so collation is locale-relative: a library sorts in one locale, the user's. leeks commits to supporting every
locale ([ADR 0027](0027-sort-and-match-in-the-users-locale.md)); this record is the interim, hardcoded because the
library has no locale setting yet. The seam is narrow — one `sort_key`, one `create_collation` call, collation at query
time so nothing locale-specific is persisted — so a configured ICU-backed collator later is purely additive: no
migration, no stored data to rewrite.
