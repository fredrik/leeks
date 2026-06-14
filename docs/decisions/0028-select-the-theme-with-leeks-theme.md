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

The field colour vocabulary ([ADR 0024](0024-a-field-colour-vocabulary.md)) had already decoupled the views from raw hex
— every formatter read a role like `theme.ARTIST`. But the roles were authored as `ARTIST = f"bold {MAUVE}"` over a
module of colour constants, so "mauve" was a public name. Fredrik caught the smell: if a theme customises by setting
`mauve = "#..."`, then a theme wanting a green artist has to write `mauve = "bright green"` — a slot named for one
colour holding another. The name would lie.

The fix names the two layers honestly. **Roles** (`artist`) are the shared, stable contract the views read. **Colour
names** (`mauve`) are a private detail of each theme — Catppuccin calls its accent "mauve", Gruvbox calls its accent
"purple", and neither should borrow the other's vocabulary. So a theme binds roles to styles, and the colour names live
as locals inside the builder. Mocha's artist is `bold mauve`; Gruvbox's is `bold purple`; a future theme's could be
`bold green` — no lying, because there is no colour-named slot to lie into.

An environment variable (not a config file) is the whole selection mechanism, on purpose: leeks has no user-config
system yet, and `LEEKS_THEME` is read once at process start, so there is no live-switching machinery to build. When a
config system arrives, a theme becomes a setting that overlays this default; until then the env var is enough, and it
keeps the [dogfooding harness](../../CLAUDE.md) honest (`LEEKS_THEME=gruvbox leek list`).

`apply()` still writes rich-click's style globals at import — a known wart — but it is harmless here: selection is fixed
at startup, so there is nothing to re-apply. Parameterising it for live switching is deferred until something needs it.

## Alternatives considered

- **Palette slots named by colour, one shared vocabulary** — how ADR 0024 left it. A theme is just a set of hexes for
  `mauve`, `peach`, … and the vocabulary (`artist = bold mauve`) is written once. Simpler, but the slot names lie the
  moment a theme's accent isn't mauve. Rejected — it is the exact coupling this record removes.
- **Themes bind roles to bare concrete styles, no colour locals** — `artist = "bold #cba6f7"` directly. Honest, but a
  theme repeats a hex everywhere a colour recurs and there is no readable name while authoring. The private locals cost
  nothing and make each builder transcribe its published palette faithfully.
- **A `--theme` flag instead of an env var** — a flag is per-invocation and would want live re-application of the help
  globals (the `apply()` wart bites). An env var fits "set it once for my shell" and dodges that. A flag can come later
  if wanted; it would layer over this cleanly.
- **A config file** — the eventual home, but it drags in the whole (unbuilt) config-system question. Too much mechanism
  for picking a palette today.
