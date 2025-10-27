"""Whatsapp qr saving

Revision ID: 51f5ada4cf69
Revises: 386262892046
Create Date: 2025-08-26 15:43:15.992818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '51f5ada4cf69'
down_revision: Union[str, Sequence[str], None] = '386262892046'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add QR code storage columns
    op.add_column('school_whatsapp_settings', sa.Column('qr_code', sa.String(length=10000), nullable=True))
    op.add_column('school_whatsapp_settings', sa.Column('qr_generated_at', sa.DateTime(), nullable=True))
    
    # Add index on qr_generated_at for efficient cleanup queries
    op.create_index(op.f('ix_school_whatsapp_settings_qr_generated_at'), 'school_whatsapp_settings', ['qr_generated_at'], unique=False)


def downgrade() -> None:
    # Drop index and columns
    op.drop_index(op.f('ix_school_whatsapp_settings_qr_generated_at'), table_name='school_whatsapp_settings')
    op.drop_column('school_whatsapp_settings', 'qr_generated_at')
    op.drop_column('school_whatsapp_settings', 'qr_code')