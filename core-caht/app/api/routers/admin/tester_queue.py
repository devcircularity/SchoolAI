# app/api/routers/admin/tester_queue.py - Complete comprehensive implementation
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
from uuid import UUID

from app.core.db import get_db
from app.models.chat import ChatMessage, MessageType
from app.models.intent_config import RoutingLog
from app.models.intent_suggestion import IntentSuggestion, SuggestionStatus, SuggestionType
from app.api.deps.auth import require_tester

router = APIRouter(prefix="/tester", tags=["Tester - Feedback Queue"])

class ProblematicMessage(BaseModel):
    """Message that needs tester attention with comprehensive debugging info"""
    message_id: str
    conversation_id: str
    user_message: str
    assistant_response: str
    intent: Optional[str]
    rating: Optional[int]
    rated_at: Optional[datetime]
    created_at: datetime
    processing_time_ms: Optional[int]
    
    # Routing information
    routing_log_id: Optional[str]
    llm_intent: Optional[str]
    llm_confidence: Optional[float]
    router_intent: Optional[str]
    final_intent: Optional[str]
    fallback_used: Optional[bool]
    
    # Context for understanding the issue
    issue_type: str  # "negative_rating", "fallback", "low_confidence", "unhandled", "slow_response", "error_intent", "orphaned_log"
    priority: int    # 1 = high, 2 = medium, 3 = low
    
    # Additional debugging context
    conversation_context: Optional[dict] = None
    routing_reason: Optional[str] = None
    error_details: Optional[str] = None
    
    # User/school context
    school_id: Optional[str]
    user_id: str

class TesterSuggestion(BaseModel):
    """Updated suggestion model to match frontend wizard"""
    message_id: Optional[str] = None
    routing_log_id: Optional[str] = None
    suggestion_type: str  # Always set to appropriate type based on content
    title: str
    description: str
    handler: str
    intent: str
    pattern: Optional[str] = None
    template_text: Optional[str] = None
    priority: str = "medium"
    tester_note: Optional[str] = None

class TesterSuggestionResponse(BaseModel):
    """Response when a suggestion is fetched - Enhanced with full details"""
    id: str
    title: str
    suggestion_type: str
    handler: str
    intent: str
    status: str
    priority: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    admin_note: Optional[str]
    
    # Add the missing fields that contain the actual suggestion content
    description: str  # The main suggestion content
    pattern: Optional[str] = None  # Regex pattern for classification improvements
    template_text: Optional[str] = None  # Template for response improvements
    tester_note: Optional[str] = None  # Additional context from tester
    
    # Message context
    chat_message_id: Optional[str] = None
    routing_log_id: Optional[str] = None
    original_message: Optional[str] = None  # User message that triggered the suggestion
    assistant_response: Optional[str] = None  # AI response that had issues


class TesterStatsResponse(BaseModel):
    """Enhanced statistics for tester queue"""
    total_messages: int
    negative_ratings: int
    fallback_used: int
    low_confidence: int
    unhandled: int
    slow_responses: int
    error_intents: int
    orphaned_logs: int
    needs_attention: int
    by_priority: dict
    by_issue_type: dict

class QueueFilters(BaseModel):
    """Available filters for the queue"""
    priorities: List[int]
    issue_types: List[str]
    date_ranges: List[str]

class ConversationMessageResponse(BaseModel):
    """Message in a conversation for tester review"""
    id: str
    content: str
    role: str  # "user" or "assistant"
    timestamp: datetime
    intent: Optional[str] = None
    rating: Optional[int] = None
    processing_time_ms: Optional[int] = None
    is_problematic: bool = False  # Highlight the problematic message


# Update the get_tester_queue function in app/api/routers/admin/tester_queue.py

# app/api/routers/admin/tester_queue.py - Update the get_tester_queue function

