"""Add public chat messages table

Revision ID: 2d7f135790dc
Revises: 2069512cbff5
Create Date: 2025-09-04 14:12:35.432235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2d7f135790dc'
down_revision: Union[str, Sequence[str], None] = '2069512cbff5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create public_chat_messages table
    op.create_table(
        'public_chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=False),
        sa.Column('ai_response', sa.Text(), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes
    op.create_index('idx_public_chat_session_id', 'public_chat_messages', ['session_id'])
    op.create_index('idx_public_chat_created_at', 'public_chat_messages', ['created_at'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_public_chat_created_at', table_name='public_chat_messages')
    op.drop_index('idx_public_chat_session_id', table_name='public_chat_messages')
    
    # Drop table
    op.drop_table('public_chat_messages')