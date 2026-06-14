# 0032 — Merge the artist foreign key

Status: Decided (2026-06-14)

## Decision

The artist foreign key, on both albums and tracks, is set by `merge()` from the artist claims — by source priority, the
same rule the scalar columns follow (ADR 0031). This is relational merge: the highest-priority artist claim's name
resolves to an `Artist` row (get-or-create, case-folded identity) rather than to a stored string. Artist no longer comes
from file_tags at write time.

genre, the other relational field, stays linked at write time from file_tags. The path source claims no genre, so genre
has one source; its cross-source merge waits for a source that claims it.

## Context

The path source gives artist a second claimant, but `merge()` resolved only scalar columns and the artist foreign key
was set at write time from file_tags, so a path-named, tag-less album shelved under Unknown Artist. Resolving a claim to
a row — the relational merge the glossary names — is the forcing function, and the artist key is its first instance. For
a single-valued foreign key the rule is pick-the-winner-then-resolve; the set-valued junction case is not built here.

## Alternatives considered

- **Keep artist set at write time from file_tags** — rejected: it ignores the path's claim and leaves the foreign key
  outside the merge model, so a tag-less album can never take an artist the path knows.
- **Merge genre relationally now too** — rejected: only file_tags claims genre, so it would be machinery without data
  (slice by data availability). genre stays write-time-linked until a second source claims it.
- **A general relational resolver in the registry** — deferred: one foreign-key field does not justify it; generalise
  when a second relational field gets a second source.

## Consequences

- genre is now the one relational field still written outside `merge()` — an asymmetry that resolves when a
  genre-claiming source arrives.
- The track artist override flows through `merge()` too; with only file_tags claiming it, that is identity.
