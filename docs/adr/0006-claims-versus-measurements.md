# 0006 — The source layer stores claims, not measurements

## Decision

Metadata divides in two, and only one half goes through the source layer.

A *claim* is an assertion about the music that a source can disagree with: title, artist, album, year, genre, track
number. Claims are written as `source_values` rows — file tags are simply the claims of the `file_tags` source — and the
merged view is computed from them.

A *measurement* is a fact about the bytes: bitrate, sample rate, bit depth, channels, format, duration as decoded,
content hash, mtime. No source gets a vote on a measurement, so measurements never pass through `source_values`; they
are columns on the file row, written at import and refreshed by re-scanning the file.

The test for a borderline field is the entity it describes. Track length appears on both sides: the decoded duration of
*this file* is a measurement on the file row, while MusicBrainz's length for *the recording* is a claim like any other.
Same number, different subjects.

## Context

Without the distinction, the source layer fills with rows nothing will ever merge against. Bitrate stored as a
`file_tags` claim invites a second source to disagree with it, which is meaningless — another source has no opinion
about the bytes on this disk. Worse, it makes the source layer's real content harder to see: review queues and
disagreement queries would wade through fields that can never disagree.

The split also keeps the file row honest as the home of file-level fact (per the files-are-modelled position): what the
bytes are is knowable by reading them, needs no provenance, and is cheap to recompute.

## Alternatives considered

- **Everything through `source_values`** — uniform, one write path. But uniformity here is false: merge rules,
  confidence, and review are meaningless for measurements, and ~half the rows would exist only to satisfy the pattern.
- **Measurements as a privileged always-wins source** — keeps one storage mechanism by adding a special case to every
  merge rule. A special case that applies to a fixed set of fields is just a worse way of writing a column.
