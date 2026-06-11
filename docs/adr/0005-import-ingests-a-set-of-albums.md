# 0005 — `leek import` ingests a set of albums

## Decision

`leek import <path>` takes a directory tree holding a set of albums, finds the albums in it, and calls the same
single-album pipeline as `leek add` (ADR 0004) for each one. The hard problem `import` owns is album-boundary detection
— deciding what is an album in a real, messy tree. It also owns the bulk UX: progress, resume, a skip-on-error journal.

Whether `import` is interactive is deliberately undecided. Boundary detection will be wrong sometimes — box sets,
discographies dumped flat, stray singles — and there is more than one defensible way to put a human in the loop:
prompting at import time, journalling uncertain boundaries for later review, a dry-run preview of the proposed split. We
choose when we build it.

One boundary *is* decided: if `import` ever asks a human anything, it asks about *what the albums are*, never about
*whether the metadata is right*. Matching quality, conflicting sources, and low confidence are review's territory —
separate, retryable, never blocking (core position: imports never block on matching). An album with terrible tags goes
through `import` exactly as it does through `add`.

## Context

This is the complement of ADR 0004. Splitting `add` from `import` moved the clustering problem out of the primitive;
this record names where it landed. `add` validates a human's claim that one directory is one album; `import` has no such
claim to lean on and must decide boundaries itself — that is the genuinely tricky part, and the reason the two commands
are different programs rather than one command with a flag.

beets' importer is the cautionary shape: it interleaved boundary decisions with match decisions, so "yes, this is one
album" and "yes, accept this match" happened in the same breath, and the session blocked on both. Whatever UX `import`
grows, those two questions stay apart — and the second one never gates ingestion.

## Alternatives considered

- **One `add` that also handles trees** — rejected in ADR 0004; it forces clustering and bulk-resume machinery into the
  inner ingest path.
- **Committing now to an interactive `import`** — the first draft of this record. Premature: the scope and the
  boundary-versus-metadata line are what must hold; the interaction model deserves contact with a real messy tree before
  it is fixed.
