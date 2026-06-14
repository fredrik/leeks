"""Source priority and confidence, and the path source itself.

A second source needs three things this migration adds (ADR 0031): a
priority on each source so merge can pick a winner, a per-claim confidence
column for analyzer claims (NULL for a reader like file_tags), and the
`path` source row registered alongside file_tags. file_tags outranks path,
so tags win when present and the path fills gaps.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

FILE_TAGS_PRIORITY = 100
PATH_PRIORITY = 50


def upgrade() -> None:
    # Add priority with a temporary default so the existing file_tags row
    # fills, then set the real values and drop the default to match the ORM.
    with op.batch_alter_table("sources") as batch:
        batch.add_column(
            sa.Column(
                "priority",
                sa.Integer(),
                nullable=False,
                server_default=str(PATH_PRIORITY),
            )
        )
    op.execute(
        f"UPDATE sources SET priority = {FILE_TAGS_PRIORITY} WHERE name = 'file_tags'"
    )
    op.execute(f"INSERT INTO sources (name, priority) VALUES ('path', {PATH_PRIORITY})")
    with op.batch_alter_table("sources") as batch:
        batch.alter_column("priority", server_default=None)

    op.add_column("source_values", sa.Column("confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("source_values", "confidence")
    op.execute("DELETE FROM sources WHERE name = 'path'")
    with op.batch_alter_table("sources") as batch:
        batch.drop_column("priority")
