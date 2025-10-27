"""add chat models without foreign keys

Revision ID: 278cb7cd4131
Revises: 71981b58e8fd
Create Date: 2025-08-22 18:11:31.430119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '278cb7cd4131'  # Fixed to match filename
down_revision: Union[str, Sequence[str], None] = '71981b58e8fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create the enum type if it doesn't exist
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT 1 FROM pg_type WHERE typname = 'messagetype'"
    )).fetchone()
    
    if not result:
        # Create the enum type only if it doesn't exist
        message_type_enum = postgresql.ENUM('USER', 'ASSISTANT', name='messagetype')
        message_type_enum.create(connection)
    
    # Create chat_conversations table
    op.create_table('chat_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('first_message', sa.Text(), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_type', postgresql.ENUM('USER', 'ASSISTANT', name='messagetype', create_type=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=True),
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        # Only keep the conversation foreign key since it's in the same file
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE')
        # Remove user_id and school_id foreign keys to avoid circular dependency
    )
    
    # Create indexes for performance
    op.create_index('ix_chat_conversations_user_school', 'chat_conversations', ['user_id', 'school_id'])
    op.create_index('ix_chat_conversations_last_activity', 'chat_conversations', ['last_activity'])
    op.create_index('ix_chat_messages_conversation', 'chat_messages', ['conversation_id'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])
    op.create_index('ix_chat_messages_user_school', 'chat_messages', ['user_id', 'school_id'])

def downgrade():
    op.drop_index('ix_chat_messages_user_school')
    op.drop_index('ix_chat_messages_created_at')
    op.drop_index('ix_chat_messages_conversation')
    op.drop_index('ix_chat_conversations_last_activity')
    op.drop_index('ix_chat_conversations_user_school')
    op.drop_table('chat_messages')
    op.drop_table('chat_conversations')
    
    # Drop the enum type if no other tables are using it
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.columns 
        WHERE data_type = 'USER-DEFINED' 
        AND udt_name = 'messagetype'
        AND table_name NOT IN ('chat_messages')
    """)).fetchone()
    
    if not result:
        # Safe to drop the enum since no other tables use it
        message_type_enum = postgresql.ENUM('USER', 'ASSISTANT', name='messagetype')
        message_type_enum.drop(connection)