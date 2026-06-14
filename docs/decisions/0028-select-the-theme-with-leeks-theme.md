# 0028 — Select the theme with `LEEKS_THEME`

Status: Decided (2026-06-14)

## Decision

A theme is a **role → style binding**, and `LEEKS_THEME` picks one at startup. leeks ships three:

- **mocha** (default) — Catppuccin Mocha, the dark pastel leeks started with
  ([ADR 0002](0002-catppuccin-mocha-theme.md)).
- **latte** — Catppuccin Latte, Mocha's light sibling, the same hues over a light base.
- **gruvbox** — warm, earthy, retro; something deliberately unlike the two Catppuccin flavours.

`theme.py` defines a `Theme` dataclass whose fields are leeks' **style roles** — `artist`, `title`, `album`, `year`,
`genre`, the text tiers (`body`, `muted`, `faint`, `border`), and the chrome (`success`, `link`, `error`, `warning`).
Each theme is one builder function that binds every role to a concrete rich style, authored with **colour names as
private locals** (`mauve`, `purple`, …) that never escape the function. The views and the `--help` styling read only
roles (`theme.ARTIST`, `apply()` → `ACTIVE.link`); neither knows a colour. An unknown or unset `LEEKS_THEME` falls back
to mocha rather than failing — a misremembered name still leaves leek usable.

This is presentation only: it honours `isatty` and `NO_COLOR` exactly as before, and the pipe and machine shapes (json,
csv, tsv) stay uncoloured ([ADR 0019](0019-the-default-output-is-for-humans-not-parsers.md)).

## Context

The field colour vocabulary ([ADR 0024](0024-a-field-colour-vocabulary.md)) decoupled the views from raw hex, but
authored the roles as `ARTIST = f"bold {MAUVE}"` over a module of colour constants — so "mauve" was a public name. A
theme wanting a green artist would have to write `mauve = "bright green"`: a slot named for one colour holding another.
The fix splits the two layers. Roles are the shared contract the views read; colour names are a private detail of each
theme — Catppuccin's accent is "mauve", Gruvbox's is "purple", and neither borrows the other's vocabulary.

An environment variable, not a config file, is the whole selection mechanism: leeks has no user-config system yet, and
`LEEKS_THEME` is read once at process start, so there is no live-switching machinery to build. It keeps the
[dogfooding harness](../../CLAUDE.md) honest (`LEEKS_THEME=gruvbox leek list`).

## Alternatives considered

- **Palette slots named by colour, one shared vocabulary** — how ADR 0024 left it: a theme is a set of hexes for
  `mauve`, `peach`, …. Rejected — the slot names lie the moment a theme's accent isn't mauve, the coupling this record
  removes.
- **Themes bind roles to bare concrete styles, no colour locals** — `artist = "bold #cba6f7"` directly. Rejected — a
  theme then repeats a hex everywhere a colour recurs, with no readable name while authoring.
- **A `--theme` flag instead of an env var** — rejected for now: a flag is per-invocation and would want live
  re-application of the help globals. An env var fits "set it once for my shell" and dodges that; a flag can layer over
  this cleanly later.
- **A config file** — the eventual home, but it drags in the whole unbuilt config-system question. Too much mechanism
  for picking a palette today; a theme becomes a setting that overlays this default once that system arrives.

## Consequences

`apply()` writes rich-click's style globals at import — a known wart, but harmless here since selection is fixed at
startup. Parameterising it for live switching is deferred until a `--theme` flag or config overlay needs it.
