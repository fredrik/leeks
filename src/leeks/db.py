"""The library on disk: root resolution, database, sessions.

The root is ~/Music/leeks, overridable through $LEEKS_ROOT — the
configuration punt from the slice 1 plan. Everything leeks owns lives
under it: the database at leeks.db, copied audio in album-<id>/.
"""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

MIGRATIONS = Path(__file__).parent / "migrations"


def library_root() -> Path:
    override = os.environ.get("LEEKS_ROOT")
    base = Path(override) if override else Path("~/Music/leeks")
    return base.expanduser()


def database_path() -> Path:
    return library_root() / "leeks.db"


def database_url() -> str:
    return f"sqlite:///{database_path()}"


def migrate() -> None:
    """Create the root and bring the database to the latest schema."""
    library_root().mkdir(parents=True, exist_ok=True)
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("sqlalchemy.url", database_url())
    command.upgrade(config, "head")


def session() -> Session:
    """A session against the migrated library database."""
    migrate()
    return Session(create_engine(database_url()))
