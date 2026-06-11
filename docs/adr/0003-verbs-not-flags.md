# 0003 — Verbs, not flags: the leek top-level interface

## Decision

leek's top level speaks in verbs. A bare `leek` prints a short *about* card — name, one-liner, a pointer to `leek help`.
`leek version` shows the version (with the sparkle). `leek help` shows the full command reference, and will later take
an optional command argument (`leek help add`). There are no top-level `--version` or `--about` flags; click's automatic
`--help` remains everywhere, since it costs nothing and renders the same text as `leek help`.

## Context

The skeleton shipped with the conventional `--version`/`--help` flags and bare `leek` falling through to full help.
Fredrik found the flag interface unlovely, and the verb form expresses a distinction flags cannot: *about* and *help*
are different documents. About is the greeting — short and sweet, stable as the CLI grows. Help is the reference — it
will become a long list of commands, and making it the default greeting would bury the introduction under the inventory.

## Alternatives considered

- **Conventional flags** (`--version`, bare `leek` shows help) — the skeleton's first shape; familiar, but conflates
  greeting with reference and reads as machinery rather than an invitation.
- **`leek about` as an explicit verb too** — possible later if anything ever needs to script the about card; bare `leek`
  covers the human case today.
