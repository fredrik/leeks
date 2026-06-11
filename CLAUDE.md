# CLAUDE.md

## Project

leeks is a music library organiser and spiritual successor to beets.

## Design principles

Keep it simple.

Don't add when you can delete.

## Documentation

Documentation lives in `docs/` — see `docs/README.md` for the directory taxonomy and lifecycles.

Claude should religiously document design decisions and notable events in `docs`, keep existing documentation updated as
code and design change, and archive what is outdated or implemented.

## Local harness

The ambition is a really good agentic feedback loop: Claude should be able to run, verify, and inspect everything
locally and fast. Today that is `just fix` / `just check`; as leeks grows, the harness grows with it — fixture audio
files, a scratch library to import into, parity harnesses for risky ports. When a feedback loop feels slow or blind,
improve the tooling before continuing with the task.

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

The recipes live in the `justfile` and wrap: `ruff format`, `ruff check`, `mdformat`, `ty check` (ty, not mypy/pyright),
and `pytest`. New behaviour requires new tests.

Markdown is formatted with mdformat (120-column wrap, configured in `.mdformat.toml`). When editing markdown, run
`uv run mdformat <file>` (or `just fix`) before considering the edit done.

### Database

- SQLAlchemy 2.0 style only (Mapped[] / mapped_column, select(); no legacy Query API)
- Schema changes always go through Alembic: `uv run alembic revision --autogenerate -m "..."` then review the generated
  migration by hand before committing
- Never modify the database schema outside a migration

### Conventions

- Core design constraints live in `docs/design/core-positions.md`. Read it before architectural work
- `docs/research/teebs/notes/` holds Fredrik's primary sources. Edit them only on his explicit request
- Planning and slicing principles live in `docs/design/project-principles.md`. Read it before planning work
- CLI: click. Entry point is `leek` (singular)
- Pydantic v2 models (TrackInfo, AlbumInfo) are the pipeline lingua franca; SQLAlchemy ORM models are persistence only.
  Never pass ORM objects through pipeline code, never put business logic on ORM models
- File tag I/O goes through mediafile; MusicBrainz access through musicbrainzngs
- Matching utilities: jellyfish, lap, numpy
