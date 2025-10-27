# app/models/intent_suggestion.py - Complete model with enhanced fields and relationships
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, UUID, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.models.base import Base

class SuggestionStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    NEEDS_ANALYSIS = "needs_analysis"

class SuggestionType(PyEnum):
    REGEX_PATTERN = "regex_pattern"
    PROMPT_TEMPLATE = "prompt_template"
    INTENT_MAPPING = "intent_mapping"
    HANDLER_IMPROVEMENT = "handler_improvement"

class IntentSuggestion(Base):
    """Model for storing tester suggestions about intent improvements"""
    __tablename__ = "intent_suggestions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Links to source messages/logs
    chat_message_id = Column(UUID(as_uuid=True), ForeignKey('chat_messages.id', ondelete='SET NULL'), nullable=True, index=True)
    routing_log_id = Column(String(255), ForeignKey('routing_logs.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Suggestion metadata
    suggestion_type = Column(
        Enum(SuggestionType, values_callable=lambda x: [e.value for e in x]), 
        nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Suggested solution
    handler = Column(String(100), nullable=False)
    intent = Column(String(100), nullable=False)
    pattern = Column(Text, nullable=True)  # For regex patterns
    template_text = Column(Text, nullable=True)  # For prompt templates
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    
    # Notes and reasoning
    tester_note = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)  # Admin's response when approving/rejecting
    
    # Enhanced workflow fields
    admin_analysis = Column(Text, nullable=True)  # Detailed analysis of what needs to be done
    implementation_notes = Column(Text, nullable=True)  # Specific implementation instructions
    
    # Status tracking
    status = Column(
        Enum(SuggestionStatus, values_callable=lambda x: [e.value for e in x]), 
        default=SuggestionStatus.PENDING, 
        nullable=False, 
        index=True
    )
    
    # User tracking
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # School context
    school_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    implemented_at = Column(DateTime, nullable=True)
    
    # Version tracking (if implemented)
    implemented_version_id = Column(String(255), ForeignKey('intent_config_versions.id', ondelete='SET NULL'), nullable=True)
    implemented_pattern_id = Column(String(255), ForeignKey('intent_patterns.id', ondelete='SET NULL'), nullable=True)
    implemented_template_id = Column(String(255), ForeignKey('prompt_templates.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    chat_message = relationship("ChatMessage", foreign_keys=[chat_message_id])
    routing_log = relationship("RoutingLog", foreign_keys=[routing_log_id])
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    implemented_version = relationship("IntentConfigVersion", foreign_keys=[implemented_version_id])
    implemented_pattern = relationship("IntentPattern", foreign_keys=[implemented_pattern_id])
    implemented_template = relationship("PromptTemplate", foreign_keys=[implemented_template_id])
    
    # Action items relationship
    action_items_rel = relationship("SuggestionActionItem", back_populates="suggestion", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<IntentSuggestion(id='{self.id}', type='{self.suggestion_type}', status='{self.status}')>"