"""add system settings table

Revision ID: 6bf9ed222185
Revises: da99bbf37425
Create Date: 2025-09-24 18:49:50.910860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql



# revision identifiers, used by Alembic.
revision: str = '6bf9ed222185'
down_revision: Union[str, Sequence[str], None] = 'da99bbf37425'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('key')
    )
    
    # Create index on updated_at for performance
    op.create_index('ix_system_settings_updated_at', 'system_settings', ['updated_at'])


def downgrade():
    op.drop_index('ix_system_settings_updated_at', table_name='system_settings')
    op.drop_table('system_settings')