"""Add school WhatsApp settings table

Revision ID: 386262892046
Revises: 90d50fb15110
Create Date: 2025-08-26 15:27:50.856679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '386262892046'
down_revision: Union[str, Sequence[str], None] = '90d50fb15110'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create school_whatsapp_settings table
    op.create_table('school_whatsapp_settings',
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('bridge_connected', sa.Boolean(), nullable=False),
        sa.Column('connection_token', sa.String(length=128), nullable=True),
        sa.Column('last_connection_check', sa.DateTime(), nullable=True),
        sa.Column('last_successful_message', sa.DateTime(), nullable=True),
        sa.Column('bridge_url', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ),
        sa.PrimaryKeyConstraint('school_id')
    )
    
    # Create index on school_id for faster lookups (though it's already PK)
    op.create_index(op.f('ix_school_whatsapp_settings_school_id'), 'school_whatsapp_settings', ['school_id'], unique=True)
    
    # Optional: Create index on connection_token for faster lookups
    op.create_index(op.f('ix_school_whatsapp_settings_connection_token'), 'school_whatsapp_settings', ['connection_token'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_school_whatsapp_settings_connection_token'), table_name='school_whatsapp_settings')
    op.drop_index(op.f('ix_school_whatsapp_settings_school_id'), table_name='school_whatsapp_settings')
    
    # Drop table
    op.drop_table('school_whatsapp_settings')