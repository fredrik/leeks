# 0004 — Make `leek add` ingest exactly one album

Status: Decided (2026-06-11)

## Decision

`leek add <path>` adds a single album to the library, non-interactively. It accepts a directory only if it looks like
exactly one album; otherwise it errors and points at the batch command — "this looks like 12 albums, use `leek import`".
`leek import` arrives later as a separate command that iterates a tree of directories and calls the same single-album
pipeline per directory, owning the bulk UX (progress, resume, a skip-on-error journal) without polluting `add` (ADR
0005).

`add` records what it knows and never forces a human decision at ingest time. Low confidence never blocks — the "imports
never block on matching" core position held at the UX level, not just the schema level.

## Context

Single-album scope changes what the album-birth heuristic is. A command that ingests arbitrary trees needs a clusterer
that decides what the albums are; a single-album command needs only a validator that checks a human's claim — "you said
this is one album; it doesn't look like one; here's why". Validators are easier to make trustworthy than clusterers, and
erring on the side of refusal is safe when the fix is reaching for the other command. beets put clustering, matching,
prompting, and moving in one interactive importer that never came back out of its complexity; splitting the commands
splits the concerns.

## Alternatives considered

- **One `add` that handles both single albums and trees** — beets' shape. Convenient at first use, but it forces the
  clustering, prompting, and bulk-resume machinery into the inner ingest path, where it never stops costing.
- **Interactive `add`** — prompting at ingest conflates "should this enter the library?" with "is the metadata right?".
  Matching and review are separate, retryable steps by core position; `add`'s job is only to record what it knows.

## Consequences

What running `leek add x` twice does, and where disambiguation lives, are deliberately undecided. Source-path
uniqueness, content hashes, and a `--force` (sugar for `remove` + `add`) are the candidate ingredients. The slice that
implements `add` carries an interim punt; the real design comes later.
