"""add trains, train_live_status_cache, ride_intents train fields

Hand-written (per session notes: this DB has PostGIS tiger-geocoder tables not in Base.metadata,
so alembic autogenerate produces destructive noise — always hand-write here).

Revision ID: 8a1f2c9e4b77
Revises: 6dd4553facaf
Create Date: 2026-09-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "8a1f2c9e4b77"
down_revision = "6dd4553facaf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trains",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("train_number", sa.String(), nullable=False, unique=True),
        sa.Column("train_name", sa.String(), nullable=False),
        sa.Column("route", sa.JSON(), nullable=False),
        sa.Column("provider_source", sa.String(), nullable=False, server_default="railradar"),
        sa.Column("cached_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_trains_train_number", "trains", ["train_number"], unique=True)

    op.create_table(
        "train_live_status_cache",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("train_id", sa.Uuid(), sa.ForeignKey("trains.id"), nullable=False),
        sa.Column("travel_date", sa.Date(), nullable=False),
        sa.Column("delay_minutes", sa.Integer(), nullable=True),
        sa.Column("last_station_code", sa.String(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_source", sa.String(), nullable=False, server_default="railradar"),
    )
    op.create_index(
        "ix_train_live_status_cache_train_id", "train_live_status_cache", ["train_id"]
    )

    op.add_column(
        "ride_intents",
        sa.Column("selected_train_id", sa.Uuid(), sa.ForeignKey("trains.id"), nullable=True),
    )
    op.add_column("ride_intents", sa.Column("travel_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("ride_intents", "travel_date")
    op.drop_column("ride_intents", "selected_train_id")
    op.drop_index("ix_train_live_status_cache_train_id", table_name="train_live_status_cache")
    op.drop_table("train_live_status_cache")
    op.drop_index("ix_trains_train_number", table_name="trains")
    op.drop_table("trains")
