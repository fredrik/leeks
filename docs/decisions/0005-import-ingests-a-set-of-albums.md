# 0005 — Make `leek import` ingest a set of albums

Status: Decided (2026-06-11)

## Decision

`leek import <path>` takes a directory tree holding a set of albums, finds the albums in it, and calls the same
single-album pipeline as `leek add` (ADR 0004) for each one. The hard problem `import` owns is album-boundary detection
— deciding what is an album in a real, messy tree. It also owns the bulk UX: progress, resume, a skip-on-error journal.

Whether `import` is interactive is deliberately undecided: boundary detection will be wrong sometimes — box sets,
discographies dumped flat, stray singles — and more than one way to put a human in the loop is defensible.

If `import` ever asks a human anything, it asks what the albums are, never whether the metadata is right. Matching
quality, conflicting sources, and low confidence are review's territory — separate, retryable, never blocking (core
position: imports never block on matching). An album with terrible tags goes through `import` exactly as it does through
`add`.

## Context

This is the complement of ADR 0004. `add` validates a human's claim that one directory is one album; `import` has no
such claim to lean on and must decide boundaries itself. That is why the two are separate programs rather than one
command with a flag.

beets' importer interleaved boundary decisions with match decisions, so "yes, this is one album" and "yes, accept this
match" blocked on each other in the same session; leeks keeps the two questions apart, and the second never gates
ingestion.

## Alternatives considered

- **One `add` that also handles trees** — rejected in ADR 0004; it forces clustering and bulk-resume machinery into the
  inner ingest path.
- **Committing now to an interactive `import`** — rejected: the interaction model deserves contact with a real messy
  tree before it is fixed.

## Consequences

The interaction model is decided when `import` is built. Candidate shapes: prompting at import time, journalling
uncertain boundaries for later review, a dry-run preview of the proposed split. Whichever wins, it asks only about album
boundaries, never about metadata.
