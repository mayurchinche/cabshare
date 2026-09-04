"""add final_destination fields to ride_intents

Hand-written (this DB's PostGIS tiger-geocoder tables confuse autogenerate — see prior
migrations' notes).

Revision ID: 3f6e8a1d2c90
Revises: 8a1f2c9e4b77
Create Date: 2026-09-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "3f6e8a1d2c90"
down_revision = "8a1f2c9e4b77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ride_intents", sa.Column("final_destination", sa.String(length=200), nullable=True))
    op.add_column("ride_intents", sa.Column("final_destination_lat", sa.Float(), nullable=True))
    op.add_column("ride_intents", sa.Column("final_destination_lng", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("ride_intents", "final_destination_lng")
    op.drop_column("ride_intents", "final_destination_lat")
    op.drop_column("ride_intents", "final_destination")
