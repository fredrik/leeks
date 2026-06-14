# 0011 — `leek list` is albums in shelf order, filtered by bare terms

Status: Superseded by [0013](0013-list-selects-its-entity-by-option.md) (2026-06-13)

## Decision

`leek list [TERM]...` prints the library's albums, one line per album — artist, year, title, track count — read from the
merged view. It lists albums and nothing else: the album is the primary entity (core position), so the default view of
the library is the view of its albums. Depth on a single entity is `leek info`'s concern; a flat per-track listing waits
until a need exists.

The order is **shelf order**: artist (case-folded, with the Unknown Artist bucket sorting under U), then year with
missing years last, then title. This is exactly the order of the library tree (ADR 0010), so the listing and the tree
never disagree about where an album sits.

Queries are **bare terms**. Every term must match (AND); a term matches an album when it appears, case-insensitively,
anywhere in the album's artist, title, or year. Terms match data, never display fallbacks: an album with no artist claim
is not found by searching `unknown`. LIKE metacharacters are escaped — a term is text, not a pattern.

Albums go to stdout, one per line; the empty-library and no-match notes go to stderr and point at `leek add`. Exit code
0 either way — an empty shelf is an answer, not an error. One per line is literal: a terminal gets the aligned, themed
table; a pipe gets one tab-separated record per album, never wrapped, so `leek list | grep` stays line-oriented.

## Context

This is the first read verb, and the first time the merged view earns its name: `list` reads the albums table's merged
columns directly and never touches the source layer — that separation is the point of having a merged view at all
(`info`, which deliberately exposes the source layer, is the designed exception).

Bare terms are a deliberate floor. beets shows a query language is a designed artifact, not an accreted one: its grammar
was never written down, so the semantics live in the parser (a colon inside a search term silently becomes a field
query; case rules differ between query types) and every comparison negotiates the stringly-typed substrate at query
time. Bare substring terms cover the dogfooding need at near-zero design cost and constrain nothing — any future
grammar, written deliberately on typed columns, keeps `leek list radiohead` meaning what it obviously means.

## Alternatives considered

- **Tracks by default, albums behind a flag** (beets' `ls`/`ls -a`) — rejected: it presents the library as a bag of
  files with album labels, the inversion leeks exists to correct, and puts a flag where a verb should be (ADR 0003).
- **A field-qualified query language now** — rejected as speculative design before contact with real queries; nothing
  forces the design today.
- **Matching terms against the Unknown Artist fallback** — rejected: it makes a display string queryable and teaches a
  "field value" no source claimed. The honest spelling of "albums with no artist" is a real query feature, designed
  later.
- **grep-style exit 1 on no match** — rejected: it makes an empty shelf an error and complicates every `leek list` in a
  script. A future flag or verb can add it; exit codes are cheap to add and expensive to change.

## Consequences

How queries grow is undecided. Field-qualified terms (`year:2019`), comparisons, negation, and per-track search are all
plausible; none is designed until a real query demands one.
