# 0024 — Give each field a colour, and let the artist pop

Status: Decided (2026-06-14)

## Decision

Every field has one hue, named once in `theme.py` and used in every view: the artist is mauve, the title bold white, the
album sapphire, the year peach, the genre green. Structural and technical fields — the track number, the file
measurements (duration, format, bitrate), the claim layer's field and source — stay muted (subtext/overlay), so the
content leads and the artist pops. The names live next to the palette constants
([ADR 0002](0002-catppuccin-mocha-theme.md)) as style fragments (`ARTIST = f"bold {MAUVE}"`), composing with bold and
italic; every formatter reads the role, not a raw colour. The Unknown bucket keeps its own look — dim italic
([ADR 0010](0010-the-library-tree-is-for-humans.md)) — because absence is not a field.

This is the human, on-a-terminal view only. The pipe stays bare and uncoloured, and the machine shapes (json, csv, tsv)
carry no styling at all ([ADR 0019](0019-the-default-output-is-for-humans-not-parsers.md)); colour is presentation, not
data.

Because the hue belongs to the field and not the view, `--fields` honours it too: a selected column renders exactly as
it does in the default view. This supersedes [ADR 0016](0016-select-fields-with-fields.md)'s note that the `--fields`
table was plain and unstyled — that rested on colour being a curated-view property, which this record reverses.

## Context

The theme was named early ([ADR 0002](0002-catppuccin-mocha-theme.md)) but spent sparingly: the listing and depth views
were almost monochrome, only the title earned bold, and the field a library is most often scanned by — the artist — did
not stand out. Deciding each field's colour once and applying it everywhere mirrors the typed-projection seam
([ADR 0014](0014-render-output-from-a-typed-projection.md)): one definition, read by every view, so the views cannot
drift apart. Holding colour to the content fields and leaving the technical ones grey is what lets the artist pop; a
view where everything is coloured has nothing that leads.

## Alternatives considered

- **Inline styles per view, no shared vocabulary** — how it already was. Rejected: the same field drifts to different
  colours across views, and there is no single place to retune the palette.
- **Colour everything**, including the measurements, track numbers, and sources — rejected because then nothing leads;
  the artist cannot pop in a field of equals. The muted technical fields are load-bearing.
- **Make the artist pop with bold alone, no new colour** — rejected because bold is already the title's signal; a second
  bold field competes rather than distinguishes. Hue is the free axis, and mauve is Catppuccin's primary accent.
