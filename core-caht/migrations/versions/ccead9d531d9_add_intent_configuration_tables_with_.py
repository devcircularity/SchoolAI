"""Add intent configuration tables with proper enums

Revision ID: ccead9d531d9
Revises: 2d7f135790dc
Create Date: 2025-09-09 10:01:43.716984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ccead9d531d9'
down_revision: Union[str, Sequence[str], None] = '2d7f135790dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create enums once; columns will reference them without re-creating
    config_status_enum = postgresql.ENUM('active', 'candidate', 'archived', name='config_status', create_type=True)
    pattern_kind_enum = postgresql.ENUM('positive', 'negative', 'synonym', name='pattern_kind', create_type=True)
    template_type_enum = postgresql.ENUM('system', 'user', 'assistant', 'fallback_context', name='template_type', create_type=True)

    bind = op.get_bind()
    config_status_enum.create(bind=bind, checkfirst=True)
    pattern_kind_enum.create(bind=bind, checkfirst=True)
    template_type_enum.create(bind=bind, checkfirst=True)

    # Intent config versions table
    op.create_table('intent_config_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', postgresql.ENUM(name='config_status', create_type=False), nullable=False, server_default='candidate'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_intent_config_versions_status', 'intent_config_versions', ['status'])
    
    # Intent patterns table
    op.create_table('intent_patterns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('version_id', sa.String(), nullable=False),
        sa.Column('handler', sa.String(100), nullable=False),
        sa.Column('intent', sa.String(100), nullable=False),
        sa.Column('kind', postgresql.ENUM(name='pattern_kind', create_type=False), nullable=False),
        sa.Column('pattern', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scope_school_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['intent_config_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_intent_patterns_version_handler', 'intent_patterns', ['version_id', 'handler'])
    op.create_index('idx_intent_patterns_enabled', 'intent_patterns', ['enabled'])
    op.create_index('idx_intent_patterns_priority', 'intent_patterns', ['priority'])
    
    # Prompt templates table
    op.create_table('prompt_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('version_id', sa.String(), nullable=False),
        sa.Column('handler', sa.String(100), nullable=False),
        sa.Column('intent', sa.String(100), nullable=True),
        sa.Column('template_type', postgresql.ENUM(name='template_type', create_type=False), nullable=False),
        sa.Column('template_text', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scope_school_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['intent_config_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prompt_templates_version_handler', 'prompt_templates', ['version_id', 'handler'])
    op.create_index('idx_prompt_templates_enabled', 'prompt_templates', ['enabled'])
    
    # Routing logs table
    op.create_table('routing_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('message_id', sa.String(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('llm_intent', sa.String(100), nullable=True),
        sa.Column('llm_confidence', sa.Float(), nullable=True),
        sa.Column('llm_entities', sa.JSON(), nullable=True),
        sa.Column('router_intent', sa.String(100), nullable=True),
        sa.Column('router_reason', sa.String(255), nullable=True),
        sa.Column('final_intent', sa.String(100), nullable=False),
        sa.Column('final_handler', sa.String(100), nullable=False),
        sa.Column('fallback_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('version_id', sa.String(), nullable=False),
        sa.Column('school_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['intent_config_versions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_routing_logs_created_at', 'routing_logs', ['created_at'])
    op.create_index('idx_routing_logs_handler_intent', 'routing_logs', ['final_handler', 'final_intent'])
    op.create_index('idx_routing_logs_fallback', 'routing_logs', ['fallback_used'])
    op.create_index('idx_routing_logs_school', 'routing_logs', ['school_id'])


def downgrade():
    op.drop_table('routing_logs')
    op.drop_table('prompt_templates')
    op.drop_table('intent_patterns')
    op.drop_table('intent_config_versions')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS config_status CASCADE')
    op.execute('DROP TYPE IF EXISTS pattern_kind CASCADE')
    op.execute('DROP TYPE IF EXISTS template_type CASCADE')