"""add kyc_documents and ride booking prompt fields

Revision ID: 1b3868304348
Revises: fd133a1dd93d
Create Date: 2026-09-02 19:44:36.888113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1b3868304348'
down_revision: Union[str, None] = 'fd133a1dd93d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'kyc_documents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('rider_id', sa.Uuid(), nullable=False),
        sa.Column('document_type', sa.Enum('PAN', name='documenttype'), nullable=False),
        sa.Column('pan_number_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('pan_number_last4', sa.String(length=4), nullable=False),
        sa.Column('pan_name_on_document', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'VERIFIED', 'REJECTED', name='kycstatus'), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rider_id'], ['riders.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_kyc_documents_rider_id'), 'kyc_documents', ['rider_id'], unique=False)

    op.add_column('rides', sa.Column('origin_train_number', sa.String(length=10), nullable=True))
    op.add_column('rides', sa.Column('booking_prompted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('rides', 'booking_prompted_at')
    op.drop_column('rides', 'origin_train_number')

    op.drop_index(op.f('ix_kyc_documents_rider_id'), table_name='kyc_documents')
    op.drop_table('kyc_documents')

    op.execute('DROP TYPE IF EXISTS kycstatus')
    op.execute('DROP TYPE IF EXISTS documenttype')
