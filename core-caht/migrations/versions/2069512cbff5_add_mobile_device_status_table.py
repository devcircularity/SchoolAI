"""Add mobile device status table

Revision ID: 2069512cbff5
Revises: 51f5ada4cf69
Create Date: 2025-08-27 04:58:35.980121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2069512cbff5'
down_revision: Union[str, Sequence[str], None] = '51f5ada4cf69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create mobile_device_status table
    op.create_table(
        'mobile_device_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', sa.String(length=128), nullable=False),
        
        # Device information
        sa.Column('app_version', sa.String(length=32), nullable=True),
        sa.Column('device_model', sa.String(length=128), nullable=True),
        sa.Column('android_version', sa.String(length=32), nullable=True),
        
        # Permission and connection status
        sa.Column('notification_access', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('sms_permission', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('listener_connected', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        # Last operation status
        sa.Column('last_forward_ok', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_sms_received_at', sa.DateTime(), nullable=True),
        
        # Network and connectivity info
        sa.Column('network_status', sa.String(length=32), nullable=True),
        sa.Column('battery_optimized', sa.Boolean(), nullable=True),
        
        # Timestamps
        sa.Column('first_seen_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_update_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_heartbeat_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        
        # Constraints
        sa.CheckConstraint("device_id != ''", name='ck_mobile_device_status_device_id_not_empty'),
        sa.UniqueConstraint('school_id', 'user_id', 'device_id', name='uq_mobile_device_status_school_user_device')
    )
    
    # Create indexes for better performance
    op.create_index('idx_mobile_device_status_school_user', 'mobile_device_status', ['school_id', 'user_id'])
    op.create_index('idx_mobile_device_status_heartbeat', 'mobile_device_status', ['last_heartbeat_at'])
    op.create_index('idx_mobile_device_status_school_heartbeat', 'mobile_device_status', ['school_id', 'last_heartbeat_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_mobile_device_status_school_heartbeat', table_name='mobile_device_status')
    op.drop_index('idx_mobile_device_status_heartbeat', table_name='mobile_device_status')
    op.drop_index('idx_mobile_device_status_school_user', table_name='mobile_device_status')
    
    # Drop the table
    op.drop_table('mobile_device_status')