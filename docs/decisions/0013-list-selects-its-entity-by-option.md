# 0013 — Select `leek list`'s entity by option; default to albums

Status: Decided (2026-06-13)

## Decision

`leek list [TERM]...` lists the library. Its **default subject is albums** — one line per album in shelf order, exactly
the view ADR 0011 shipped (artist, year, title, track count; read from the merged view; bare terms ANDed against the
album's artist/title/year; data never display fallbacks; aligned table to a terminal, tab-separated record to a pipe;
exit 0 on an empty shelf). That behaviour is unchanged.

An **option selects a different subject**: `leek list --tracks`, `--artists`, `--genres`. The options are mutually
exclusive; with none, the subject is albums. Each names a first-class entity (core position: artists and genres are real
rows, not strings), so each is a genuine listing, not a reshaping of the album view.

This does not give `list` a second concern. Its one concern is *the library, made visible*; the option chooses which
projection of the library to print. "One verb, one concern" (verbs.md) is about a verb doing two unrelated jobs — `add`
quietly importing, the way beets' importer grew — not about a listing that can name what it lists. Listing tracks and
listing albums are the same job pointed at different rows.

The **album default is load-bearing**. The album is the primary entity, top-down (core position); leeks does not present
the library as a bag of files the way beets' bare `ls` does, defaulting to tracks. You must *ask* for tracks. This is
the half of ADR 0011's `ls -a` objection that survives: the sin was the bottom-up default, not the option. The other
half — "a flag where a verb belongs" — no longer holds, because verbs.md no longer forbids options that change the
subject (it once did; that line was removed deliberately). ADR 0003 still bans flags only at the top level.

Two things about the non-album subjects are settled in **direction, not grammar** — matching ADR 0012, the per-entity
detail is designed on contact, when the slice that builds these options arrives:

- **Each subject has its own default order**, overridable later by sort terms (ADR 0012's deferred grammar). Albums:
  shelf order (ADR 0011). Tracks: the *tree walk* — album shelf order, then track number, then filename (the same
  tie-break assembly uses, glossary). A track listing thus reads as a depth-first walk of the library tree, and ADR
  0010/0011's "the listing and the tree never disagree" extends to tracks for free. Artists: case-folded name. Genres:
  alphabetical (open; settled when built).
- **What a term matches is per subject, and a deliberate choice.** beets made cross-entity matching free —
  `ls radiohead` hits an artist on a track row — because it denormalises the album's fields onto every track. leeks
  normalises (the founding annoyance), so whether a `--tracks` term reaches *up* to the track's album artist is a choice
  the query grammar must make on purpose, not a side effect of storage. Deferred to the grammar (ADR 0012); named here
  so the eventual design starts from the right question.

Nothing is built today. `leek list` keeps its shipped albums-only behaviour; the options and their orderings arrive when
a need does. This record settles that the entities *are* listable from `list` via options, and that albums stay the
default.

## Context

ADR 0011 shipped `list` as "albums and nothing else" and rejected listing tracks behind a flag for two reasons: it would
present the library bottom-up, and it would be a flag where a verb belongs. Both were sound at the time. Since then
Fredrik confirmed he wants tracks, artists, and genres listable too, and removed the verbs.md principle that forbade an
option from changing a verb's subject — leaving the bottom-up objection standing (and honoured by keeping albums the
default) but dissolving the flag objection.

ADR 0011's decision text now contradicts the intended surface: it says `list` lists albums and nothing else, and names
tracks-behind-a-flag among its rejected alternatives. A decided record is never amended in this project — only its
Status line moves — so the fix is supersession, not rewriting 0011. This record absorbs 0011's still-true content (the
album view is reproduced above, unchanged) and extends it, so there is one record to read for what `leek list` is. 0011
remains as the history of how the albums-only floor was set, and why.

## Alternatives considered

- **Amend ADR 0011 in place** — the project never amends decision records; the Status line is the only mutable line.
  Supersession also keeps the honest trail: a door closed in 0011, reopened here.
- **Separate verbs — `leek tracks`, `leek artists`, `leek genres`** — nouns wearing verb costumes, and it scatters "the
  library, made visible" across four verbs that share all their machinery. One verb with a subject option keeps the
  concern whole.
- **Design the per-entity grammar now** (orderings, field reach, mutual-exclusion errors) — speculation before contact,
  the thing ADR 0011 and 0012 both declined for good reason. Direction now, grammar on contact.
- **Keep the albums-only `list` and never broaden it** — defensible minimalism, but it forces the bag-of-tracks question
  onto `info` (depth, not breadth) or onto new verbs; the maintainer wants the breadth view, and the option is its
  natural home.
