"""chat migration

Revision ID: 90d50fb15110
Revises: 278cb7cd4131
Create Date: 2025-08-24 04:24:47.650480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '90d50fb15110'
down_revision: Union[str, Sequence[str], None] = '278cb7cd4131'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add context_data column to chat_conversations table"""
    # Add context_data column as JSONB
    op.add_column('chat_conversations', 
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    
    # Create GIN index for efficient JSON queries
    op.create_index(
        'idx_chat_conversations_context_data',
        'chat_conversations', 
        ['context_data'],
        postgresql_using='gin'
    )
    
    # Create additional performance indexes if they don't exist
    op.create_index(
        'idx_chat_conversations_last_activity_user',
        'chat_conversations',
        ['user_id', 'school_id', 'last_activity'],
        postgresql_ops={'last_activity': 'DESC'}
    )
    
    op.create_index(
        'idx_chat_conversations_archived',
        'chat_conversations',
        ['user_id', 'school_id', 'is_archived', 'last_activity'],
        postgresql_ops={'last_activity': 'DESC'}
    )
    
    # Initialize existing conversations with empty context
    op.execute(
        "UPDATE chat_conversations SET context_data = '{}' WHERE context_data IS NULL"
    )


def downgrade() -> None:
    """Remove context_data column and related indexes"""
    # Drop indexes first
    op.drop_index('idx_chat_conversations_archived', table_name='chat_conversations')
    op.drop_index('idx_chat_conversations_last_activity_user', table_name='chat_conversations')
    op.drop_index('idx_chat_conversations_context_data', table_name='chat_conversations')
    
    # Drop the column
    op.drop_column('chat_conversations', 'context_data')