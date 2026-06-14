# 0024 — Give each field a colour, and let the artist pop

Status: Decided (2026-06-14)

## Decision

Every field has one hue, named once in `theme.py` and used in every view, so the eye learns the vocabulary: the artist
is always mauve, the title bold white, the album sapphire, the year peach, the genre green. Structural and technical
fields — the track number, the file measurements (duration, format, bitrate), the claim layer's field and source — stay
muted (subtext/overlay), so the content leads and the artist pops. The names live next to the palette constants
([ADR 0002](0002-catppuccin-mocha-theme.md)) as style fragments (`ARTIST = f"bold {MAUVE}"`), so they compose with bold
and italic and every formatter reads the role, not a raw colour. The Unknown bucket keeps its own look — dim italic
([ADR 0010](0010-the-library-tree-is-for-humans.md)) — because absence is not a field.

This is the human, on-a-terminal view only. The pipe stays bare and uncoloured, and the machine shapes (json, csv, tsv)
carry no styling at all ([ADR 0019](0019-the-default-output-is-for-humans-not-parsers.md)); colour is presentation, not
data.

Because the hue belongs to the field and not the view, `--fields` honours it too: a selected column renders exactly as
it does in the default view. This supersedes [ADR 0016](0016-select-fields-with-fields.md)'s note that the `--fields`
table was plain and unstyled — that rested on colour being a curated-view property, which this record reverses.

## Context

The theme was named early ([ADR 0002](0002-catppuccin-mocha-theme.md)) but spent sparingly: the listing and depth views
were almost monochrome — the artist rendered in the same plain text as everything else, and only the title earned bold.
The thing a music library is most often scanned by — who made it — did not stand out at all. The fix is not to sprinkle
colour ad hoc but to decide, once, what each field's colour *means*, and apply it everywhere the field appears. A reader
who learns "mauve is the artist" on the shelf reads it the same way in an album heading, a track card, and the add
confirmation. The discipline mirrors the typed-projection seam
([ADR 0014](0014-render-output-from-a-typed-projection.md)): one definition, read by every view, so the views cannot
drift apart.

Holding colour to the content fields and leaving the technical ones grey is what lets the artist pop — a view where
everything is coloured has nothing that stands out.

## Alternatives considered

- **Inline styles per view, no shared vocabulary** — how it already was. Quick to add a colour, but the same field
  drifts to different colours across views and there is no single place to retune the palette. Rejected for the same
  reason the projection is shared: one seam, many readers.
- **Colour everything** — give the measurements, the track numbers, the sources their own hues too. Maximally colourful,
  but then nothing leads; the artist cannot pop in a field of equals. The muted technical fields are load- bearing.
- **Make the artist pop with bold alone, no new colour** — bold is already the title's signal; a second bold field
  competes rather than distinguishes. Hue is the free axis, and mauve is Catppuccin's primary accent — the natural
  choice for the primary field.
