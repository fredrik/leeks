# 0002 — Theme the CLI with Catppuccin Mocha

Status: Decided (2026-06-11)

## Decision

leeks' visual identity is the [Catppuccin Mocha](https://catppuccin.com/palette) palette. `leeks/theme.py` names the
palette as constants and applies it to rich-click's style globals; all future styled output (rich tables, progress,
errors) draws from the same constants. Styles are truecolor; rich downgrades them on less capable terminals and drops
them when output is piped or `NO_COLOR` is set.

## Context

The joy rule in [project principles](../design/project-principles.md) makes the CLI's look a requirement, not a garnish.
The CLI skeleton plan punted the theme decision to `leek list`; Fredrik resolved it early by choosing Catppuccin Mocha,
a widely-used community palette with an established style convention (mauve as primary accent, red for errors, green for
success) and sibling flavours if a light variant is ever wanted.

## Alternatives considered

- **rich-click defaults** — serviceable, but generic; leeks would have no look of its own.
- **A bespoke palette** — maximum identity, but palette design is real work and Catppuccin's is already good and
  documented.
- **Another Catppuccin flavour** (Latte, Frappé, Macchiato) — Mocha is the dark flavour and the de-facto default;
  terminals skew dark.
