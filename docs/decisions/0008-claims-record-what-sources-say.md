# 0008 — Claims record what sources say; the path is a source

Status: Decided (2026-06-12)

## Decision

Two rulings from the slice 1 parity review, one principle: **the claim layer records only what a source actually says.**

**Consensus is unanimity-or-nothing.** When an album's files disagree on an album-level tag (year, genre, tracktotal),
`file_tags` claims nothing for that field. A source that disagrees with itself has not said anything; resolving
disagreement is merge-and-review's business, not assembly's.

**Fallbacks are not claims.** When tags are silent, the NOT NULL merged columns (album title, track title) take the
directory name or file stem as working values — and `source_values` stays silent too. `file_tags` never claims what no
tag said. An untagged album still enters the library: the files that most need management are the ones with the worst
metadata.

**The path is a source.** Filesystem names carry real metadata —
`The Avalanches - Since I Left You (2001) [FLAC] {Scandinavia - XLCD 138}` asserts artist, title, year, format, region,
and catalogue number: release-level facts file tags often lack. That information enters the library as claims of a
`path` source. Note what the filesystem literally says is only the *name*; extracting title or year from it is parsing —
heuristic, capable of being wrong — so the path parser is an analyzer under ADR 0007 and its claims carry confidence.

Sequencing: the path source is a genuine second source, and identity merge cannot host two. It arrives as its own slice
once merge machinery exists — plausibly *before* MusicBrainz, as a cheap local source to exercise two-source merging
gently. Until then, the fallbacks above stand as its explicit placeholder.

## Context

The slice 1 parity experiment (journal, 2026-06-12) forked exactly here: the zero-context twin recorded file stems as
`file_tags` title claims and refused albums with no album tag at all. Both moves have costs this record exists to avoid.
A fabricated claim manufactures conflict later — when MusicBrainz disagrees with a "file_tags claim" no tag ever made,
the review queue stages a fight between a real source and a fiction. And refusing untagged albums gates out precisely
the music the project was founded to manage.

Naming the path a source keeps every position intact at once: imports never block, sources are layers, claims are
honest, and the directory name's real information is captured rather than laundered through a fallback or discarded.

## Alternatives considered

- **Fallbacks recorded as `file_tags` claims** — the twin's shape for track titles; its own journal conceded the
  overstatement. Cheap today, phantom review conflicts tomorrow.
- **Refusing untagged albums** — the twin's shape for albums; contradicts the founding purpose.
- **Building the path source inside slice 1** — the data is available, but the machinery is not: a second source needs
  priorities and merge rules, which slice by data availability assigns to a later slice. Recording the decision now and
  the implementation later is the same move core-positions makes for the entity hierarchy (ADR 0006).
