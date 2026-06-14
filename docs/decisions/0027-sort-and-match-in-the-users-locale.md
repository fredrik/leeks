# 0027 — Sort and match in the user's locale

Status: Decided (2026-06-14)

## Decision

leeks will support every locale. Locale-sensitive behaviour — collation (sort order) first, and the locale-dependent
parts of matching and case/accent folding in time — follows the library's locale and is *correct* for that locale, not
merely tolerant of non-ASCII. leeks is meant to ship globally; a sort order that is right only for Swedish (or English)
is a latent bug for every other user, not a missing nice-to-have.

This is a standing commitment, not an implemented feature. The current Swedish-only collation
([ADR 0026](0026-sort-in-swedish-order.md)) is the interim; this record fixes the direction it is interim *toward*.

## Context

Collation is locale-relative: there is no single ordering correct for all languages at once. Swedish wants `å ä ö` as
distinct letters after `z`; German wants them folded in with `a o u`; Spanish wants `ñ` after `n`; Unicode's
language-neutral root groups every accented letter with its base. These are mutually exclusive, so a library cannot sort
"internationally" — it sorts in *one* locale, the user's. The same is true of the locale-dependent edges of matching
(which strings count as equal) and folding.

Two things stand between here and there:

1. **A home for the library's locale.** It must be a property of the library, stored — not read from the ambient
   `$LANG`, or the same library would sort differently from different shells. That is the configuration seam leeks has
   deliberately punted, and the first library-level setting will set the precedent for how leeks does configuration at
   all — a decision worth making deliberately, not as a side effect of sort.
2. **A collation engine that knows every locale.** ICU (via PyICU) carries the per-locale tailorings; it is almost
   certainly also wanted by the matcher port for normalisation and folding, so the C dependency it brings is best
   adopted once, for both, rather than smuggled in for sort alone.

Because collation happens at query time and nothing locale-specific is persisted (ADR 0026), reaching the destination is
purely additive — swap the hardcoded `sort_key` for a configured ICU collator, no migration, no stored data to rewrite.
That is what makes sequencing this *after* the configuration seam cheap rather than a debt that compounds.

## Alternatives considered

- **Hardcode a single locale forever** — rejected outright by the global-shipping goal: it makes leeks correct for one
  audience and quietly wrong for the rest.
- **Hand-roll per-language tailorings** — rejected as the beets accretion trap. German `ß`, Spanish `ñ`, the Nordic
  `æ ø å`, Hungarian digraphs (`cs`, `sz`, `zs`), contextual rules — encoding these by hand is reimplementing ICU, badly
  and forever. The engine for this exists; we should use it.
- **Do it now, before the configuration seam exists** — the live question when this was written. Feasible, and the
  query-time design keeps the rework cost near zero either way; the cost of *now* is forcing the first library-level
  setting (where locale is stored, how it is set) as a rider on a sort change, rather than designing leeks'
  configuration story on its own terms. Recorded here so the choice is explicit rather than defaulted.
