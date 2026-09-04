"""add stations table

Revision ID: 6dd4553facaf
Revises: 1b3868304348
Create Date: 2026-09-02 21:53:28.663919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6dd4553facaf'
down_revision: Union[str, None] = '1b3868304348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('station_code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('source_dataset_version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_stations_station_code'), 'stations', ['station_code'], unique=True)
    op.create_index(op.f('ix_stations_name'), 'stations', ['name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_stations_name'), table_name='stations')
    op.drop_index(op.f('ix_stations_station_code'), table_name='stations')
    op.drop_table('stations')
