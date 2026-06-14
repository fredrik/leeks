# 0013 — Select `leek list`'s entity by option; default to albums

Status: Decided (2026-06-13)

Amended by [0019](0019-the-default-output-is-for-humans-not-parsers.md) (2026-06-13): a pipe no longer gets a
tab-separated record — it gets the human format rendered plain; the rest of this record stands.

## Decision

`leek list [TERM]...` lists the library. Its **default subject is albums** — one line per album in shelf order, the view
ADR 0011 shipped (artist, year, title, track count; read from the merged view; bare terms ANDed against the album's
artist/title/year; data never display fallbacks; aligned table to a terminal, human format rendered plain to a pipe;
exit 0 on an empty shelf).

An **option selects a different subject**: `leek list --tracks`, `--artists`, `--genres`, mutually exclusive; with none,
the subject is albums. Each names a first-class entity (core position: artists and genres are real rows, not strings),
so each is a genuine listing, not a reshaping of the album view. `list` keeps its one concern — the library made visible
— and the option chooses which projection to print; this is not a second concern in the sense verbs.md forbids (a verb
doing two unrelated jobs, like `add` quietly importing).

The **album default is load-bearing**: the album is the primary entity, top-down (core position), so you must ask for
tracks. leeks does not default to a bag of files the way beets' bare `ls` does. This is the surviving half of ADR 0011's
`ls -a` objection — the bottom-up default, not the option. The other half, "a flag where a verb belongs", no longer
holds: verbs.md no longer forbids options that change the subject. ADR 0003 still bans flags only at the top level.

Two things about the non-album subjects are settled in **direction, not grammar** — per ADR 0012, the per-entity detail
is designed on contact, when the slice that builds these options arrives:

- **Each subject has its own default order**, overridable later by sort terms (ADR 0012's deferred grammar). Albums:
  shelf order (ADR 0011). Tracks: the tree walk — album shelf order, then track number, then filename (the same
  tie-break assembly uses, glossary), so a track listing is a depth-first walk of the tree and ADR 0010/0011's "the
  listing and the tree never disagree" extends to tracks. Artists: case-folded name. Genres: alphabetical (open).
- **What a term matches is per subject, a deliberate choice.** beets makes cross-entity matching free — `ls radiohead`
  hits an artist on a track row — by denormalising the album's fields onto every track. leeks normalises, so whether a
  `--tracks` term reaches up to the track's album artist is a choice the query grammar makes on purpose. Deferred to the
  grammar (ADR 0012); named here so its design starts from the right question.

Nothing is built today: `list` keeps its shipped albums-only behaviour, and the options and their orderings arrive when
a need does. This record settles that the entities are listable from `list` via options, with albums the default.

## Context

ADR 0011 shipped `list` as albums and nothing else, rejecting tracks-behind-a-flag because it would present the library
bottom-up and put a flag where a verb belongs. Fredrik now wants tracks, artists, and genres listable too, and verbs.md
no longer forbids an option from changing a verb's subject — leaving the bottom-up objection standing (honoured by
keeping albums the default) but dissolving the flag objection.

ADR 0011's decision text now contradicts the intended surface: it lists albums and nothing else, and names
tracks-behind-a-flag among its rejected alternatives. A decided record is never amended here — only its Status line
moves — so the fix is supersession. This record absorbs 0011's still-true content (the album view, reproduced above) and
extends it, so there is one record for what `leek list` is. 0011 remains as the history of how the albums-only floor was
set.

## Alternatives considered

- **Amend ADR 0011 in place** — rejected; the project never amends decision records, only the Status line moves.
  Supersession also keeps the honest trail of a door closed in 0011 and reopened here.
- **Separate verbs — `leek tracks`, `leek artists`, `leek genres`** — rejected; nouns wearing verb costumes, scattering
  "the library, made visible" across four verbs that share all their machinery. One verb with a subject option keeps the
  concern whole.
- **Design the per-entity grammar now** (orderings, field reach, mutual-exclusion errors) — rejected as speculation
  before contact, which ADR 0011 and 0012 both declined.
- **Keep the albums-only `list` and never broaden it** — rejected; it forces the bag-of-tracks question onto `info`
  (depth, not breadth) or onto new verbs, and the breadth view's natural home is the option.
