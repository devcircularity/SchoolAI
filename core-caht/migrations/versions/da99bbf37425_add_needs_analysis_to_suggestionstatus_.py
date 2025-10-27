"""add needs_analysis to suggestionstatus enum

Revision ID: da99bbf37425
Revises: 5437ba177027
Create Date: 2025-09-24 13:19:59.442589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da99bbf37425'
down_revision: Union[str, Sequence[str], None] = '5437ba177027'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    # Add new value to existing enum
    op.execute("ALTER TYPE suggestionstatus ADD VALUE IF NOT EXISTS 'needs_analysis'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # You would need to recreate the enum type without this value
    # For now, we'll just pass since removing enum values is complex
    pass