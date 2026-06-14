# 0022 — Genre is a set-valued claim

Status: Decided (2026-06-14)

## Decision

A field may be **set-valued**, and genre is the first one: a source claims as many genres as it carries, each its own
`source_values` row. The uniqueness key widens to include the value —
`(source_id, entity_type, entity_id, field, value)` — so one source can make several genre claims for one album, but
never the same one twice.

Three rulings follow from that:

**The claim layer holds what the format hands us.** mediafile returns a file's genres as a list — multiple Vorbis
comments, ID3v2.4 multi-value frames, MP4 lists are all genuinely several values from one source, with no parsing
involved. We record that list verbatim, one claim per genre. We do *not* split a single delimited string like
`"Ambient; Modern Classical"` into parts: choosing a delimiter is heuristic, and heuristic extraction is an analyzer's
job (ADR 0007), deferred like the path source (ADR 0008).

**Arity is code, not schema.** Widening the key drops the database-level guarantee that title/year/artist are
single-valued per source. We accept that: the only thing universally meaningless is an *identical* duplicate claim, and
that is all the constraint now forbids. Which fields are single- versus set-valued is domain knowledge the write path
and merge carry — today, only `genre` is set-valued.

**Consensus on a set is unanimity on the whole set.** When an album's files disagree on their genre set, `file_tags`
claims nothing — exactly as a scalar field does under disagreement (ADR 0008). A source that disagrees with itself has
said nothing. The agreed set is stored sorted; order is not meaningful at the claim layer, and the merged genres list is
sorted for display regardless.

The merged view already modelled genres as a set (the `album_genres` junction). This decision only lets the *claim*
layer be as honest about multiplicity as the merged layer already was. While `file_tags` is the only source, identity
merge copies the set through unchanged; reconciling two sources' genre sets is the relational-merge problem the glossary
already defers to source #2.

## Context

`leek show` grew a genres list (ADR 0020), but nothing could populate it with more than one genre. Genre was recorded as
a single scalar claim, and the `source_values` uniqueness key — `(source_id, entity_type, entity_id, field)` — allowed
exactly one value per field per source. That key is right for a title or a year, where a source has one answer and a
second answer is a contradiction. It is wrong for genre, where a file legitimately carries several genres at once and
the format stores them as a set. The list had no real data behind it, and the corpus had no specimen to produce any.

## Alternatives considered

- **An ordinal column in the key** — `(…, field, ordinal)` keeps one row per scalar and records genre order. But SQLite
  treats NULLs as distinct, so scalars would need an `ordinal = 0` convention to stay constrained, and we have no use
  for genre *order*: the merged list sorts for display. More machinery for an ordering nothing reads.
- **Keep the claim scalar; split into genres in an analyzer** — smallest change, and right for a single delimited
  string. But it is wrong for the common case: formats natively hand us a list, with nothing to parse. Treating that
  list as one string would be the laundering ADR 0008 warns against.
- **Union as the consensus rule** — the truer rule for genre, and the one Fredrik flagged: three tracks tagged folk,
  jangle pop, and pop aren't *disagreeing*, they're each contributing a facet, and the album is their union. Genre is
  additive in a way a year or a title is not — two files can't both be right about the year, but they can both be right
  about a genre. Deferred deliberately: union is a genre-shaped softening of consensus, not a general rule, and the
  schema laid down here (one row per genre) is exactly what union will need. Unanimity is the honest, simple placeholder
  until that effort.
