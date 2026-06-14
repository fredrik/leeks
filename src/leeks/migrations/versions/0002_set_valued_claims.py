"""Set-valued claims: a field may carry several values from one source.

Widens the source_values uniqueness key to include value, so a source can
claim several genres for one album (each its own row) while still being
barred from claiming the same one twice (ADR 0022). Existing single-valued
rows already satisfy the wider key, so there is no data to migrate.

SQLite cannot ALTER a constraint in place, so batch rebuilds the table. We
hand batch an explicit copy_from rather than letting it reflect: reflection
re-applies the naming convention to the existing CHECK and doubles its
prefix, drifting from the deterministic names 0001 and the ORM agree on.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

KEY = "uq_source_values_source_id"
NARROW = ["source_id", "entity_type", "entity_id", "field"]
WIDE = [*NARROW, "value"]


def _source_values(unique: list[str]) -> sa.Table:
    """The source_values table as 0001 built it, with the given unique key.

    Names every constraint exactly as 0001 did, so the batch rebuild
    reproduces them verbatim instead of re-deriving (and doubling) them.
    """
    return sa.Table(
        "source_values",
        sa.MetaData(),
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("source_id", sa.Integer, nullable=False),
        sa.Column("entity_type", sa.String, nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=False),
        sa.Column("field", sa.String, nullable=False),
        sa.Column("value", sa.String, nullable=False),
        sa.Column("added", sa.DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_source_values"),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], name="fk_source_values_source_id_sources"
        ),
        sa.CheckConstraint(
            "entity_type IN ('album', 'track')", name="ck_source_values_entity_type"
        ),
        sa.UniqueConstraint(*unique, name=KEY),
    )


def _rekey(was: list[str], now: list[str]) -> None:
    with op.batch_alter_table("source_values", copy_from=_source_values(was)) as batch:
        batch.drop_constraint(KEY, type_="unique")
        batch.create_unique_constraint(KEY, now)


def upgrade() -> None:
    _rekey(NARROW, WIDE)


def downgrade() -> None:
    _rekey(WIDE, NARROW)
