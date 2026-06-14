# 0003 — Speak in verbs, not flags, at the top level

Status: Decided (2026-06-11)

## Decision

leek's top level speaks in verbs. A bare `leek` prints a short about card — name, one-liner, a pointer to `leek help`.
`leek version` shows the version (with the sparkle). `leek help` shows the full command reference, and will later take
an optional command argument (`leek help add`). There are no top-level `--version` or `--about` flags; click's automatic
`--help` remains everywhere, since it costs nothing and renders the same text as `leek help`.

## Context

About and help are different documents: about is the greeting, short and stable as the CLI grows; help is the command
reference, which becomes a long list. A flag interface conflates the two and makes the reference the default greeting,
burying the introduction under the inventory. Verbs keep them separate.

## Alternatives considered

- **Conventional flags** (`--version`, bare `leek` shows help) — familiar, but conflates greeting with reference.
- **`leek about` as an explicit verb too** — possible later if anything needs to script the about card; bare `leek`
  covers the human case today.
