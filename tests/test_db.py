"""The library database: migration, idempotence, and ORM/schema parity."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, select, text

from leeks import db, orm

TABLES = {
    "albums",
    "tracks",
    "files",
    "artists",
    "artist_credits",
    "genres",
    "album_genres",
    "sources",
    "source_values",
}


def test_migrate_creates_the_library(leeks_root):
    with db.session() as session:
        assert (leeks_root / "leeks.db").exists()
        assert TABLES <= set(inspect(session.get_bind()).get_table_names())
        assert session.scalars(select(orm.Source.name)).all() == ["file_tags"]


def test_migrate_is_idempotent():
    db.migrate()
    db.migrate()
    with db.session() as session:
        assert len(session.scalars(select(orm.Source)).all()) == 1


def test_foreign_keys_are_enforced():
    # SQLite ships with foreign keys off; db.py must switch them on.
    with db.session() as session:
        assert session.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_migration_matches_orm_metadata():
    # The hand-written migration must stay in lockstep with the ORM models:
    # autogenerate against a freshly migrated database has nothing to add.
    db.migrate()
    engine = create_engine(db.database_url())
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diffs = compare_metadata(context, orm.Base.metadata)
    assert diffs == []
