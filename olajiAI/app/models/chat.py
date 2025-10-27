# app/models/chat.py (updated)
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from uuid import uuid4

from app.models.base import Base  # <-- use shared Base

class Chat(Base):
    __tablename__ = "chats"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    school_id = Column(String, nullable=False)
    system_facts_seeded = Column(Boolean, default=False)
    starred = Column(Boolean, default=False)  # New field for starring chats
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_chats_user_school', 'user_id', 'school_id'),
        Index('ix_chats_created_at', 'created_at'),
        Index('ix_chats_starred', 'starred'),
    )

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    chat_id = Column(String, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tool_call = Column(Text, nullable=True)
    tool_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    chat = relationship("Chat", back_populates="messages")

    __table_args__ = (
        Index('ix_messages_chat_id', 'chat_id'),
        Index('ix_messages_created_at', 'created_at'),
    )