@router.get("/queue", response_model=List[ProblematicMessage])
def get_tester_queue(
    priority: Optional[int] = Query(None, ge=1, le=3, description="Filter by priority (1=high, 2=medium, 3=low)"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    days_back: int = Query(7, ge=1, le=30, description="Days to look back"),
    school_id: Optional[str] = Query(None, description="Filter by specific school (optional for testers)"),
    show_suggested: bool = Query(False, description="Include messages that already have suggestions"),
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Get comprehensive queue of messages that need tester attention - Respects admin hide setting."""
    
    # Check if queue is hidden by admin
    from app.models.system_settings import SystemSetting
    hide_setting = db.query(SystemSetting).filter(
        SystemSetting.key == "hide_tester_queue"
    ).first()
    
    # Check if user is admin - using claims from JWT token
    is_admin = ctx.get("claims", {}).get("is_admin", False) or ctx.get("claims", {}).get("is_super_admin", False)
    
    # If hidden and user is not admin/super_admin, return empty queue
    if hide_setting and hide_setting.value.get("hidden", False):
        if not is_admin:
            print(f"Queue hidden from tester: {ctx['user'].full_name}")
            return []
    
    print(f"\n=== TESTER QUEUE - UPDATED VERSION ===")
    print(f"User: {ctx['user'].full_name}")
    print(f"Is Admin: {is_admin}")
    print(f"Queue Hidden: {hide_setting.value.get('hidden', False) if hide_setting else False}")
    print(f"Filters: priority={priority}, issue_type={issue_type}, days_back={days_back}, show_suggested={show_suggested}")
    
    # Calculate date threshold
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    
    # Get all message IDs that already have suggestions (unless explicitly requested)
    messages_with_suggestions = set()
    if not show_suggested:
        suggestion_query = db.query(IntentSuggestion.chat_message_id).filter(
            IntentSuggestion.chat_message_id.isnot(None),
            IntentSuggestion.created_at >= date_threshold
        )
        
        messages_with_suggestions = {str(msg_id) for (msg_id,) in suggestion_query.all() if msg_id}
        print(f"Found {len(messages_with_suggestions)} messages with existing suggestions")
    
    # Base query - ALL SCHOOLS for testers
    base_query = db.query(ChatMessage).filter(
        ChatMessage.message_type == MessageType.ASSISTANT,
        ChatMessage.created_at >= date_threshold
    )
    
    # Filter out messages that already have suggestions
    if messages_with_suggestions:
        base_query = base_query.filter(
            ~ChatMessage.id.in_([UUID(msg_id) for msg_id in messages_with_suggestions])
        )
    
    # Only filter by school if explicitly requested
    if school_id:
        try:
            school_uuid = UUID(school_id)
            base_query = base_query.filter(ChatMessage.school_id == school_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school ID format")
    
    problematic_messages = []
    processed_ids = set()
    
    print(f"\n🔍 FINDING PROBLEMATIC MESSAGES (excluding handled)...")
    
    # 1. NEGATIVE RATINGS - Highest Priority
    print("1. Checking negative ratings...")
    negative_messages = base_query.filter(ChatMessage.rating == -1).all()
    print(f"   Found {len(negative_messages)} messages with negative ratings (after filtering)")
    
    for msg in negative_messages:
        if str(msg.id) not in processed_ids:
            problematic_msg = _build_comprehensive_problematic_message(
                db, msg, "negative_rating", 1
            )
            if _apply_filters(problematic_msg, priority, issue_type):
                problematic_messages.append(problematic_msg)
                processed_ids.add(str(msg.id))
                print(f"   Added negative rating: {msg.id}")
    
    # 2. UNHANDLED INTENTS - High Priority  
    print("2. Checking unhandled intents...")
    unhandled_messages = base_query.filter(
        ChatMessage.intent.in_(['unhandled', 'unknown', 'ollama_fallback'])
    ).all()
    print(f"   Found {len(unhandled_messages)} unhandled messages (after filtering)")
    
    for msg in unhandled_messages:
        if str(msg.id) not in processed_ids:
            issue_type_name = f"intent_{msg.intent}" if msg.intent else "unhandled"
            problematic_msg = _build_comprehensive_problematic_message(
                db, msg, issue_type_name, 1
            )
            if _apply_filters(problematic_msg, priority, issue_type):
                problematic_messages.append(problematic_msg)
                processed_ids.add(str(msg.id))
                print(f"   Added unhandled intent: {msg.id} ({msg.intent})")
    
    # 3. ERROR INTENTS - High Priority
    print("3. Checking error intents...")
    error_messages = base_query.filter(
        or_(
            ChatMessage.intent == 'error',
            ChatMessage.intent.like('%error%'),
            ChatMessage.content.like('%error%')
        )
    ).all()
    print(f"   Found {len(error_messages)} error messages (after filtering)")
    
    for msg in error_messages:
        if str(msg.id) not in processed_ids:
            problematic_msg = _build_comprehensive_problematic_message(
                db, msg, "error_intent", 1
            )
            if _apply_filters(problematic_msg, priority, issue_type):
                problematic_messages.append(problematic_msg)
                processed_ids.add(str(msg.id))
                print(f"   Added error message: {msg.id}")
    
    # 4. ROUTING LOG ISSUES - Medium Priority
    print("4. Checking routing logs...")
    routing_query = db.query(RoutingLog).filter(
        RoutingLog.created_at >= date_threshold
    )
    if school_id:
        routing_query = routing_query.filter(RoutingLog.school_id == school_id)
    
    problematic_routes = routing_query.filter(
        or_(
            RoutingLog.fallback_used == True,
            RoutingLog.final_intent.in_(['unhandled', 'unknown', 'ollama_fallback'])
        )
    ).all()
    print(f"   Found {len(problematic_routes)} problematic routing logs")
    
    for route in problematic_routes:
        chat_msg = _find_message_for_routing_log(db, route)
        if chat_msg and str(chat_msg.id) not in processed_ids and str(chat_msg.id) not in messages_with_suggestions:
            issue_type_name = "fallback_used" if route.fallback_used else f"routing_{route.final_intent}"
            problematic_msg = _build_comprehensive_problematic_message(
                db, chat_msg, issue_type_name, 2, route
            )
            if _apply_filters(problematic_msg, priority, issue_type):
                problematic_messages.append(problematic_msg)
                processed_ids.add(str(chat_msg.id))
                print(f"   Added routing issue: {chat_msg.id} ({issue_type_name})")
    
    # Sort by priority, then by date
    problematic_messages.sort(key=lambda x: (x.priority, -x.created_at.timestamp()))
    
    # Final summary
    print(f"\n=== QUEUE SUMMARY ===")
    print(f"Total problematic messages: {len(problematic_messages)}")
    print(f"Messages filtered out (have suggestions): {len(messages_with_suggestions)}")
    
    result = problematic_messages[:limit]
    print(f"Returning {len(result)} messages after limit")
    
    return result

def _build_comprehensive_problematic_message(
    db: Session, 
    chat_msg: ChatMessage, 
    issue_type: str, 
    priority: int,
    routing_log: Optional[RoutingLog] = None
) -> ProblematicMessage:
    """Build a comprehensive problematic message with full debugging context"""
    
    # If no routing log provided, try to find one
    if not routing_log:
        routing_log = _find_routing_log_for_message(db, chat_msg)
    
    # Get the user message that preceded this
    user_msg = _get_preceding_user_message(db, chat_msg)
    
    # Extract additional debugging info from response_data
    response_data = chat_msg.response_data or {}
    
    # Get conversation context
    conversation_context = _get_conversation_context(db, chat_msg)
    
    # Build error details if available
    error_details = None
    if 'error' in chat_msg.content.lower() or chat_msg.intent and 'error' in chat_msg.intent:
        error_details = f"Content contains error indicators. Intent: {chat_msg.intent}"
    
    return ProblematicMessage(
        message_id=str(chat_msg.id),
        conversation_id=str(chat_msg.conversation_id),
        user_message=user_msg.content if user_msg else "Unknown",
        assistant_response=chat_msg.content,
        intent=chat_msg.intent,
        rating=chat_msg.rating,
        rated_at=chat_msg.rated_at,
        created_at=chat_msg.created_at,
        processing_time_ms=chat_msg.processing_time_ms,
        
        # Enhanced routing information
        routing_log_id=str(routing_log.id) if routing_log else None,
        llm_intent=routing_log.llm_intent if routing_log else response_data.get('llm_intent'),
        llm_confidence=routing_log.llm_confidence if routing_log else response_data.get('llm_confidence'),
        router_intent=routing_log.router_intent if routing_log else response_data.get('router_intent'),
        final_intent=routing_log.final_intent if routing_log else chat_msg.intent,
        fallback_used=routing_log.fallback_used if routing_log else response_data.get('fallback', False),
        
        # Issue classification
        issue_type=issue_type,
        priority=priority,
        
        # Additional debugging context
        conversation_context=conversation_context,
        routing_reason=routing_log.router_reason if routing_log else None,
        error_details=error_details,
        
        # Context
        school_id=str(chat_msg.school_id) if chat_msg.school_id else None,
        user_id=str(chat_msg.user_id)
    )

def _build_orphaned_routing_log_entry(routing_log: RoutingLog) -> ProblematicMessage:
    """Create entry for routing logs that don't have corresponding chat messages"""
    return ProblematicMessage(
        message_id=f"orphaned_{routing_log.id}",
        conversation_id=routing_log.conversation_id or "unknown",
        user_message=routing_log.message[:200] + "..." if len(routing_log.message) > 200 else routing_log.message,
        assistant_response="[No corresponding chat message found - orphaned routing log]",
        intent=routing_log.final_intent,
        rating=None,
        rated_at=None,
        created_at=routing_log.created_at,
        processing_time_ms=routing_log.latency_ms,
        
        # Routing information available
        routing_log_id=str(routing_log.id),
        llm_intent=routing_log.llm_intent,
        llm_confidence=routing_log.llm_confidence,
        router_intent=routing_log.router_intent,
        final_intent=routing_log.final_intent,
        fallback_used=routing_log.fallback_used,
        
        # Issue classification
        issue_type="orphaned_log",
        priority=3,  # Low priority
        
        # Additional context
        conversation_context={"type": "orphaned_routing_log"},
        routing_reason=routing_log.router_reason,
        error_details="Routing log exists but no corresponding chat message found",
        
        # Context
        school_id=routing_log.school_id,
        user_id=routing_log.user_id
    )

def _apply_filters(msg: ProblematicMessage, priority: Optional[int], issue_type: Optional[str]) -> bool:
    """Apply filters to determine if message should be included"""
    if priority is not None and msg.priority != priority:
        return False
    if issue_type and msg.issue_type != issue_type:
        return False
    return True

def _determine_routing_issue_type(routing_log: RoutingLog) -> str:
    """Determine issue type from routing log"""
    if routing_log.fallback_used:
        return "fallback"
    elif routing_log.final_intent in ["unhandled", "unknown", "ollama_fallback"]:
        return "unhandled"
    elif routing_log.llm_confidence and routing_log.llm_confidence < 0.6:
        return "low_confidence"
    else:
        return "routing_issue"

def _determine_routing_priority(routing_log: RoutingLog) -> int:
    """Determine priority from routing log"""
    if routing_log.fallback_used or routing_log.final_intent in ["unhandled", "unknown"]:
        return 1  # High
    elif routing_log.llm_confidence and routing_log.llm_confidence < 0.6:
        return 2  # Medium
    else:
        return 3  # Low

def _get_conversation_context(db: Session, chat_msg: ChatMessage) -> dict:
    """Get conversation context for debugging"""
    try:
        # Get recent messages in this conversation
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == chat_msg.conversation_id,
            ChatMessage.created_at <= chat_msg.created_at
        ).order_by(ChatMessage.created_at.desc()).limit(5).all()
        
        # Get conversation metadata
        conversation = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == chat_msg.conversation_id
        ).first()
        
        return {
            "message_count": len(recent_messages),
            "conversation_length": len(recent_messages),
            "recent_intents": [msg.intent for msg in recent_messages if msg.intent],
            "conversation_title": getattr(conversation, 'title', 'Unknown') if hasattr(conversation, 'title') else 'Unknown',
            "conversation_started": min(msg.created_at for msg in recent_messages).isoformat() if recent_messages else None
        }
    except Exception as e:
        return {"error": f"Failed to get conversation context: {str(e)}"}

