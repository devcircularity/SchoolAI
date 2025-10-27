"""create chats/messages and migrate from old tables

Revision ID: b7cf35b5c209
Revises:
Create Date: 2025-08-12 06:06:55.965010
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b7cf35b5c209"
down_revision: Union[str, None] = None  # set to your previous revision id if you have one
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create chats/messages and migrate from old tables if present."""
    # --- New tables ---
    op.create_table(
        "chats",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("school_id", sa.String(), nullable=False),
        sa.Column("system_facts_seeded", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_chats_user_school", "chats", ["user_id", "school_id"])
    op.create_index("ix_chats_created_at", "chats", ["created_at"])

    op.create_table(
        "messages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("chat_id", sa.String(), sa.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),  # user / assistant / system
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_call", sa.Text(), nullable=True),
        sa.Column("tool_result", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    # --- Optional data migration from old tables ---
    bind = op.get_bind()
    insp = sa.inspect(bind)

    def has_table(name: str) -> bool:
        try:
            return name in insp.get_table_names()
        except Exception:
            return False

    # Adjust these if your old table names differ
    old_sessions = "chat_sessions"
    old_messages = "chat_messages"

    # Copy sessions to chats
    if has_table(old_sessions):
        bind.execute(
            sa.text(
                f"""
                INSERT INTO chats (id, title, user_id, school_id, system_facts_seeded, created_at, updated_at)
                SELECT id, title, user_id, school_id, :seeded, created_at, updated_at
                FROM {old_sessions}
                """
            ).bindparams(seeded=False)
        )

    # Copy messages to messages (session_id -> chat_id; tool_name -> tool_call; tool_result = NULL)
    if has_table(old_messages):
        # Not all legacy rows may have columns exactly as below; adjust if needed
        legacy_cols = {c["name"] for c in insp.get_columns(old_messages)}
        # minimally required legacy columns
        required = {"id", "session_id", "role", "content", "created_at"}
        if required.issubset(legacy_cols):
            tool_col = "tool_name" if "tool_name" in legacy_cols else None
            bind.execute(
                sa.text(
                    f"""
                    INSERT INTO messages (id, chat_id, role, content, tool_call, tool_result, created_at)
                    SELECT id, session_id, role, content, {(':tool' if tool_col else 'NULL')}, NULL, created_at
                    FROM {old_messages}
                    """
                ).bindparams(**({"tool": None} if not tool_col else {}))
            )


def downgrade() -> None:
    """Downgrade schema: drop messages and chats."""
    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_chat_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_chats_created_at", table_name="chats")
    op.drop_index("ix_chats_user_school", table_name="chats")
    op.drop_table("chats")