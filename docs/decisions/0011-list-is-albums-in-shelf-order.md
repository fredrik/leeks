# 0011 — `leek list` is albums in shelf order, filtered by bare terms

Status: Superseded by [0013](0013-list-selects-its-entity-by-option.md) (2026-06-13)

## Decision

`leek list [TERM]...` prints the library's albums, one line per album — artist, year, title, track count — read from the
merged view. It lists albums and nothing else: the album is the primary entity (core position), so the default view of
the library is the view of its albums. Depth on a single entity is `leek info`'s concern; a flat per-track listing waits
until a need exists.

The order is **shelf order**: artist (case-folded, with the Unknown Artist bucket sorting under U), then year with
missing years last, then title. This is exactly the order of the library tree (ADR 0010) — `leek list` reads like
walking the shelf, and the listing and the tree never disagree about where an album sits.

Queries are **bare terms**. Every term must match (AND); a term matches an album when it appears, case-insensitively,
anywhere in the album's artist, title, or year. Terms match *data*, never display fallbacks: an album with no artist
claim is not found by searching `unknown`. LIKE metacharacters are escaped — a term is text, not a pattern.

Scriptability is the primitive's job: albums go to stdout, one per line; the empty-library and no-match notes go to
stderr and point at the right verb (`leek add`). Exit code 0 either way — an empty shelf is an answer, not an error. One
per line is literal: a terminal gets the aligned, themed table; a pipe gets one tab-separated record per album, never
wrapped — a record folded across physical lines would break `leek list | grep`.

Deliberately undecided: how queries grow. Field-qualified terms (`year:2019`), comparisons, negation, and per-track
search are all plausible; none is designed. The punt: bare substring terms only, until a real query demands more.

## Context

This is the first read verb, and the first time the merged view earns its name: `list` reads the albums table's merged
columns directly and never touches the source layer — that separation is the point of having a merged view at all
(`info`, which deliberately exposes the source layer, is the designed exception).

beets' query language informs this punt from both sides. Its surface is genuinely good and well loved — bare terms,
`field:value`, ranges: terse, guessable ideas that earned their keep, and a future leeks grammar should preserve what
makes them enjoyable. The cautionary half is *how* that language came to be: it was never designed, it accumulated —
regex, ranges, OR, negation each grafted on over the years — so its semantics live in the parser (a colon inside a
search term silently becomes a field query; case rules differ between query types) and every comparison negotiates the
stringly-typed substrate at query time. The lesson is not "no query language", nor "beets' was wrong"; it is that a
query language is a designed artifact — write the grammar down deliberately, on typed columns, once real queries show
what to design. Bare terms cover the dogfooding need (find an album, eyeball the shelf) at near-zero design cost and
constrain nothing: any future grammar can keep `leek list radiohead` meaning what it obviously means.

## Alternatives considered

- **Tracks by default, albums behind a flag** — beets' `ls`/`ls -a` shape. Bottom-up: it presents the library as a bag
  of files with album labels, which is the inversion leeks exists to correct. Also a flag where a verb should be (ADR
  0003).
- **A field-qualified query language now** — speculative design before contact with real queries; beets' lesson is that
  this must be designed deliberately, and nothing forces the design today.
- **Matching terms against the Unknown Artist fallback** — friendly at first glance, but it makes a display string
  queryable and teaches users a "field value" that no source ever claimed. The honest spelling of "albums with no
  artist" is a real query feature, designed later.
- **grep-style exit 1 on no match** — scriptable, but it makes an empty shelf an error and complicates every innocent
  `leek list` in a script. If scripts need it, a future flag or verb can provide it; exit codes are cheap to add and
  expensive to change.