def _find_routing_log_for_message(db: Session, chat_msg: ChatMessage) -> Optional[RoutingLog]:
    """Find the routing log that corresponds to a chat message using multiple strategies"""
    
    # Strategy 1: Check if routing_log_id is stored in response_data
    if chat_msg.response_data and chat_msg.response_data.get('routing_log_id'):
        routing_log = db.query(RoutingLog).filter(
            RoutingLog.id == chat_msg.response_data['routing_log_id']
        ).first()
        if routing_log:
            return routing_log
    
    # Strategy 2: Try exact content match
    routing_log = db.query(RoutingLog).filter(
        RoutingLog.message == chat_msg.content,
        RoutingLog.school_id == str(chat_msg.school_id),
        RoutingLog.user_id == str(chat_msg.user_id)
    ).first()
    
    if routing_log:
        return routing_log
    
    # Strategy 3: Try fuzzy match within conversation timeframe
    time_window = timedelta(minutes=15)  # Increased from 5 to 15 minutes
    routing_log = db.query(RoutingLog).filter(
        RoutingLog.conversation_id == str(chat_msg.conversation_id),
        RoutingLog.user_id == str(chat_msg.user_id),
        RoutingLog.created_at >= chat_msg.created_at - time_window,
        RoutingLog.created_at <= chat_msg.created_at + time_window
    ).order_by(
        func.abs(func.extract('epoch', RoutingLog.created_at - chat_msg.created_at))
    ).first()
    
    return routing_log

def _find_message_for_routing_log(db: Session, routing_log: RoutingLog) -> Optional[ChatMessage]:
    """Find the chat message that corresponds to a routing log"""
    
    # Strategy 1: Try exact content match
    chat_msg = db.query(ChatMessage).filter(
        ChatMessage.content == routing_log.message,
        ChatMessage.school_id == UUID(routing_log.school_id) if routing_log.school_id else None,
        ChatMessage.user_id == UUID(routing_log.user_id) if routing_log.user_id else None,
        ChatMessage.message_type == MessageType.ASSISTANT
    ).first()
    
    if chat_msg:
        return chat_msg
    
    # Strategy 2: Try conversation and time-based match
    if routing_log.conversation_id:
        time_window = timedelta(minutes=15)  # Increased window
        try:
            conversation_uuid = UUID(routing_log.conversation_id)
            chat_msg = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conversation_uuid,
                ChatMessage.message_type == MessageType.ASSISTANT,
                ChatMessage.created_at >= routing_log.created_at - time_window,
                ChatMessage.created_at <= routing_log.created_at + time_window
            ).order_by(
                func.abs(func.extract('epoch', ChatMessage.created_at - routing_log.created_at))
            ).first()
            
            return chat_msg
        except ValueError:
            # Invalid UUID format
            pass
    
    return None

def _get_preceding_user_message(db: Session, chat_msg: ChatMessage) -> Optional[ChatMessage]:
    """Get the user message that preceded this assistant message"""
    return db.query(ChatMessage).filter(
        ChatMessage.conversation_id == chat_msg.conversation_id,
        ChatMessage.message_type == MessageType.USER,
        ChatMessage.created_at < chat_msg.created_at
    ).order_by(desc(ChatMessage.created_at)).first()

