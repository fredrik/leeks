# 0033 — Claim the path's release facts, claim-only

Status: Decided (2026-06-14)

## Decision

The path source claims three release facts a directory name carries that file tags do not: medium (the release's
physical form — vinyl, CD, cassette), region, and catalogue number. Each is a claim field in the registry
(`leeks/fields.py`), single-valued and album-level, and each is **claim-only**: it has no cast, so `merge()` gives it no
merged column. The facts live in the source layer, visible to `leek show --sources`, and nowhere else until a consumer
earns a column.

The parser classifies every bracketed group — `(...)`, `[...]`, `{...}` — by its content, not its bracket: the bracket
is punctuation, the content is the fact. A four-digit number in parens is the year; a token in the closed medium or
region vocabulary is that fact; a `{Label - Cat#}` brace yields the catalogue (the part after the " - "; the label is
discarded). Everything else is stripped from the title and claimed as nothing.

The encoding the `[FLAC]` token names is **not** a path claim. Encoding is a measurement read from the bytes (ADR 0007,
`File.format`); the path strips the token and asserts nothing from it.

A claim field gains a `tagged` flag, default true. The path-only facts set it false: no `AlbumInfo`/`TrackInfo`
attribute backs them, so the file_tags write path skips them and only the path source claims them.

## Context

Slice 6 of the path-source arc reads the facts a filename carries that tags and bytes do not. They are conflict-free —
only the path asserts them — so there is no cross-source resolution to design; the work is which facts to claim and
whether each earns a merged column.

Encoding (FLAC/MP3/V0) is a measurement (ADR 0007): the bytes state it, so claiming it from the path would duplicate a
measurement and breach the claims/measurements split. Medium — vinyl versus CD versus cassette — is a release fact the
bytes cannot reveal (a FLAC may be ripped from either), and is what MusicBrainz calls a release's format. The path
claims medium and never encoding.

Real names put medium in any bracket — `(Vinyl)`, `[CD]`, `{Cassette}` — so the bracket cannot classify the content;
only the content can. Classifying by content rather than bracket kind is what lets the year, medium, region, and
catalogue come from whichever bracket holds them.

A merged column costs an `Album` column, a migration, and a registry cast, and is justified only by a reader. No verb
reads medium, region, or catalogue yet; `show --sources` reads the source layer directly. So claim-only is the correct
default, following `tracktotal`, which has been a claimed field with no column since the registry began.

## Alternatives considered

- **Give each fact a merged column now** — rejected: a column without a consumer is machinery ahead of need; the cast,
  schema change, and migration wait for a verb that reads the fact.
- **Claim the label too** — deferred: a label is an entity (like artist), not a scalar string; the catalogue brace
  yields the catalogue and the label is discarded until a slice gives labels a home.
- **Add `medium`/`region`/`catalogue` attributes to `AlbumInfo`** so the file_tags write path reads them as `None` —
  rejected: it would put fields tags never fill on the tag-assembly model. The `tagged` flag records the truth instead —
  these fields have no file_tags reading.
- **Recognise the medium by bracket kind** (parens year, brackets encoding, braces label) — rejected: real names put
  medium in any bracket, so the bracket carries no meaning the content does not already.

## Consequences

- The medium and region vocabularies are small and closed; they catch the unambiguous tokens and stay silent on the
  rest, growing with the harness like the rest of the grammar.
- The catalogue is read only from the `{Label - Cat#}` form. A bare brace token is left unclaimed — it could be a label,
  a region, or a catalogue, and guessing would breach the parser's silence-over-guessing rule.
- `tagged` is the registry's first field that no source-of-truth model backs; a future tagged source for any of these
  facts flips the flag and joins the merge.
