"""Add password reset tokens table

Revision ID: dfb3203b0da5
Revises: 2803f7d46fb8
Create Date: 2025-09-22 14:07:23.509406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID



# revision identifiers, used by Alembic.
revision: str = 'dfb3203b0da5'
down_revision: Union[str, Sequence[str], None] = '2803f7d46fb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Ensure UUID extension exists
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create password_reset_tokens table
    op.create_table('password_reset_tokens',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_ip', sa.String(length=45), nullable=True),
        sa.Column('used_ip', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token')
    )
    
    # Create indexes for performance
    op.create_index('idx_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_password_reset_tokens_token', 'password_reset_tokens', ['token'])
    op.create_index('idx_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])
    op.create_index('idx_password_reset_tokens_used', 'password_reset_tokens', ['used'])
    
    # Create partial index for active tokens (unused and non-expired)
    op.execute(
        """
        CREATE INDEX idx_password_reset_tokens_active 
        ON password_reset_tokens(user_id, expires_at) 
        WHERE used = false
        """
    )
    
    # Add check constraint to ensure expires_at is in the future when created
    # Note: Removed this constraint as it can cause issues with timezone handling
    # op.create_check_constraint(
    #     'chk_expires_at_future',
    #     'password_reset_tokens',
    #     'expires_at > created_at'
    # )


def downgrade():
    # Drop indexes
    op.drop_index('idx_password_reset_tokens_active', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_used', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_user_id', table_name='password_reset_tokens')
    
    # Drop table
    op.drop_table('password_reset_tokens')