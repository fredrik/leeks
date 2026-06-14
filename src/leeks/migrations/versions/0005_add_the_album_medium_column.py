"""Add the album medium column.

medium (vinyl/CD/cassette) graduates from a claim-only field to a merged
column now that `leek show` reads it (ADR 0034). Nullable: most albums have
no medium claim, and merge() fills it from the path's claim when they do.
region and catalogue stay claim-only, so they get no column here.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("albums", sa.Column("medium", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("albums", "medium")
