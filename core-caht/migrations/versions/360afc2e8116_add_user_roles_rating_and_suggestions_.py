"""Add user roles rating and suggestions clean

Revision ID: 360afc2e8116
Revises: ccead9d531d9
Create Date: 2025-09-10 21:08:06.100271

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '360afc2e8116'
down_revision: Union[str, Sequence[str], None] = 'ccead9d531d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user roles, rating system, and intent suggestions."""
    
    # 1. Add user role system columns
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    
    # 2. Update existing users
    op.execute("UPDATE users SET roles_csv = 'PARENT' WHERE roles_csv IS NULL OR roles_csv = ''")
    
    # 3. Add rating system to chat messages
    op.add_column('chat_messages', sa.Column('rating', sa.Integer(), nullable=True))
    op.add_column('chat_messages', sa.Column('rated_at', sa.DateTime(), nullable=True))
    
    # 4. Create enum types with error handling
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE suggestiontype AS ENUM ('regex_pattern', 'prompt_template', 'intent_mapping', 'handler_improvement');
        EXCEPTION
            WHEN duplicate_object THEN 
                RAISE NOTICE 'Type suggestiontype already exists, skipping creation';
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE suggestionstatus AS ENUM ('pending', 'approved', 'rejected', 'implemented');
        EXCEPTION
            WHEN duplicate_object THEN 
                RAISE NOTICE 'Type suggestionstatus already exists, skipping creation';
        END $$;
    """)
    
    # 5. Create intent_suggestions table
    op.execute("""
        CREATE TABLE intent_suggestions (
            id UUID PRIMARY KEY,
            chat_message_id UUID REFERENCES chat_messages(id) ON DELETE SET NULL,
            routing_log_id VARCHAR(255) REFERENCES routing_logs(id) ON DELETE SET NULL,
            suggestion_type suggestiontype NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            handler VARCHAR(100) NOT NULL,
            intent VARCHAR(100) NOT NULL,
            pattern TEXT,
            template_text TEXT,
            priority VARCHAR(20) DEFAULT 'medium' NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
            tester_note TEXT,
            admin_note TEXT,
            status suggestionstatus DEFAULT 'pending' NOT NULL,
            created_by UUID NOT NULL REFERENCES users(id),
            reviewed_by UUID REFERENCES users(id),
            school_id UUID,
            created_at TIMESTAMP DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
            reviewed_at TIMESTAMP,
            implemented_at TIMESTAMP,
            implemented_version_id VARCHAR(255) REFERENCES intent_config_versions(id) ON DELETE SET NULL,
            implemented_pattern_id VARCHAR(255) REFERENCES intent_patterns(id) ON DELETE SET NULL,
            implemented_template_id VARCHAR(255) REFERENCES prompt_templates(id) ON DELETE SET NULL
        );
    """)
    
    # 6. Create all indexes
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_roles_csv', 'users', ['roles_csv'])
    op.create_index('idx_users_last_login', 'users', ['last_login'])
    
    op.create_index('idx_chat_messages_rating', 'chat_messages', ['rating'])
    op.create_index('idx_chat_messages_rated_at', 'chat_messages', ['rated_at'])
    
    op.create_index('idx_intent_suggestions_chat_message_id', 'intent_suggestions', ['chat_message_id'])
    op.create_index('idx_intent_suggestions_routing_log_id', 'intent_suggestions', ['routing_log_id'])
    op.create_index('idx_intent_suggestions_status', 'intent_suggestions', ['status'])
    op.create_index('idx_intent_suggestions_created_by', 'intent_suggestions', ['created_by'])
    op.create_index('idx_intent_suggestions_reviewed_by', 'intent_suggestions', ['reviewed_by'])
    op.create_index('idx_intent_suggestions_school_id', 'intent_suggestions', ['school_id'])
    op.create_index('idx_intent_suggestions_created_at', 'intent_suggestions', ['created_at'])
    op.create_index('idx_intent_suggestions_suggestion_type', 'intent_suggestions', ['suggestion_type'])
    op.create_index('idx_intent_suggestions_priority', 'intent_suggestions', ['priority'])
    
    # 7. Create update trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_intent_suggestions_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER intent_suggestions_updated_at_trigger
            BEFORE UPDATE ON intent_suggestions
            FOR EACH ROW
            EXECUTE FUNCTION update_intent_suggestions_updated_at();
    """)


def downgrade() -> None:
    """Remove all added features."""
    
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS intent_suggestions_updated_at_trigger ON intent_suggestions")
    op.execute("DROP FUNCTION IF EXISTS update_intent_suggestions_updated_at()")
    
    # Drop indexes
    op.drop_index('idx_intent_suggestions_priority', table_name='intent_suggestions')
    op.drop_index('idx_intent_suggestions_suggestion_type', table_name='intent_suggestions')
    op.drop_index('idx_intent_suggestions_created_at', table_name='intent_suggestions')
    op.drop_index('idx_intent_suggestions_school_id', table_name='intent_suggestions')
    op.drop_index('idx_intent_suggestions_reviewed_by', table_name='intent_suggestions')
    op.drop_index('idx_intent_suggestions_created_by', table_name='intent_suggestions')
    op.drop_index('idx_intent_suggestions_status', table_name='intent_suggestions')
    op.drop_index('idx_intent_suggestions_routing_log_id', table_name='intent_suggestions')
    op.drop_index('idx_intent_suggestions_chat_message_id', table_name='intent_suggestions')
    
    op.drop_index('idx_chat_messages_rated_at', table_name='chat_messages')
    op.drop_index('idx_chat_messages_rating', table_name='chat_messages')
    
    op.drop_index('idx_users_last_login', table_name='users')
    op.drop_index('idx_users_roles_csv', table_name='users')
    op.drop_index('idx_users_is_active', table_name='users')
    
    # Drop table
    op.execute("DROP TABLE IF EXISTS intent_suggestions")
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS suggestionstatus")
    op.execute("DROP TYPE IF EXISTS suggestiontype")
    
    # Remove columns
    op.drop_column('chat_messages', 'rated_at')
    op.drop_column('chat_messages', 'rating')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'is_active')