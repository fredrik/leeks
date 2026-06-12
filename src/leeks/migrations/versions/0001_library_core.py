"""Library core: the merged view file tags can populate, plus the source layer.

Revision ID: 0001
Revises:
Create Date: 2026-06-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "albums",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("year", sa.Integer),
        sa.Column("added", sa.DateTime, nullable=False),
    )
    op.create_table(
        "artists",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.UniqueConstraint("name", name="uq_artists_name"),
    )
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.UniqueConstraint("name", name="uq_genres_name"),
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.UniqueConstraint("name", name="uq_sources_name"),
    )
    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "album_id",
            sa.Integer,
            sa.ForeignKey("albums.id", name="fk_tracks_album_id_albums"),
            nullable=False,
        ),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("track", sa.Integer),
        sa.Column("added", sa.DateTime, nullable=False),
    )
    op.create_table(
        "files",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "track_id",
            sa.Integer,
            sa.ForeignKey("tracks.id", name="fk_files_track_id_tracks"),
            nullable=False,
        ),
        sa.Column("path", sa.String, nullable=False),
        sa.Column("source_path", sa.String, nullable=False),
        sa.Column("format", sa.String, nullable=False),
        sa.Column("bitrate", sa.Integer),
        sa.Column("samplerate", sa.Integer),
        sa.Column("channels", sa.Integer),
        sa.Column("duration", sa.Float),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String, nullable=False),
        sa.Column("mtime", sa.Float, nullable=False),
        sa.Column("added", sa.DateTime, nullable=False),
        sa.UniqueConstraint("path", name="uq_files_path"),
        sa.UniqueConstraint("source_path", name="uq_files_source_path"),
    )
    op.create_table(
        "artist_credits",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "artist_id",
            sa.Integer,
            sa.ForeignKey("artists.id", name="fk_artist_credits_artist_id_artists"),
            nullable=False,
        ),
        sa.Column(
            "album_id",
            sa.Integer,
            sa.ForeignKey("albums.id", name="fk_artist_credits_album_id_albums"),
        ),
        sa.Column(
            "track_id",
            sa.Integer,
            sa.ForeignKey("tracks.id", name="fk_artist_credits_track_id_tracks"),
        ),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.CheckConstraint(
            "(album_id IS NULL) != (track_id IS NULL)",
            name="ck_artist_credits_one_owner",
        ),
        sa.CheckConstraint(
            "role IN ('albumartist', 'artist')", name="ck_artist_credits_role"
        ),
    )
    op.create_table(
        "album_genres",
        sa.Column(
            "album_id",
            sa.Integer,
            sa.ForeignKey("albums.id", name="fk_album_genres_album_id_albums"),
            primary_key=True,
        ),
        sa.Column(
            "genre_id",
            sa.Integer,
            sa.ForeignKey("genres.id", name="fk_album_genres_genre_id_genres"),
            primary_key=True,
        ),
    )
    op.create_table(
        "source_values",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer,
            sa.ForeignKey("sources.id", name="fk_source_values_source_id_sources"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String, nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=False),
        sa.Column("field", sa.String, nullable=False),
        sa.Column("value", sa.String, nullable=False),
        sa.Column("added", sa.DateTime, nullable=False),
        sa.UniqueConstraint(
            "source_id",
            "entity_type",
            "entity_id",
            "field",
            name="uq_source_values_source_id",
        ),
        sa.CheckConstraint(
            "entity_type IN ('album', 'track')", name="ck_source_values_entity_type"
        ),
    )
    # file_tags exists from day one: it is the source every library starts with.
    op.execute("INSERT INTO sources (name) VALUES ('file_tags')")


def downgrade() -> None:
    op.drop_table("source_values")
    op.drop_table("album_genres")
    op.drop_table("artist_credits")
    op.drop_table("files")
    op.drop_table("tracks")
    op.drop_table("sources")
    op.drop_table("genres")
    op.drop_table("artists")
    op.drop_table("albums")
