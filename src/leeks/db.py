"""The library on disk: root resolution, database, sessions.

The root is ~/Music/leeks, overridable through $LEEKS_ROOT — the
configuration punt from the slice 1 plan. Everything leeks owns lives
under it: the database at leeks.db, copied audio in album-<id>/.
"""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session

MIGRATIONS = Path(__file__).parent / "migrations"


def library_root() -> Path:
    override = os.environ.get("LEEKS_ROOT")
    base = Path(override) if override else Path("~/Music/leeks")
    return base.expanduser()


def database_url(root: Path) -> str:
    return f"sqlite:///{root / 'leeks.db'}"


def migrate(root: Path) -> None:
    """Create the root and bring its database to the latest schema."""
    root.mkdir(parents=True, exist_ok=True)
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("sqlalchemy.url", database_url(root))
    command.upgrade(config, "head")


@event.listens_for(Engine, "connect")
def _enforce_foreign_keys(connection, _record) -> None:
    # SQLite ships with foreign keys off; real foreign keys are a core position.
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def session(root: Path | None = None) -> Session:
    """A session against the migrated library database at the root."""
    if root is None:
        root = library_root()
    migrate(root)
    return Session(create_engine(database_url(root)))