@router.post("/suggestions", response_model=dict)
def submit_tester_suggestion(
    suggestion: TesterSuggestion,
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Submit a suggestion for fixing a problematic message - Updated for frontend compatibility."""
    
    print(f"\n=== TESTER SUGGESTION SUBMISSION ===")
    print(f"Message ID: {suggestion.message_id}")
    print(f"Suggestion Type: {suggestion.suggestion_type}")
    print(f"Title: {suggestion.title}")
    print(f"Description length: {len(suggestion.description) if suggestion.description else 0}")
    print(f"Handler: {suggestion.handler}")
    print(f"Intent: {suggestion.intent}")
    print(f"Priority: {suggestion.priority}")
    
    # Verify the message/log exists if provided
    if suggestion.message_id:
        try:
            message_uuid = UUID(suggestion.message_id)
            message = db.query(ChatMessage).filter(ChatMessage.id == message_uuid).first()
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            print(f"Found message: {message.content[:100]}...")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    if suggestion.routing_log_id:
        routing_log = db.query(RoutingLog).filter(RoutingLog.id == suggestion.routing_log_id).first()
        if not routing_log:
            raise HTTPException(status_code=404, detail="Routing log not found")
    
    # Map frontend suggestion types to backend enum values
    suggestion_type_mapping = {
        'regex_pattern': SuggestionType.REGEX_PATTERN,
        'prompt_template': SuggestionType.PROMPT_TEMPLATE,
        'intent_mapping': SuggestionType.INTENT_MAPPING,
        'handler_improvement': SuggestionType.HANDLER_IMPROVEMENT,
        'user_query': SuggestionType.REGEX_PATTERN,  # User query issues -> regex patterns
        'ai_response': SuggestionType.PROMPT_TEMPLATE  # AI response issues -> prompt templates
    }
    
    # Validate and map suggestion type
    if suggestion.suggestion_type not in suggestion_type_mapping:
        valid_types = list(suggestion_type_mapping.keys())
        raise HTTPException(status_code=400, detail=f"Invalid suggestion type. Must be one of: {valid_types}")
    
    suggestion_type_enum = suggestion_type_mapping[suggestion.suggestion_type]
    
    # Validate priority
    if suggestion.priority not in ["low", "medium", "high", "critical"]:
        raise HTTPException(status_code=400, detail="Priority must be one of: low, medium, high, critical")
    
    # Basic validation for required fields
    if not suggestion.title or not suggestion.description:
        raise HTTPException(status_code=400, detail="Title and description are required")
    
    if not suggestion.handler or not suggestion.intent:
        raise HTTPException(status_code=400, detail="Handler and intent are required")
    
    # For regex patterns, we'll allow empty pattern since the description explains the issue
    if suggestion_type_enum == SuggestionType.REGEX_PATTERN and suggestion.pattern:
        # Test compile the regex pattern if provided
        import re
        try:
            re.compile(suggestion.pattern, re.IGNORECASE)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {str(e)}")
    
    # For prompt templates, template_text is optional since description explains the improvement needed
    if suggestion_type_enum == SuggestionType.PROMPT_TEMPLATE and suggestion.template_text:
        # Basic validation for template text
        if len(suggestion.template_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Template text must be at least 10 characters")
    
    try:
        # Create the suggestion record
        suggestion_record = IntentSuggestion(
            id=uuid.uuid4(),
            chat_message_id=UUID(suggestion.message_id) if suggestion.message_id else None,
            routing_log_id=suggestion.routing_log_id,
            suggestion_type=suggestion_type_enum,
            title=suggestion.title,
            description=suggestion.description,
            handler=suggestion.handler,
            intent=suggestion.intent,
            pattern=suggestion.pattern,
            template_text=suggestion.template_text,
            priority=suggestion.priority,
            tester_note=suggestion.tester_note,
            status=SuggestionStatus.PENDING,
            created_by=ctx["user"].id,
            school_id=UUID(ctx["claims"].get("active_school_id")) if ctx["claims"].get("active_school_id") else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(suggestion_record)
        db.commit()
        
        print(f"✓ Successfully created suggestion: {suggestion_record.id}")
        
        return {
            "message": "Suggestion submitted successfully", 
            "suggestion_id": str(suggestion_record.id),
            "status": suggestion_record.status.value,
            "title": suggestion_record.title,
            "suggestion_type": suggestion_record.suggestion_type.value,
            "priority": suggestion_record.priority,
            "created_at": suggestion_record.created_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error submitting suggestion: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        
        # More detailed error logging
        if hasattr(e, 'orig'):
            print(f"Database error details: {e.orig}")
        
        raise HTTPException(status_code=500, detail=f"Failed to submit suggestion: {str(e)}")



# In app/api/routers/admin/tester_queue.py - Update the get_my_suggestions endpoint

@router.get("/suggestions", response_model=List[TesterSuggestionResponse])
def get_my_suggestions(
    limit: int = Query(100, ge=1, le=500, description="Number of suggestions to return"),  # Increased limit
    status: Optional[str] = Query(None, description="Filter by status"),
    suggestion_type: Optional[str] = Query(None, description="Filter by suggestion type"),
    page: int = Query(1, ge=1, description="Page number for pagination"),  # Add pagination
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Get suggestions submitted by the current tester - Enhanced with pagination and higher limits"""
    
    # Build query with eager loading for related data
    query = db.query(IntentSuggestion).options(
        joinedload(IntentSuggestion.chat_message)
    ).filter(
        IntentSuggestion.created_by == ctx["user"].id
    )
    
    # Apply filters
    if status:
        try:
            status_enum = SuggestionStatus(status)
            query = query.filter(IntentSuggestion.status == status_enum)
        except ValueError:
            valid_statuses = [s.value for s in SuggestionStatus]
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    if suggestion_type:
        try:
            type_enum = SuggestionType(suggestion_type)
            query = query.filter(IntentSuggestion.suggestion_type == type_enum)
        except ValueError:
            valid_types = [t.value for t in SuggestionType]
            raise HTTPException(status_code=400, detail=f"Invalid suggestion type. Must be one of: {valid_types}")
    
    # Get total count for reference
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    suggestions = query.order_by(desc(IntentSuggestion.created_at)).offset(offset).limit(limit).all()
    
    print(f"Tester {ctx['user'].full_name} has {total_count} total suggestions, returning {len(suggestions)} for page {page}")
    
    result = []
    for suggestion in suggestions:
        # Get original message context if available
        original_message = None
        assistant_response = None
        
        if suggestion.chat_message:
            # Get the user message that preceded the problematic AI response
            original_message = _get_user_message_before(db, suggestion.chat_message)
            assistant_response = suggestion.chat_message.content
        
        result.append(TesterSuggestionResponse(
            id=str(suggestion.id),
            title=suggestion.title,
            suggestion_type=suggestion.suggestion_type.value,
            handler=suggestion.handler,
            intent=suggestion.intent,
            status=suggestion.status.value,
            priority=suggestion.priority,
            created_at=suggestion.created_at,
            reviewed_at=suggestion.reviewed_at,
            admin_note=suggestion.admin_note,
            
            # Add the full suggestion content
            description=suggestion.description,
            pattern=suggestion.pattern,
            template_text=suggestion.template_text,
            tester_note=suggestion.tester_note,
            
            # Message context
            chat_message_id=str(suggestion.chat_message_id) if suggestion.chat_message_id else None,
            routing_log_id=suggestion.routing_log_id,
            original_message=original_message,
            assistant_response=assistant_response
        ))
    
    # Log the total for debugging
    if total_count > limit:
        print(f"WARNING: Tester has {total_count} suggestions but only showing {len(result)}. Consider implementing pagination in frontend.")
    
    return result

@router.get("/stats", response_model=TesterStatsResponse)
def get_tester_stats(
    days_back: int = Query(7, ge=1, le=30, description="Days to look back for statistics"),
    school_id: Optional[str] = Query(None, description="Filter by specific school"),
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics for tester queue and problematic messages."""
    
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    
    # Base query for assistant messages in the time period
    base_query = db.query(ChatMessage).filter(
        ChatMessage.message_type == MessageType.ASSISTANT,
        ChatMessage.created_at >= date_threshold
    )
    
    # Add school filter if provided
    if school_id:
        try:
            school_uuid = UUID(school_id)
            base_query = base_query.filter(ChatMessage.school_id == school_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school ID format")
    
    # Count total messages
    total_messages = base_query.count()
    
    # Count negative ratings
    negative_ratings = base_query.filter(ChatMessage.rating == -1).count()
    
    # Count fallback usage (multiple indicators)
    fallback_used = 0
    fallback_used += base_query.filter(ChatMessage.response_data.op('->>')('fallback') == 'true').count()
    fallback_used += base_query.filter(ChatMessage.intent == 'ollama_fallback').count()
    fallback_used += base_query.filter(ChatMessage.intent == 'unhandled').count()
    
    # Count routing log issues
    routing_log_query = db.query(RoutingLog).filter(
        RoutingLog.created_at >= date_threshold
    )
    if school_id:
        routing_log_query = routing_log_query.filter(RoutingLog.school_id == school_id)
    
    # Low confidence routing decisions
    low_confidence = routing_log_query.filter(
        RoutingLog.llm_confidence < 0.6,
        RoutingLog.llm_confidence.isnot(None)
    ).count()
    
    # Unhandled intents
    unhandled = routing_log_query.filter(
        RoutingLog.final_intent.in_(["unhandled", "unknown", "ollama_fallback"])
    ).count()
    
    # Performance issues
    slow_responses = base_query.filter(
        ChatMessage.processing_time_ms > 10000  # > 10 seconds
    ).count()
    
    # Error intents
    error_intents = base_query.filter(
        or_(
            ChatMessage.intent.like('%error%'),
            ChatMessage.intent == 'file_processing_error',
            ChatMessage.content.like('%error%')
        )
    ).count()
    
    # Orphaned routing logs (logs without corresponding messages)
    all_routing_logs = routing_log_query.count()
    matched_logs = routing_log_query.filter(
        RoutingLog.message_id.isnot(None)
    ).count()
    orphaned_logs = all_routing_logs - matched_logs
    
    # Calculate total needing attention (deduplicated estimate)
    # This is a simplified count - the actual queue does deduplication
    unique_issues = set()
    
    # Add message IDs from different issue types
    negative_rated_ids = [str(msg.id) for msg in base_query.filter(ChatMessage.rating == -1).all()]
    fallback_msg_ids = [str(msg.id) for msg in base_query.filter(
        or_(
            ChatMessage.response_data.op('->>')('fallback') == 'true',
            ChatMessage.intent == 'ollama_fallback',
            ChatMessage.intent == 'unhandled'
        )
    ).all()]
    slow_msg_ids = [str(msg.id) for msg in base_query.filter(ChatMessage.processing_time_ms > 10000).all()]
    error_msg_ids = [str(msg.id) for msg in base_query.filter(
        or_(
            ChatMessage.intent.like('%error%'),
            ChatMessage.intent == 'file_processing_error'
        )
    ).all()]
    
    unique_issues.update(negative_rated_ids)
    unique_issues.update(fallback_msg_ids)
    unique_issues.update(slow_msg_ids)
    unique_issues.update(error_msg_ids)
    
    # Add estimate for routing issues that might not have corresponding messages
    needs_attention = len(unique_issues) + orphaned_logs
    
    # Enhanced breakdown by issue type
    by_issue_type = {
        "negative_rating": negative_ratings,
        "fallback": fallback_used,
        "low_confidence": low_confidence,
        "unhandled": unhandled,
        "slow_response": slow_responses,
        "error_intent": error_intents,
        "orphaned_log": orphaned_logs
    }
    
    # Enhanced priority breakdown
    by_priority = {
        "high": negative_ratings + fallback_used + unhandled + error_intents,  # Priority 1
        "medium": low_confidence + slow_responses,  # Priority 2  
        "low": orphaned_logs  # Priority 3
    }
    
    return TesterStatsResponse(
        total_messages=total_messages,
        negative_ratings=negative_ratings,
        fallback_used=fallback_used,
        low_confidence=low_confidence,
        unhandled=unhandled,
        slow_responses=slow_responses,
        error_intents=error_intents,
        orphaned_logs=orphaned_logs,
        needs_attention=needs_attention,
        by_priority=by_priority,
        by_issue_type=by_issue_type
    )

@router.get("/filters", response_model=QueueFilters)
def get_queue_filters(
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Get available filter options for the comprehensive tester queue"""
    
    return QueueFilters(
        priorities=[1, 2, 3],  # High, Medium, Low
        issue_types=[
            "negative_rating",    # Thumbs down from users
            "fallback",          # System fell back to generic responses
            "low_confidence",    # LLM classifier had low confidence
            "unhandled",         # Intent couldn't be handled
            "slow_response",     # Processing took too long
            "error_intent",      # Response had error-related intent
            "orphaned_log",      # Routing log without corresponding message
            "ollama_fallback",   # Specific Ollama fallback
            "routing_issue"      # General routing problems
        ],
        date_ranges=["1", "3", "7", "14", "30"]  # Days
    )

@router.get("/conversation/{conversation_id}", response_model=List[ConversationMessageResponse])
def get_conversation_for_tester(
    conversation_id: str,
    message_id: Optional[str] = Query(None, description="Focus on specific message and its context"),
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Get conversation context for tester review - focused on problematic message if specified"""
    
    try:
        conversation_uuid = UUID(conversation_id)
        target_message_uuid = UUID(message_id) if message_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation or message ID format")
    
    print(f"\n=== TESTER CONVERSATION REQUEST ===")
    print(f"Conversation ID: {conversation_id}")
    print(f"Target Message ID: {message_id}")
    print(f"Requested by: {ctx['user'].full_name}")
    
    if target_message_uuid:
        # Focused view: Get the specific problematic message and its preceding user message
        target_message = db.query(ChatMessage).filter(
            ChatMessage.id == target_message_uuid
        ).first()
        
        if not target_message:
            raise HTTPException(status_code=404, detail="Target message not found")
        
        if target_message.conversation_id != conversation_uuid:
            raise HTTPException(status_code=400, detail="Message does not belong to this conversation")
        
        # Get the user message that preceded this assistant message
        user_message = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_uuid,
            ChatMessage.message_type == MessageType.USER,
            ChatMessage.created_at < target_message.created_at
        ).order_by(desc(ChatMessage.created_at)).first()
        
        messages = []
        if user_message:
            messages.append(user_message)
        messages.append(target_message)
        
        print(f"Found focused context: {len(messages)} messages")
        
    else:
        # Full conversation view (original behavior)
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_uuid
        ).order_by(ChatMessage.created_at).all()
        
        print(f"Found full conversation: {len(messages)} messages")
    
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")
    
    # Build response
    conversation_messages = []
    for message in messages:
        # Determine role based on message type
        role = "user" if message.message_type == MessageType.USER else "assistant"
        
        # Mark the target message as problematic if this is a focused view
        is_problematic = (target_message_uuid is not None and 
                         str(message.id) == str(target_message_uuid))
        
        conversation_messages.append(ConversationMessageResponse(
            id=str(message.id),
            content=message.content,
            role=role,
            timestamp=message.created_at,
            intent=message.intent,
            rating=message.rating,
            processing_time_ms=message.processing_time_ms,
            is_problematic=is_problematic
        ))
    
    print(f"Returning {len(conversation_messages)} formatted messages")
    return conversation_messages

def _get_user_message_before(db: Session, chat_message: ChatMessage) -> Optional[str]:
    """Get the user message that preceded this assistant message"""
    if not chat_message:
        return None
        
    try:
        # Find the user message that came before this assistant message
        user_message = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == chat_message.conversation_id,
            ChatMessage.message_type == MessageType.USER,
            ChatMessage.created_at < chat_message.created_at
        ).order_by(desc(ChatMessage.created_at)).first()
        
        return user_message.content if user_message else None
        
    except Exception as e:
        print(f"Error getting user message before: {e}")
        return None


# Add this diagnostic version to find what we're missing

@router.get("/queue-diagnostic", response_model=List[ProblematicMessage])
def get_tester_queue_diagnostic(
    priority: Optional[int] = Query(None, ge=1, le=3),
    issue_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    days_back: int = Query(7, ge=1, le=30),
    school_id: Optional[str] = Query(None),
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """DIAGNOSTIC: Find why problematic messages are missing."""
    
    print(f"\n=== DIAGNOSTIC TESTER QUEUE ===")
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    
    # Build base query
    base_query = db.query(ChatMessage).filter(
        ChatMessage.message_type == MessageType.ASSISTANT,
        ChatMessage.created_at >= date_threshold
    )
    
    if school_id:
        try:
            school_uuid = UUID(school_id)
            base_query = base_query.filter(ChatMessage.school_id == school_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school ID format")
    
    total_messages = base_query.count()
    print(f"Total assistant messages: {total_messages}")
    
    # DIAGNOSTIC: Check EVERY possible issue type with relaxed criteria
    all_issues = []
    
    # 1. ANY messages with ratings (not just -1)
    print(f"\n1. RATING ANALYSIS:")
    rated_messages = base_query.filter(ChatMessage.rating.isnot(None)).all()
    print(f"   Messages with ANY rating: {len(rated_messages)}")
    
    rating_breakdown = {}
    for msg in rated_messages:
        rating_breakdown[msg.rating] = rating_breakdown.get(msg.rating, 0) + 1
    print(f"   Rating breakdown: {rating_breakdown}")
    
    # Add ALL rated messages as potential issues
    for msg in rated_messages:
        issue_type = "negative_rating" if msg.rating == -1 else f"rating_{msg.rating}"
        priority = 1 if msg.rating == -1 else 2
        all_issues.append(_build_comprehensive_problematic_message(
            db, msg, issue_type, priority
        ))
    
    # 2. ANY messages with specific intents (broader search)
    print(f"\n2. INTENT ANALYSIS:")
    problematic_intents = [
        'unhandled', 'unknown', 'ollama_fallback', 'fallback', 
        'error', 'file_processing_error', 'general'  # Add 'general' as potentially problematic
    ]
    
    intent_breakdown = {}
    for intent in problematic_intents:
        count = base_query.filter(ChatMessage.intent == intent).count()
        intent_breakdown[intent] = count
        if count > 0:
            messages = base_query.filter(ChatMessage.intent == intent).all()
            for msg in messages:
                all_issues.append(_build_comprehensive_problematic_message(
                    db, msg, f"intent_{intent}", 2
                ))
    
    print(f"   Intent breakdown: {intent_breakdown}")
    
    # Also check what intents actually exist
    all_intents = db.query(ChatMessage.intent).filter(
        ChatMessage.intent.isnot(None),
        ChatMessage.created_at >= date_threshold
    ).distinct().all()
    print(f"   All intents in timeframe: {[i[0] for i in all_intents]}")
    
    # 3. Check for slow messages (lower threshold)
    print(f"\n3. PERFORMANCE ANALYSIS:")
    very_slow = base_query.filter(ChatMessage.processing_time_ms > 5000).count()  # 5s instead of 10s
    slow = base_query.filter(ChatMessage.processing_time_ms > 2000).count()       # 2s
    print(f"   Messages >5s: {very_slow}")
    print(f"   Messages >2s: {slow}")
    
    if very_slow > 0:
        slow_messages = base_query.filter(ChatMessage.processing_time_ms > 5000).all()
        for msg in slow_messages:
            all_issues.append(_build_comprehensive_problematic_message(
                db, msg, "slow_response", 2
            ))
    
    # 4. Check response_data for ANY indicators
    print(f"\n4. RESPONSE DATA ANALYSIS:")
    messages_with_response_data = base_query.filter(ChatMessage.response_data.isnot(None)).all()
    print(f"   Messages with response_data: {len(messages_with_response_data)}")
    
    response_data_patterns = {}
    for msg in messages_with_response_data:
        if msg.response_data:
            for key in msg.response_data.keys():
                response_data_patterns[key] = response_data_patterns.get(key, 0) + 1
    print(f"   Response data keys: {response_data_patterns}")
    
    # Look for any fallback indicators
    for msg in messages_with_response_data:
        if msg.response_data and msg.response_data.get('fallback'):
            all_issues.append(_build_comprehensive_problematic_message(
                db, msg, "response_data_fallback", 1
            ))
    
    # 5. Routing logs analysis
    print(f"\n5. ROUTING LOGS ANALYSIS:")
    routing_logs = db.query(RoutingLog).filter(
        RoutingLog.created_at >= date_threshold
    ).all()
    print(f"   Total routing logs: {len(routing_logs)}")
    
    if routing_logs:
        confidence_breakdown = {"high": 0, "medium": 0, "low": 0, "null": 0}
        fallback_count = 0
        
        for log in routing_logs:
            if log.fallback_used:
                fallback_count += 1
            
            if log.llm_confidence is None:
                confidence_breakdown["null"] += 1
            elif log.llm_confidence >= 0.8:
                confidence_breakdown["high"] += 1
            elif log.llm_confidence >= 0.6:
                confidence_breakdown["medium"] += 1
            else:
                confidence_breakdown["low"] += 1
        
        print(f"   Confidence breakdown: {confidence_breakdown}")
        print(f"   Fallback used count: {fallback_count}")
        
        # Add routing issues
        for log in routing_logs:
            if (log.fallback_used or 
                (log.llm_confidence and log.llm_confidence < 0.7) or  # Relaxed threshold
                log.final_intent in ["unhandled", "unknown", "ollama_fallback"]):
                
                chat_msg = _find_message_for_routing_log(db, log)
                if chat_msg:
                    all_issues.append(_build_comprehensive_problematic_message(
                        db, chat_msg, "routing_issue", 2, log
                    ))
                else:
                    all_issues.append(_build_orphaned_routing_log_entry(log))
    
    # 6. Look for recent messages that might be problematic based on content
    print(f"\n6. CONTENT ANALYSIS:")
    recent_messages = base_query.order_by(desc(ChatMessage.created_at)).limit(20).all()
    
    suspicious_patterns = ['sorry', 'error', 'unable', 'cannot', "can't", 'fail', 'problem']
    content_issues = 0
    
    for msg in recent_messages:
        content_lower = msg.content.lower()
        if any(pattern in content_lower for pattern in suspicious_patterns):
            content_issues += 1
            all_issues.append(_build_comprehensive_problematic_message(
                db, msg, "suspicious_content", 3
            ))
    
    print(f"   Messages with suspicious content: {content_issues}")
    
    # Remove duplicates based on message_id
    seen_message_ids = set()
    unique_issues = []
    
    for issue in all_issues:
        if issue.message_id not in seen_message_ids:
            unique_issues.append(issue)
            seen_message_ids.add(issue.message_id)
    
    print(f"\n=== DIAGNOSTIC RESULTS ===")
    print(f"Total issues found (with duplicates): {len(all_issues)}")
    print(f"Unique issues: {len(unique_issues)}")
    
    # Show breakdown
    issue_type_breakdown = {}
    for issue in unique_issues:
        issue_type_breakdown[issue.issue_type] = issue_type_breakdown.get(issue.issue_type, 0) + 1
    
    print(f"Issue breakdown: {issue_type_breakdown}")
    
    # Apply filters
    filtered_issues = []
    for issue in unique_issues:
        if _apply_filters(issue, priority, issue_type):
            filtered_issues.append(issue)
    
    print(f"After applying filters: {len(filtered_issues)}")
    
    # Sort and return
    filtered_issues.sort(key=lambda x: (x.priority, -x.created_at.timestamp()))
    
    return filtered_issues[:limit]



# Add these basic diagnostic endpoints to your tester router

@router.get("/debug/messages", response_model=dict)
def debug_all_messages(
    limit: int = Query(50, ge=1, le=200),
    days_back: int = Query(30, ge=1, le=90),
    include_user_messages: bool = Query(True),
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Debug: Get all messages across all schools with detailed info."""
    
    print(f"\n=== DEBUG: FETCHING ALL MESSAGES ===")
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    
    # Build base query - ALL message types, ALL schools
    base_query = db.query(ChatMessage).filter(
        ChatMessage.created_at >= date_threshold
    ).order_by(desc(ChatMessage.created_at))
    
    if not include_user_messages:
        base_query = base_query.filter(ChatMessage.message_type == MessageType.ASSISTANT)
    
    messages = base_query.limit(limit).all()
    
    print(f"Found {len(messages)} messages in last {days_back} days")
    
    # Analyze the data
    analysis = {
        "total_found": len(messages),
        "date_range": f"Last {days_back} days",
        "breakdown": {
            "by_type": {},
            "by_school": {},
            "by_intent": {},
            "by_rating": {},
            "with_processing_time": 0,
            "with_response_data": 0
        },
        "sample_messages": []
    }
    
    for msg in messages:
        # Type breakdown
        msg_type = msg.message_type.value if msg.message_type else "unknown"
        analysis["breakdown"]["by_type"][msg_type] = analysis["breakdown"]["by_type"].get(msg_type, 0) + 1
        
        # School breakdown
        school = str(msg.school_id) if msg.school_id else "no_school"
        analysis["breakdown"]["by_school"][school] = analysis["breakdown"]["by_school"].get(school, 0) + 1
        
        # Intent breakdown (assistant messages only)
        if msg.message_type == MessageType.ASSISTANT and msg.intent:
            analysis["breakdown"]["by_intent"][msg.intent] = analysis["breakdown"]["by_intent"].get(msg.intent, 0) + 1
        
        # Rating breakdown
        if msg.rating is not None:
            analysis["breakdown"]["by_rating"][str(msg.rating)] = analysis["breakdown"]["by_rating"].get(str(msg.rating), 0) + 1
        
        # Processing time
        if msg.processing_time_ms is not None:
            analysis["breakdown"]["with_processing_time"] += 1
        
        # Response data
        if msg.response_data is not None:
            analysis["breakdown"]["with_response_data"] += 1
    
    # Sample messages for inspection
    for msg in messages[:5]:
        sample = {
            "id": str(msg.id),
            "type": msg.message_type.value if msg.message_type else None,
            "created_at": msg.created_at.isoformat(),
            "school_id": str(msg.school_id) if msg.school_id else None,
            "content_preview": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
            "intent": msg.intent,
            "rating": msg.rating,
            "processing_time_ms": msg.processing_time_ms,
            "has_response_data": msg.response_data is not None,
            "response_data_keys": list(msg.response_data.keys()) if msg.response_data else []
        }
        analysis["sample_messages"].append(sample)
    
    print(f"Analysis complete:")
    print(f"- Message types: {analysis['breakdown']['by_type']}")
    print(f"- Schools: {len(analysis['breakdown']['by_school'])} different schools")
    print(f"- Intents: {len(analysis['breakdown']['by_intent'])} different intents")
    print(f"- Ratings: {analysis['breakdown']['by_rating']}")
    
    return analysis

@router.get("/debug/conversations", response_model=dict)
def debug_all_conversations(
    limit: int = Query(20, ge=1, le=100),
    days_back: int = Query(30, ge=1, le=90),
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Debug: Get all conversations across all schools with message counts."""
    
    print(f"\n=== DEBUG: FETCHING ALL CONVERSATIONS ===")
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    
    # Get unique conversation IDs with message counts
    conversation_stats = db.query(
        ChatMessage.conversation_id,
        ChatMessage.school_id,
        ChatMessage.user_id,
        func.count(ChatMessage.id).label('message_count'),
        func.min(ChatMessage.created_at).label('first_message'),
        func.max(ChatMessage.created_at).label('last_message'),
        func.array_agg(ChatMessage.intent.distinct()).label('intents_used')
    ).filter(
        ChatMessage.created_at >= date_threshold
    ).group_by(
        ChatMessage.conversation_id,
        ChatMessage.school_id,
        ChatMessage.user_id
    ).order_by(desc(func.max(ChatMessage.created_at))).limit(limit).all()
    
    print(f"Found {len(conversation_stats)} conversations")
    
    analysis = {
        "total_conversations": len(conversation_stats),
        "date_range": f"Last {days_back} days",
        "breakdown": {
            "by_school": {},
            "by_message_count": {"1-5": 0, "6-10": 0, "11-20": 0, "20+": 0},
            "by_duration": {"< 1 hour": 0, "1-24 hours": 0, "1+ days": 0}
        },
        "sample_conversations": []
    }
    
    for conv in conversation_stats:
        # School breakdown
        school = str(conv.school_id) if conv.school_id else "no_school"
        analysis["breakdown"]["by_school"][school] = analysis["breakdown"]["by_school"].get(school, 0) + 1
        
        # Message count breakdown
        if conv.message_count <= 5:
            analysis["breakdown"]["by_message_count"]["1-5"] += 1
        elif conv.message_count <= 10:
            analysis["breakdown"]["by_message_count"]["6-10"] += 1
        elif conv.message_count <= 20:
            analysis["breakdown"]["by_message_count"]["11-20"] += 1
        else:
            analysis["breakdown"]["by_message_count"]["20+"] += 1
        
        # Duration breakdown
        duration = conv.last_message - conv.first_message
        if duration.total_seconds() < 3600:  # < 1 hour
            analysis["breakdown"]["by_duration"]["< 1 hour"] += 1
        elif duration.total_seconds() < 86400:  # < 24 hours
            analysis["breakdown"]["by_duration"]["1-24 hours"] += 1
        else:
            analysis["breakdown"]["by_duration"]["1+ days"] += 1
    
    # Sample conversations
    for conv in conversation_stats[:10]:
        sample = {
            "conversation_id": str(conv.conversation_id),
            "school_id": str(conv.school_id) if conv.school_id else None,
            "user_id": str(conv.user_id),
            "message_count": conv.message_count,
            "first_message": conv.first_message.isoformat(),
            "last_message": conv.last_message.isoformat(),
            "duration_hours": round((conv.last_message - conv.first_message).total_seconds() / 3600, 2),
            "intents_used": [intent for intent in conv.intents_used if intent] if conv.intents_used else []
        }
        analysis["sample_conversations"].append(sample)
    
    print(f"Conversation analysis:")
    print(f"- Schools: {len(analysis['breakdown']['by_school'])} different schools")
    print(f"- Message counts: {analysis['breakdown']['by_message_count']}")
    print(f"- Durations: {analysis['breakdown']['by_duration']}")
    
    return analysis

@router.get("/debug/routing-logs", response_model=dict)
def debug_routing_logs(
    limit: int = Query(50, ge=1, le=200),
    days_back: int = Query(30, ge=1, le=90),
    ctx = Depends(require_tester),
    db: Session = Depends(get_db)
):
    """Debug: Get all routing logs with analysis."""
    
    print(f"\n=== DEBUG: FETCHING ALL ROUTING LOGS ===")
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    
    routing_logs = db.query(RoutingLog).filter(
        RoutingLog.created_at >= date_threshold
    ).order_by(desc(RoutingLog.created_at)).limit(limit).all()
    
    print(f"Found {len(routing_logs)} routing logs")
    
    analysis = {
        "total_found": len(routing_logs),
        "date_range": f"Last {days_back} days",
        "breakdown": {
            "by_school": {},
            "by_final_intent": {},
            "by_confidence": {"high": 0, "medium": 0, "low": 0, "null": 0},
            "fallback_used": 0,
            "with_llm_intent": 0,
            "with_router_intent": 0
        },
        "sample_logs": []
    }
    
    for log in routing_logs:
        # School breakdown
        school = log.school_id or "no_school"
        analysis["breakdown"]["by_school"][school] = analysis["breakdown"]["by_school"].get(school, 0) + 1
        
        # Final intent breakdown
        if log.final_intent:
            analysis["breakdown"]["by_final_intent"][log.final_intent] = analysis["breakdown"]["by_final_intent"].get(log.final_intent, 0) + 1
        
        # Confidence breakdown
        if log.llm_confidence is None:
            analysis["breakdown"]["by_confidence"]["null"] += 1
        elif log.llm_confidence >= 0.8:
            analysis["breakdown"]["by_confidence"]["high"] += 1
        elif log.llm_confidence >= 0.6:
            analysis["breakdown"]["by_confidence"]["medium"] += 1
        else:
            analysis["breakdown"]["by_confidence"]["low"] += 1
        
        # Other flags
        if log.fallback_used:
            analysis["breakdown"]["fallback_used"] += 1
        if log.llm_intent:
            analysis["breakdown"]["with_llm_intent"] += 1
        if log.router_intent:
            analysis["breakdown"]["with_router_intent"] += 1
    
    # Sample logs
    for log in routing_logs[:5]:
        sample = {
            "id": log.id,
            "created_at": log.created_at.isoformat(),
            "school_id": log.school_id,
            "user_id": log.user_id,
            "message_preview": log.message[:100] + "..." if log.message and len(log.message) > 100 else log.message,
            "llm_intent": log.llm_intent,
            "router_intent": log.router_intent,
            "final_intent": log.final_intent,
            "llm_confidence": log.llm_confidence,
            "fallback_used": log.fallback_used,
            "latency_ms": log.latency_ms
        }
        analysis["sample_logs"].append(sample)
    
    print(f"Routing log analysis:")
    print(f"- Schools: {len(analysis['breakdown']['by_school'])} different schools")
    print(f"- Final intents: {len(analysis['breakdown']['by_final_intent'])} different intents")
    print(f"- Confidence: {analysis['breakdown']['by_confidence']}")
    print(f"- Fallback used: {analysis['breakdown']['fallback_used']}")
    
    return analysis