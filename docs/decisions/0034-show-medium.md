# 0034 — Show medium, and give it a merged column

Status: Decided (2026-06-14)

## Decision

`leek show` displays an album's medium (vinyl/CD/cassette) in the heading parenthetical, beside the year:
`<artist> — <title> (<year> · <medium>)`. An absent fact drops out, so an album with neither year nor medium gets no
parens.

Because a reader now consumes it, medium graduates from claim-only to a merged column (ADR 0033 anticipated this): it
carries a `str` cast in the registry, gets a nullable `albums.medium` column, and `merge()` fills it from the
highest-priority medium claim — the path's, today. It stays untagged: file_tags has no attribute for it, so only the
path claims it.

region and catalogue have no reader, so they remain claim-only — recorded in the source layer, visible to
`leek show --sources`, with no column. They graduate the same way if a reader arrives.

## Context

medium, region, and catalogue landed claim-only (ADR 0033) because nothing read them — only `show --sources` dumped the
raw claim layer. The deferral that recorded was "until a consumer earns a column." medium is the first to find one: an
album's physical form belongs in the depth view a person reads, so `leek show` displays it.

A merged column is the natural home for a scalar the merged view shows: `merge()` already resolves the registry's
cast-carrying fields, so a cast and a column are all medium needs to flow like title and year.

## Alternatives considered

- **Read the medium from the claim layer at show time, no column** — rejected: it reimplements priority resolution
  outside `merge()`, the one place that owns it, for a value that is a plain merged scalar.
- **Promote region and catalogue too** — declined: neither has a reader, and a column without one is the machinery ADR
  0033 declined. They wait for their own consumer.
- **A second line under the heading, as genres have** — rejected: medium is a compact identifying fact like the year, so
  it sits with the year in the parenthetical; genres are a set and earn their own line.

## Consequences

- The heading parenthetical now gathers facts (year, then medium); a future compact fact joins it there rather than
  growing the heading sideways.
- medium is the registry's first field that is both untagged and a merged column — a column file_tags never fills,
  proving the `tagged` flag and the cast are independent (ADR 0033).
