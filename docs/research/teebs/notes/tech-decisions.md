# Tech stack

> Converted to markdown from `tech-decisions.txt` (teebs@b817be9); the verbatim original is in git history.

- **Python** — beets' language; well-known.
- **SQLite** — a single-file database is portable and simple. Risk: might not be able to handle multi-concurrency, etc.
  If so, reevaluate.
- **Pydantic** for validation.
- **SQLAlchemy** for storage.
- **Alembic** for migrations.
- **click** for CLI.
- **pytest** for testing.
