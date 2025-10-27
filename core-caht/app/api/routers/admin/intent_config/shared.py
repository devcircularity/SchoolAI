# app/api/routers/admin/intent_config/shared.py
"""Shared utilities and schemas for intent configuration management"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

def safe_enum_value(enum_field):
    """Safely extract value from enum field that might be string or enum"""
    if hasattr(enum_field, 'value'):
        return enum_field.value
    return str(enum_field)

# Shared Pydantic schemas
class VersionResponse(BaseModel):
    id: str
    name: str
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime]
    pattern_count: int
    template_count: int

class CreateVersionRequest(BaseModel):
    name: str
    notes: Optional[str] = None
    copy_from: Optional[str] = None  # Version ID to copy from

class PatternResponse(BaseModel):
    id: str
    handler: str
    intent: str
    kind: str
    pattern: str
    priority: int
    enabled: bool
    scope_school_id: Optional[str]
    created_at: datetime
    updated_at: datetime

class CreatePatternRequest(BaseModel):
    handler: str
    intent: str
    kind: str  # positive, negative, synonym
    pattern: str
    priority: int = 100
    enabled: bool = True
    scope_school_id: Optional[str] = None

class UpdatePatternRequest(BaseModel):
    handler: Optional[str] = None
    intent: Optional[str] = None
    kind: Optional[str] = None
    pattern: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    scope_school_id: Optional[str] = None

class TemplateResponse(BaseModel):
    id: str
    handler: str
    intent: Optional[str]
    template_type: str
    template_text: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

class CreateTemplateRequest(BaseModel):
    handler: str
    intent: Optional[str] = None
    template_type: str  # system, user, fallback_context
    template_text: str
    enabled: bool = True

class UpdateTemplateRequest(BaseModel):
    handler: Optional[str] = None
    intent: Optional[str] = None
    template_type: Optional[str] = None
    template_text: Optional[str] = None
    enabled: Optional[bool] = None

class LogResponse(BaseModel):
    id: str
    message: str
    llm_intent: Optional[str]
    llm_confidence: Optional[float]
    router_intent: Optional[str]
    router_reason: Optional[str]
    final_intent: str
    final_handler: str
    fallback_used: bool
    latency_ms: int
    created_at: datetime
    has_negative_rating: Optional[bool] = None
    user_rating: Optional[int] = None

class LogStatsResponse(BaseModel):
    total_logs: int
    fallback_rate: float
    avg_confidence: Optional[float]
    negative_ratings: int
    low_confidence_count: int
    unhandled_count: int
    top_intents: List[Dict[str, Any]]
    top_handlers: List[Dict[str, Any]]

class TestClassifyRequest(BaseModel):
    message: str
    school_id: Optional[str] = None

class TestClassifyResponse(BaseModel):
    message: str
    config_router_result: Optional[Dict[str, Any]]
    llm_classifier_result: Optional[Dict[str, Any]]
    final_decision: Dict[str, Any]
    processing_steps: List[str]