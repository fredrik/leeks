# 0009 — Artist links now; the credits table arrives with MusicBrainz

Status: Decided (2026-06-12)

## Decision

Slice 1 links artists with two nullable foreign keys — `albums.artist_id` and `tracks.artist_id` (set only when a
track's artist overrides the album's) — instead of an `artist_credits` junction. The credits table (artist-to-entity
links with role, position, and join phrase) arrives with the MusicBrainz slice, created by the same backfill migration
that brings release groups and recordings, converting the slice-1 links into position-0 credits.

This is ADR 0006's rule applied to its next case. In slice 1 the junction's distinguishing columns carried no
information: `role` was fully determined by which foreign key was set, `position` was always 0. Degenerate rows are
ceremony, and the data that justifies the junction — multiple credited artists, roles, ordering, join phrases — is
MusicBrainz data.

The `artists` table itself stays: "artists are first-class rows" is a core position, and its data is real today (one row
per raw credit string, deduplicated across albums).

## Context

The slice was built *with* the credits table, faithfully to the detail plan — and the plan had inherited it from the
teebs data model, a speculative design written before any contact with implementation. Fredrik caught the overreach in
review; notably, the parity-twin experiment could not have caught it, since both implementations read the same plan and
inherited the same anchoring. Twins detect ambiguity in a plan, not error in it. The process lesson is recorded in
[project-principles](../design/project-principles.md): learn from teebs' decisions, never copy its details.

## Alternatives considered

- **Keep the credits table** — the finished model's shape, but two of its four meaningful columns held constants;
  exactly the day-one ceremony ADR 0006 rejected for release groups.
- **Artist name columns on albums/tracks** — no junction *and* no artist rows; violates the first-class-artists core
  position and loses the cross-album deduplication that already works today.
