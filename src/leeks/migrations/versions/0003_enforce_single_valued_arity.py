"""Enforce single-valued arity at the schema, not just the write path.

A partial unique index gives every claim field the registry does not mark
set-valued at most one row per source — so a source cannot claim two years
for one album — while genre (and any future set field) stays free to
repeat by value (ADR 0025). The existing wide unique still bars identical
duplicates for every field; this adds the narrow one for the rest.

Existing rows already satisfy it: the write path never recorded two of a
single-valued field, so there is nothing to migrate.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

# The set-valued fields excluded from one-per-source; in step with the
# registry's MULTI_FIELDS at this revision (genre).
WHERE = "field NOT IN ('genre')"


def upgrade() -> None:
    op.create_index(
        "uq_source_values_single",
        "source_values",
        ["source_id", "entity_type", "entity_id", "field"],
        unique=True,
        sqlite_where=sa.text(WHERE),
    )


def downgrade() -> None:
    op.drop_index("uq_source_values_single", table_name="source_values")
