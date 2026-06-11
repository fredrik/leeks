# 0005 — `leek import` ingests many albums, interactively

## Decision

`leek import <path>` takes a directory tree holding a full set of albums and walks it, calling the same single-album
pipeline as `leek add` (ADR 0004) for each album it finds. Where `add` is the non-interactive primitive, `import` is the
interactive session: it is the command where a human steers a bulk ingest — confirming album boundaries when detection
is unsure, splitting a directory that looks like several albums, skipping what should not enter at all. It also owns the
bulk UX: progress, resume, and a skip-on-error journal.

The interaction has a strict boundary: `import` prompts about *what the albums are*, never about *whether the metadata
is right*. Matching quality, conflicting sources, and low confidence are review's territory — separate, retryable, never
blocking (core position: imports never block on matching). An album with terrible tags sails through `import` exactly as
it does through `add`; the human is consulted on boundaries, not on quality.

## Context

This is the complement of ADR 0004. Splitting `add` from `import` moved the clustering problem out of the primitive;
this record decides where the human lands. Album-boundary detection over a real, messy tree will be wrong sometimes —
box sets, discographies dumped flat, stray singles — and the moment of import is when a human is present, looking at the
tree, cheapest to ask. Sending boundary mistakes silently into the library would convert each one into a later
remove-and-readd chore.

beets' importer interleaved its prompts with matching, so saying "yes, this is one album" and "yes, accept this match"
happened in the same breath, and the session blocked on both. Keeping `import`'s questions to boundaries — and `add` at
zero questions — keeps the two decisions apart.

## Alternatives considered

- **Fully automatic `import`** — journal everything, ask nothing. Maximally scriptable, but boundary mistakes land in
  the library and must be repaired later without the human who was just there, looking at the directory tree.
- **Interactive matching too** — beets' shape; rejected by the core position. Metadata decisions belong to review, which
  is retryable and never gates ingestion.
