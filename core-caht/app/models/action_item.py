# app/models/action_item.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, UUID, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class SuggestionActionItem(Base):
    """Action items for tracking suggestion implementation"""
    __tablename__ = "suggestion_action_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    suggestion_id = Column(UUID(as_uuid=True), ForeignKey('intent_suggestions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Action item details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    implementation_type = Column(String(50), default="other", nullable=False)  # pattern, template, code_fix, documentation, other
    status = Column(String(20), default="pending", nullable=False)  # pending, in_progress, completed
    
    # Assignment and scheduling
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    suggestion = relationship("IntentSuggestion", back_populates="action_items_rel")
    assignee = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<ActionItem(id='{self.id}', title='{self.title}', status='{self.status}')>"