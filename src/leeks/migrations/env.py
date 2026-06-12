"""Alembic environment: migrations run against the leeks library database."""

from alembic import context
from sqlalchemy import create_engine

from leeks import db
from leeks.orm import Base

config = context.config
target_metadata = Base.metadata


def url() -> str:
    # The CLI (alembic.ini) leaves the url blank; default to the library.
    return config.get_main_option("sqlalchemy.url") or db.database_url(
        db.library_root()
    )


def run_migrations_offline() -> None:
    context.configure(url=url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(url())
    with engine.connect() as connection:
        # render_as_batch: SQLite cannot ALTER in place; batch mode can.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
