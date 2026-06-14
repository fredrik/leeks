"""The library database: migration, idempotence, and ORM/schema parity."""

import unicodedata

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, select, text

from leeks import db, orm

TABLES = {
    "albums",
    "tracks",
    "files",
    "artists",
    "genres",
    "album_genres",
    "sources",
    "source_values",
}


def test_migrate_creates_the_library(leeks_root):
    with db.session() as session:
        assert (leeks_root / "leeks.db").exists()
        assert TABLES <= set(inspect(session.get_bind()).get_table_names())
        # The two sources every library starts with, file_tags outranking path.
        sources = session.scalars(
            select(orm.Source).order_by(orm.Source.priority.desc())
        ).all()
        assert [(s.name, s.priority) for s in sources] == [
            ("file_tags", 100),
            ("path", 50),
        ]


def test_migrate_is_idempotent(leeks_root):
    db.migrate(leeks_root)
    db.migrate(leeks_root)
    with db.session() as session:
        assert len(session.scalars(select(orm.Source)).all()) == 2


def test_foreign_keys_are_enforced():
    # SQLite ships with foreign keys off; db.py must switch them on.
    with db.session() as session:
        assert session.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_search_fold_ignores_case_and_accents():
    # Search folds both, so åsa/Åsa/asa are one needle (ADR 0021).
    assert db.fold("Åsa") == db.fold("åsa") == db.fold("asa")
    assert db.fold("Vinterhök") == db.fold("vinterhok")
    # And whichever normalisation the haystack was stored in.
    assert db.fold(unicodedata.normalize("NFD", "Åsa")) == db.fold("Åsa")


def test_sort_key_orders_swedish():
    # Sorting keeps å/ä/ö distinct and last, in that order (ADR 0026).
    letters = ["Ö", "A", "Å", "Z", "Ä", "W"]
    assert sorted(letters, key=db.sort_key) == ["A", "W", "Z", "Å", "Ä", "Ö"]
    # Case-insensitive, foreign accents sort with their base letter.
    assert db.sort_key("ÅSA") == db.sort_key("åsa")
    assert db.sort_key("café") < db.sort_key("cafz")  # é sorts as e, before z
    # NFC and NFD spellings produce the same key.
    assert db.sort_key(unicodedata.normalize("NFD", "Öje")) == db.sort_key("Öje")


def test_sort_collation_is_registered_on_the_connection(leeks_root):
    # The ORDER BY collation must be live on every connection, not just in
    # Python — Åsa sorts after Z through SQL (ADR 0026).
    with db.session() as session:
        ordered = session.scalars(
            text(
                "SELECT 'Åsa' AS name UNION ALL SELECT 'Bo' UNION ALL "
                "SELECT 'Öje' UNION ALL SELECT 'alm' "
                f"ORDER BY name COLLATE {db.SORT_COLLATION}"
            )
        ).all()
    assert ordered == ["alm", "Bo", "Åsa", "Öje"]


def test_migration_matches_orm_metadata(leeks_root):
    # The hand-written migration must stay in lockstep with the ORM models:
    # autogenerate against a freshly migrated database has nothing to add.
    db.migrate(leeks_root)
    engine = create_engine(db.database_url(leeks_root))
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diffs = compare_metadata(context, orm.Base.metadata)
    assert diffs == []


def _claim(field: str, value: str) -> orm.SourceValue:
    from datetime import UTC, datetime

    return orm.SourceValue(
        source_id=1,  # file_tags, inserted at migration
        entity_type="album",
        entity_id=1,
        field=field,
        value=value,
        added=datetime.now(UTC).replace(tzinfo=None),
    )


def test_schema_bars_two_claims_for_a_single_valued_field(leeks_root):
    # Arity is the schema's job now, not the write path's (ADR 0025): one
    # source cannot claim two years for one album.
    import pytest
    from sqlalchemy.exc import IntegrityError

    with db.session() as session:
        session.add_all([_claim("year", "2019"), _claim("year", "2020")])
        with pytest.raises(IntegrityError):
            session.flush()


def test_schema_allows_several_genres_but_no_duplicate(leeks_root):
    # genre is set-valued, so several rows are fine — but the same one twice
    # is barred by the wide unique (ADR 0022/0025).
    import pytest
    from sqlalchemy.exc import IntegrityError

    with db.session() as session:
        session.add_all([_claim("genre", "Ambient"), _claim("genre", "Dub Techno")])
        session.flush()  # several genres: no violation
        session.add(_claim("genre", "Ambient"))
        with pytest.raises(IntegrityError):
            session.flush()
