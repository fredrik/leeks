# 0008 — Claims record what sources say; the path is a source

Status: Decided (2026-06-12)

## Decision

The claim layer records only what a source actually says. Three rulings follow.

**Consensus is unanimity-or-nothing.** When an album's files disagree on an album-level tag (year, genre, tracktotal),
`file_tags` claims nothing for that field. A source that disagrees with itself has said nothing; resolving disagreement
is merge-and-review's business, not assembly's.

**Fallbacks are not claims.** When tags are silent, the NOT NULL merged columns (album title, track title) take the
directory name or file stem as working values, and `source_values` stays silent. `file_tags` never claims what no tag
said. An untagged album still enters the library.

**The path is a source.** Filesystem names carry real metadata —
`The Avalanches - Since I Left You (2001) [FLAC] {Scandinavia - XLCD 138}` asserts artist, title, year, format, region,
and catalogue number, release-level facts file tags often lack. That information enters the library as claims of a
`path` source. The filesystem literally says only the *name*; extracting title or year from it is parsing — heuristic,
capable of being wrong — so the path parser is an analyzer under ADR 0007 and its claims carry confidence.

The path source is a genuine second source, and identity merge cannot host two, so it arrives as its own slice once
merge machinery exists — plausibly before MusicBrainz, as a cheap local source to exercise two-source merging. Until
then, the fallbacks above stand as its placeholder.

## Context

The slice 1 parity experiment (journal, 2026-06-12) forked here: the zero-context twin recorded file stems as
`file_tags` title claims and refused albums with no album tag. Both carry costs this record avoids. A fabricated claim
manufactures conflict later — when MusicBrainz disagrees with a `file_tags` claim no tag made, the review queue stages a
real source against a fiction. Refusing untagged albums gates out precisely the music the project exists to manage, the
files with the worst metadata.

Naming the path a source keeps every position intact: imports never block, sources are layers, claims stay honest, and
the directory name's real information is captured rather than laundered through a fallback or discarded.

## Alternatives considered

- **Fallbacks recorded as `file_tags` claims** — the twin's shape for track titles; its own journal conceded the
  overstatement. Cheap today, phantom review conflicts tomorrow.
- **Refusing untagged albums** — the twin's shape for albums; contradicts the founding purpose.
- **Building the path source inside slice 1** — rejected: the data is available but the machinery is not. A second
  source needs priorities and merge rules, which slice-by-data-availability assigns later. Deciding now and implementing
  later is the move core-positions makes for the entity hierarchy (ADR 0006).
