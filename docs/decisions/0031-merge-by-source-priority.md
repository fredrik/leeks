# 0031 — Resolve merged columns by source priority

Status: Decided (2026-06-14)

## Decision

Each `sources` row carries an integer `priority`; `merge()` sets every merged column to the value of the
highest-priority source that claims it. file_tags has priority 100 and the path source 50, so file tags win a field when
they claim it and the path source fills the gaps they leave.

Claims carry a per-claim `confidence` (a nullable float on `source_values`): an analyzer records how sure it is, a
reader like file_tags records NULL. Confidence is stored but does not yet enter resolution — priority alone decides the
winner.

The `path` source is registered at migration alongside file_tags. This slice it claims one field: a parenthesised
four-digit year read from the directory name (ADR 0008).

## Context

`merge()` was an identity copy because file_tags was the only source — every claim simply passed through to its column.
The path source is the second source (ADR 0008), so a field can now be claimed twice and merge must choose. A fixed
per-source priority is the cheapest rule that chooses correctly: the two sources differ in kind, not degree — tags read
what the file states, the path guesses from a name — so no scoring is needed. Priority lives on the row, not in code, so
a third source slots in by picking a number.

## Alternatives considered

- **Confidence-weighted resolution** — rejected for now: it needs a confidence scale calibrated across sources, which
  two sources differing by kind don't yet justify. Confidence is recorded so the option stays open.
- **Most-recent claim wins** — rejected: insertion order carries no meaning, and the result would depend on add order.
- **Hardcode file_tags > path in `merge()`** — rejected: priority is data the merge reads, so adding a source is a row,
  not an edit to the resolver.

## Consequences

- Confidence is stored but unused in resolution — a live deferral until a source makes degree, not kind, the deciding
  factor (an analyzer disagreeing with another analyzer).
- Priorities are fixed constants; making them configurable waits for a reason to.
- Relational fields (artist, genre) are not merged columns, so this rule does not touch them; reconciling them across
  sources is its own slice.
