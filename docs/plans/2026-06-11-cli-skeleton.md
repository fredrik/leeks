# CLI skeleton — `leek`

Slice 0 of the [roadmap](2026-06-11-roadmap.md): the first runnable surface. The `leek` entry point wired through
`[project.scripts]`, `--version` and `--help`, no subcommands. Commands arrive with the slices that have data behind
them; this slice exists so that every later slice lands on a surface that already runs.

## Verification

- `tests/test_cli.py`, using click's `CliRunner`:
  - `leek --version` exits 0 and reports the version that `importlib.metadata` reports for the installed package — the
    test asserts against metadata, not a hardcoded string, so a version bump never breaks it.
  - `leek --help` exits 0 and includes the one-line project description.
  - Bare `leek` prints help and exits 0. A tool with no subcommands yet should greet, not error.
  - Help output piped to a non-terminal carries no ANSI escape codes — colour is for eyes, never for pipes. (Under
    `CliRunner` output is not a TTY, so the plain-text assertions above double as this guarantee.)
- One subprocess test invokes the installed `leek` console script (under `uv run pytest` the project venv's `bin` is on
  `PATH`). `CliRunner` never exercises the `[project.scripts]` wiring; this test is the only thing that proves the entry
  point actually resolves.
- `just check` passes.
- Dogfood by hand: `uv run leek` and `uv run leek --version`.

## What gets built

- `src/leeks/cli.py` — a group named `leek`. A group rather than a bare command, because every subsequent slice adds a
  subcommand to it; starting with a group means slice 1 adds `add` without restructuring anything.
- Colour from day one, via [rich-click](https://github.com/ewels/rich-click) (`uv add rich-click`): a drop-in wrapper
  that renders click help with rich. Commands stay ordinary click commands — no new API to learn, and rich itself
  becomes available for later slices' output (`list`, `info` tables). rich handles the colour discipline for free:
  styles are dropped when output is piped and when `NO_COLOR` is set.
- `--version` via `click.version_option(package_name="leeks")`, which reads the installed package metadata. The version
  lives only in `pyproject.toml`; there is no `__version__` string to fall out of sync — beets carried that duplication
  for years.
- `[project.scripts] leek = "leeks.cli:leek"` in `pyproject.toml`.
- Help text: the one-line project description, written to be worth reading. Fredrik wants leeks quite colourful, and the
  joy ethos backs him up — the help screen is the first thing leeks ever shows anyone, so it should already look like
  something you'd want to use.

## Exclusions and punts

- **No subcommands.** `add` opens slice 1.
- **No config file, no logging setup, no database or Alembic wiring.** All of it arrives with `leek add`, the first
  slice with data behind it.
- **No global options** (`--library`, `--verbose`, …). Punt: the first global option is added when its first real
  consumer exists, not before.
- **Open question: a leeks colour theme.** Colour itself is decided (in, from slice 0), but a deliberate palette — what
  leeks looks like, consistently, across commands — deserves more material to design against. Punt: rich-click's
  defaults for now; design the theme at `leek list`, the first slice with real output to style.

## Done means

Tests above pass, `just check` is green, `uv run leek --version` answers, and this plan moves to `docs/archive/plans/`.
