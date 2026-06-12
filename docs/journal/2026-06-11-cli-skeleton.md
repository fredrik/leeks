# Slice 0: the CLI skeleton

Session record, 2026-06-11, written up the day after. Slice 0 went from just-in-time plan to landed in one session — and
the landing itself became the day's second story: the workflow conventions crystallised around the first branch to
travel them.

## The landings

| Marker  | What                                                                                    |
| ------- | --------------------------------------------------------------------------------------- |
| e87e159 | `Add CLI skeleton (Slice 0)` — plan, implementation, theme, sparkle, verb interface     |
| 4901d3e | `Adopt semi-linear git history` — the ethos amended from strict fast-forward to markers |
| 6bccae5 | `Add just land for semi-linear merges` — the convention wrapped in code, landing itself |
| e6bafd3 | `Add landing modes and drop the shortlog` — `--ff`, `--squash`, output polish           |

## The slice

The plan was written first and archived the same session (`docs/archive/plans/2026-06-11-cli-skeleton.md`), verification
leading: `CliRunner` tests plus one subprocess test, because `CliRunner` never exercises the `[project.scripts]` wiring.
What landed:

- The `leek` entry point as a rich-click group; version read from package metadata, no `__version__` to drift.
- Catppuccin Mocha as the visual identity ([ADR 0002](../adr/0002-catppuccin-mocha-theme.md)): `leeks/theme.py` names
  the palette, future styled output draws from the same constants. A behavioural test pins mauve's truecolor sequence
  under `FORCE_COLOR`; piped output stays clean.
- The sparkle: `leek version` animates the word through the Mocha accents (1.2s at 24fps), terminal-only, Ctrl-C
  skippable. The rainbow is the theme's, not HSV's.
- Verbs, not flags ([ADR 0003](../adr/0003-verbs-not-flags.md)): bare `leek` greets with a short about card, `version`
  and `help` are subcommands, `--help` kept since it's free. About and help are different documents — the greeting stays
  short while the reference grows.

## The conventions

The slice's interface work kept changing the process documents beneath it, deliberately:

- The principles' Ethos section became **Ethos and pathos** — the worktree rule is character, the joy rule is feeling.
- Strict fast-forward linearity gave way to **semi-linear history**: branches rebase, then land under a `--no-ff` marker
  with an imperative title plus a label when there is something to cite. `git log --first-parent` reads like the
  roadmap.
- `just land` wraps the convention: fzf picks the branch and the title, suggestions come from a file the readying agent
  leaves in `.git/info/land-suggestions/<branch>` (live Haiku call as fallback), cleanup removes the branch and worktree
  with non-destructive variants. `--ff` and `--squash` are the spelled-out exceptions; a squashed branch is
  force-deleted only after tree equality proves main holds everything it had.

## Specimens worth keeping

- click ≥ 8.2 exits 2 when a group gets no arguments; a tool with no subcommands yet should greet, not error — pinned by
  test so an upgrade can't regress it.
- `click.echo` strips ANSI when stdout is not a TTY, silently defeating rich's `FORCE_COLOR` rendering; the Mocha test
  caught it on the first run.
- Under `pipefail`, the landing script died cleaning up a branch with no worktree — found by testing all three modes in
  a throwaway clone, never by the happy path.
- Haiku, asked for titles in the form `'Imperative title (Label)'`, dutifully invented `(Workflow)` — format examples
  are law to small models; the label-when-citable rule had to move into the prompt.

## Left open

- The full Mocha theme — a deliberate, consistent palette across commands — waits for `leek list`, the first slice with
  real output to design against.
- `leek help <command>` waits for commands worth explaining.
- Slice 1 is next: `leek add`, where TrackInfo and AlbumInfo stop being theory.
