# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

leeks is a music library organiser and spiritual successor to beets.

## Design principles

Keep it simple.

Don't add when you can delete.

## Documentation

Documentation is kept in the `docs` directory:

| Path           | Purpose                                                          |
| -------------- | ---------------------------------------------------------------- |
| `docs/adr`     | Proper ADR-style decision records. Official.                     |
| `docs/archive` | Where outdated documentation and implemented plans are archived. |
| `docs/design`  | Design documents. Should have a long expected lifetime.          |
| `docs/journal` | Date-stamped filenames that record specific sessions.            |
| `docs/plans`   | Where active plans live.                                         |

Claude should religiously use `docs` to document design decisions and other notable events.

Claude should keep existing documentation updated when code, design, etc is changed.

Claude should archive outdated documentation and plans that are already implemented.

## Spec-driven development

This project follows a spec-driven approach. The human coder is steering spec and plan, the agent is implementing.

We use [OpenSpec](https://github.com/Fission-AI/OpenSpec) to manage changes. Change artifacts (proposal, design, tasks)
and specs live in the `openspec` directory. The workflow is driven by the `/opsx:*` commands: `explore`, `propose`,
`apply`, `sync`, `archive`. OpenSpec changes are the working plans; `docs/adr` remains the home for durable decisions
that outlive a change.

## Local harness

Claude should strive to use an efficient local test harness to run and verify the code. The feedback loop should be as
tight as possible. Insist on improving the tooling if deemed less than perfect.

## Code

Remove dead code.

## Tooling

The project uses Python and uv. Never use pip, pip install, or python -m venv directly.

Developer tools (uv, just) are declared in `mise.toml`; each developer installs mise once globally. Python is managed by
uv via `.python-version`, not by mise, so there's a single source of truth for the interpreter version.

### Environment & packages

- `uv sync` — install/sync dependencies
- `uv add <pkg>` / `uv add --dev <pkg>` — add dependencies (never edit pyproject.toml dependency lists by hand)
- `uv run <cmd>` — run anything inside the project environment
- Python: compatibility floor is >=3.12 (`requires-python` in pyproject.toml); development runs on 3.14, pinned in
  `.python-version` via `uv python pin 3.14`. Only raise the floor when code actually uses a newer-version feature
- Build backend: uv_build

### Quality gates (run before considering a task done)

- `just fix` — apply formatting and lint autofixes, then type-check and test
- `just check` — read-only verification of the same gates (what CI runs)

The recipes live in the `justfile` and wrap: `ruff format`, `ruff check`, `mdformat` (markdown formatting, configured in
`.mdformat.toml`), `ty check` (ty, not mypy/pyright), and `pytest`. New behaviour requires new tests.

Markdown is formatted with mdformat (120-column wrap). When editing markdown, run `uv run mdformat <file>` (or
`just fix`) before considering the edit done.

### Database

- SQLAlchemy 2.0 style only (Mapped[] / mapped_column, select(); no legacy Query API)
- Schema changes always go through Alembic: `uv run alembic revision --autogenerate -m "..."` then review the generated
  migration by hand before committing
- Never modify the SQLite schema outside a migration

### Conventions

- CLI: click. Entry point is `leek` (singular)
- Pydantic v2 models (TrackInfo, AlbumInfo) are the pipeline lingua franca; SQLAlchemy ORM models are persistence only.
  Never pass ORM objects through pipeline code, never put business logic on ORM models
- File tag I/O goes through mediafile; MusicBrainz access through musicbrainzngs
- Matching utilities: jellyfish, lap, numpy
