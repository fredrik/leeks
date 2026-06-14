# 0009 — Link artists now; defer the credits table to MusicBrainz

Status: Decided (2026-06-12)

## Decision

Slice 1 links artists with two nullable foreign keys — `albums.artist_id` and `tracks.artist_id` (set only when a
track's artist overrides the album's) — instead of an `artist_credits` junction. The credits table (artist-to-entity
links with role, position, and join phrase) arrives with the MusicBrainz slice, created by the same backfill migration
that brings release groups and recordings, converting the slice-1 links into position-0 credits.

This is ADR 0006's rule applied to its next case. In slice 1 the junction's distinguishing columns carry no information:
`role` is fully determined by which foreign key is set, `position` is always 0. The data that justifies the junction —
multiple credited artists, roles, ordering, join phrases — is MusicBrainz data.

The `artists` table itself stays: "artists are first-class rows" is a core position, and its data is real today (one row
per raw credit string, deduplicated across albums).

## Context

The detail plan carried the credits table over from the teebs data model, a speculative design written before any
contact with implementation. Both columns that justify a junction were constant in slice-1 data, so the junction was
day-one ceremony. The process lesson is recorded in [project-principles](../design/project-principles.md): learn from
teebs' decisions, never copy its details.

## Alternatives considered

- **Keep the credits table** — the finished model's shape, but two of its four meaningful columns held constants; the
  day-one ceremony ADR 0006 rejected for release groups.
- **Artist name columns on albums/tracks** — no junction *and* no artist rows; violates the first-class-artists core
  position and loses the cross-album deduplication that already works today.
