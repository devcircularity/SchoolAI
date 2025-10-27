# app/models/chat.py - Updated ChatMessage model with rating support
import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, UUID, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.models.base import Base

class MessageType(PyEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatConversation(Base):
    """Enhanced chat conversation model with persistent context"""
    __tablename__ = "chat_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    first_message = Column(Text, nullable=False)
    last_activity = Column(DateTime, nullable=False, default=func.now(), index=True)
    message_count = Column(Integer, default=0, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    
    # Store persistent context data as JSON
    context_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatConversation(id='{self.id}', title='{self.title}', user_id='{self.user_id}')>"

class ChatMessage(Base):
    """Enhanced chat message model with user feedback support"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('chat_conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    school_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    message_type = Column(Enum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True, index=True)
    
    # Context and response data stored as JSON
    context_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    
    # User feedback: +1 = thumbs up, -1 = thumbs down, None = not rated
    rating = Column(Integer, nullable=True, index=True)
    rated_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id='{self.id}', type='{self.message_type}', rating='{self.rating}')>"