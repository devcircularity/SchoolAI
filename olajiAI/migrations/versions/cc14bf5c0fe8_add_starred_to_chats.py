"""add starred to chats

Revision ID: cc14bf5c0fe8
Revises: b7cf35b5c209
Create Date: 2025-08-12 12:45:36.337047
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "cc14bf5c0fe8"
down_revision: Union[str, None] = "b7cf35b5c209"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add column with default to backfill existing rows, then drop the default
    op.add_column(
        "chats",
        sa.Column("starred", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("ix_chats_starred", "chats", ["starred"])
    op.alter_column("chats", "starred", server_default=None)

def downgrade() -> None:
    op.drop_index("ix_chats_starred", table_name="chats")
    op.drop_column("chats", "starred")