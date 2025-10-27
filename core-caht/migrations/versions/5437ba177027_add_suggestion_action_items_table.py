"""add suggestion action items table

Revision ID: 5437ba177027
Revises: dfb3203b0da5
Create Date: 2025-09-24 08:47:58.371483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql



# revision identifiers, used by Alembic.
revision: str = '5437ba177027'
down_revision: Union[str, Sequence[str], None] = 'dfb3203b0da5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'suggestion_action_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('suggestion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('implementation_type', sa.String(50), nullable=False, server_default='other'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['suggestion_id'], ['intent_suggestions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_action_items_suggestion_id', 'suggestion_action_items', ['suggestion_id'])
    op.create_index('ix_action_items_status', 'suggestion_action_items', ['status'])


def downgrade():
    op.drop_index('ix_action_items_status', table_name='suggestion_action_items')
    op.drop_index('ix_action_items_suggestion_id', table_name='suggestion_action_items')
    op.drop_table('suggestion_action_items')