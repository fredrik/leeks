# 0027 — Sort and match in the user's locale

Status: Decided (2026-06-14)

## Decision

leeks supports every locale. Locale-sensitive behaviour — collation (sort order) first, and the locale-dependent parts
of matching and case/accent folding in time — follows the library's locale and is correct for that locale, not merely
tolerant of non-ASCII. A sort order right only for Swedish (or English) is a latent bug for every other user.

This is a standing commitment, not an implemented feature. The current Swedish-only collation
([ADR 0026](0026-sort-in-swedish-order.md)) is the interim toward it.

## Context

Collation is locale-relative: no single ordering is correct for all languages at once. Swedish wants `å ä ö` as distinct
letters after `z`; German folds them in with `a o u`; Spanish wants `ñ` after `n`; Unicode's language-neutral root
groups every accented letter with its base. These are mutually exclusive, so a library sorts in one locale, the user's.
The same holds for the locale-dependent edges of matching (which strings count as equal) and folding.

Two things stand between here and there:

1. **A home for the library's locale.** It is a property of the library, stored — not the ambient `$LANG`, or the same
   library would sort differently from different shells. This is the first library-level setting, so it sets the
   precedent for how leeks does configuration at all, and is decided on its own terms rather than as a side effect of
   sort.
2. **A collation engine that knows every locale.** ICU (via PyICU) carries the per-locale tailorings; the matcher port
   wants it too for normalisation and folding, so the C dependency it brings is adopted once, for both.

Collation happens at query time and nothing locale-specific is persisted (ADR 0026), so reaching the destination is
purely additive: swap the hardcoded `sort_key` for a configured ICU collator — no migration, no stored data to rewrite.

## Alternatives considered

- **Hardcode a single locale forever** — rejected: correct for one audience, quietly wrong for the rest.
- **Hand-roll per-language tailorings** — rejected as the beets accretion trap. German `ß`, Spanish `ñ`, the Nordic
  `æ ø å`, Hungarian digraphs (`cs`, `sz`, `zs`), contextual rules: encoding these by hand reimplements ICU, badly and
  forever.
- **Do it now, before the configuration seam exists** — rejected: the query-time design keeps the rework cost near zero
  either way, so doing it now buys nothing and forces the first library-level setting as a rider on a sort change.
