"""Add phrase support to intent patterns

Revision ID: db4bbc7ece0e
Revises: 360afc2e8116
Create Date: 2025-09-11 20:06:43.026699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql  # Add this import


# revision identifiers, used by Alembic.
revision: str = 'db4bbc7ece0e'
down_revision: Union[str, Sequence[str], None] = '360afc2e8116'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add phrase-related columns to intent_patterns table"""
    
    # Add phrases column (array of text)
    op.add_column('intent_patterns', 
        sa.Column('phrases', postgresql.ARRAY(sa.String()), nullable=True)
    )
    
    # Add regex confidence column
    op.add_column('intent_patterns', 
        sa.Column('regex_confidence', sa.Float(), nullable=True)
    )
    
    # Add regex explanation column
    op.add_column('intent_patterns', 
        sa.Column('regex_explanation', sa.Text(), nullable=True)
    )
    
    # Add index on phrases for better search performance
    op.create_index('idx_intent_patterns_phrases', 'intent_patterns', ['phrases'], 
                   postgresql_using='gin')
    
    # Add check constraint for confidence range
    op.create_check_constraint(
        'ck_intent_patterns_confidence_range',
        'intent_patterns', 
        'regex_confidence IS NULL OR (regex_confidence >= 0.0 AND regex_confidence <= 1.0)'
    )


def downgrade():
    """Remove phrase-related columns from intent_patterns table"""
    
    # Drop check constraint
    op.drop_constraint('ck_intent_patterns_confidence_range', 'intent_patterns')
    
    # Drop index
    op.drop_index('idx_intent_patterns_phrases', table_name='intent_patterns')
    
    # Drop columns
    op.drop_column('intent_patterns', 'regex_explanation')
    op.drop_column('intent_patterns', 'regex_confidence')
    op.drop_column('intent_patterns', 'phrases')