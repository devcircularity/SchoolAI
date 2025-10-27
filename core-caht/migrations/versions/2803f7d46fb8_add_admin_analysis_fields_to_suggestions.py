"""Add admin analysis fields to suggestions

Revision ID: 2803f7d46fb8
Revises: db4bbc7ece0e
Create Date: 2025-09-12 06:35:48.190365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2803f7d46fb8'
down_revision: Union[str, Sequence[str], None] = 'db4bbc7ece0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('intent_suggestions', sa.Column('admin_analysis', sa.Text, nullable=True))
    op.add_column('intent_suggestions', sa.Column('implementation_notes', sa.Text, nullable=True))

def downgrade():
    op.drop_column('intent_suggestions', 'admin_analysis')
    op.drop_column('intent_suggestions', 'implementation_notes')