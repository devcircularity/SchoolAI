# app/api/routers/admin/chat_monitoring.py - New admin chat monitoring endpoints
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel

from app.core.db import get_db
from app.models.chat import ChatMessage, MessageType, ChatConversation
from app.models.user import User
from app.models.school import School
from app.api.deps.auth import require_admin

router = APIRouter(prefix="/admin/chat", tags=["Admin - Chat Monitoring"])

# Pydantic schemas for monitoring
class ChatMessageResponse(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    school_id: Optional[str]
    school_name: Optional[str] = None  # Add school name
    content: str
    message_type: str  # "user" or "assistant"
    intent: Optional[str]
    rating: Optional[int]
    rated_at: Optional[datetime]
    processing_time_ms: Optional[int]
    created_at: datetime

class ConversationSummaryResponse(BaseModel):
    conversation_id: str
    user_id: str
    school_id: Optional[str]
    message_count: int
    last_message_at: datetime
    has_negative_rating: bool
    unresolved_issues: int

class RealtimeStatsResponse(BaseModel):
    active_conversations: int
    messages_today: int
    average_response_time: int
    satisfaction_rate: float
    fallback_rate: float
    top_intents_today: List[Dict[str, Any]]

class ConversationDetailsResponse(BaseModel):
    conversation_id: str
    messages: List[ChatMessageResponse]
    user_info: Dict[str, Any]
    school_info: Optional[Dict[str, Any]]
    routing_logs: List[Dict[str, Any]] = []

@router.get("/messages", response_model=List[ChatMessageResponse])
def get_recent_messages(
    limit: int = Query(50, ge=1, le=200, description="Number of messages to return"),
    school_id: Optional[str] = Query(None, description="Filter by school ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    has_rating: bool = Query(False, description="Only messages with ratings"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    hours_back: int = Query(168, ge=1, le=8760, description="Hours to look back (default: 1 week)"),  # Increased max to 1 year
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get recent chat messages across all conversations"""
    
    print(f"\n=== ADMIN CHAT MONITORING: GET MESSAGES ===")
    print(f"Admin: {ctx['user'].full_name}")
    print(f"Filters: limit={limit}, school_id={school_id}, hours_back={hours_back}")
    
    # Calculate date threshold
    date_threshold = datetime.utcnow() - timedelta(hours=hours_back)
    print(f"Looking for messages after: {date_threshold}")
    
    # First, let's check total messages in database for debugging
    total_messages_in_db = db.query(ChatMessage).count()
    total_recent_messages = db.query(ChatMessage).filter(
        ChatMessage.created_at >= date_threshold
    ).count()
    print(f"Total messages in database: {total_messages_in_db}")
    print(f"Messages in time range: {total_recent_messages}")
    
    # Build base query - NO SCHOOL FILTERING BY DEFAULT (admin sees all)
    query = db.query(ChatMessage).filter(
        ChatMessage.created_at >= date_threshold
    )
    
    print(f"Base query count: {query.count()}")
    
    # Apply filters
    if school_id:
        try:
            school_uuid = UUID(school_id)
            query = query.filter(ChatMessage.school_id == school_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school ID format")
    
    if user_id:
        try:
            user_uuid = UUID(user_id)
            query = query.filter(ChatMessage.user_id == user_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    if has_rating:
        query = query.filter(ChatMessage.rating.isnot(None))
    
    if message_type:
        if message_type not in ["user", "assistant"]:
            raise HTTPException(status_code=400, detail="Message type must be 'user' or 'assistant'")
        msg_type = MessageType.USER if message_type == "user" else MessageType.ASSISTANT
        query = query.filter(ChatMessage.message_type == msg_type)
    
    # Order by most recent first and apply limit
    messages = query.order_by(desc(ChatMessage.created_at)).limit(limit).all()
    
    print(f"Found {len(messages)} messages")
    
    # Get school names for messages that have school_id
    school_ids = [str(msg.school_id) for msg in messages if msg.school_id]
    school_names = {}
    
    if school_ids:
        from app.models.school import School
        schools = db.query(School).filter(School.id.in_(school_ids)).all()
        school_names = {str(school.id): school.name for school in schools}
        print(f"Found {len(school_names)} school names")
    
    # Convert to response format
    result = []
    for msg in messages:
        school_name = None
        if msg.school_id and str(msg.school_id) in school_names:
            school_name = school_names[str(msg.school_id)]
        
        result.append(ChatMessageResponse(
            id=str(msg.id),
            conversation_id=str(msg.conversation_id),
            user_id=str(msg.user_id),
            school_id=str(msg.school_id) if msg.school_id else None,
            school_name=school_name,
            content=msg.content,
            message_type=msg.message_type.value if msg.message_type else "unknown",
            intent=msg.intent,
            rating=msg.rating,
            rated_at=msg.rated_at,
            processing_time_ms=msg.processing_time_ms,
            created_at=msg.created_at
        ))
    
    print(f"Returning {len(result)} formatted messages")
    return result

@router.get("/conversations", response_model=List[ConversationSummaryResponse])
def get_active_conversations(
    school_id: Optional[str] = Query(None, description="Filter by school ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to return"),
    problems_only: bool = Query(False, description="Only conversations with issues"),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get active conversations with summary information"""
    
    print(f"\n=== ADMIN CHAT MONITORING: GET CONVERSATIONS ===")
    
    # Get conversation summaries using aggregation
    query = db.query(
        ChatMessage.conversation_id,
        ChatMessage.user_id,
        ChatMessage.school_id,
        func.count(ChatMessage.id).label('message_count'),
        func.max(ChatMessage.created_at).label('last_message_at'),
        func.bool_or(ChatMessage.rating == -1).label('has_negative_rating')
    ).group_by(
        ChatMessage.conversation_id,
        ChatMessage.user_id,
        ChatMessage.school_id
    )
    
    # Apply school filter
    if school_id:
        try:
            school_uuid = UUID(school_id)
            query = query.filter(ChatMessage.school_id == school_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school ID format")
    
    # Filter for problems if requested
    if problems_only:
        # Only conversations with negative ratings or other issues
        query = query.having(func.bool_or(ChatMessage.rating == -1) == True)
    
    # Order by most recent activity and apply limit
    conversations = query.order_by(desc(func.max(ChatMessage.created_at))).limit(limit).all()
    
    print(f"Found {len(conversations)} conversations")
    
    # Convert to response format
    result = []
    for conv in conversations:
        # For now, set unresolved_issues to 0 - you can enhance this later
        unresolved_issues = 1 if conv.has_negative_rating else 0
        
        result.append(ConversationSummaryResponse(
            conversation_id=str(conv.conversation_id),
            user_id=str(conv.user_id),
            school_id=str(conv.school_id) if conv.school_id else None,
            message_count=conv.message_count,
            last_message_at=conv.last_message_at,
            has_negative_rating=conv.has_negative_rating or False,
            unresolved_issues=unresolved_issues
        ))
    
    return result

@router.get("/stats/realtime", response_model=RealtimeStatsResponse)
def get_realtime_stats(
    school_id: Optional[str] = Query(None, description="Filter by school ID"),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get real-time dashboard statistics"""
    
    print(f"\n=== ADMIN CHAT MONITORING: GET REALTIME STATS ===")
    
    # Calculate time thresholds
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_hour = now - timedelta(hours=1)
    
    # Base query for today's messages
    base_query = db.query(ChatMessage)
    if school_id:
        try:
            school_uuid = UUID(school_id)
            base_query = base_query.filter(ChatMessage.school_id == school_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school ID format")
    
    # Active conversations (conversations with messages in last hour)
    active_conversations = base_query.filter(
        ChatMessage.created_at >= last_hour
    ).distinct(ChatMessage.conversation_id).count()
    
    # Messages today
    messages_today = base_query.filter(
        ChatMessage.created_at >= today_start
    ).count()
    
    # Average response time for assistant messages today with processing time
    avg_response_time_result = base_query.filter(
        ChatMessage.created_at >= today_start,
        ChatMessage.message_type == MessageType.ASSISTANT,
        ChatMessage.processing_time_ms.isnot(None)
    ).with_entities(func.avg(ChatMessage.processing_time_ms)).scalar()
    
    average_response_time = int(avg_response_time_result) if avg_response_time_result else 0
    
    # Satisfaction rate (positive ratings / total ratings today)
    total_ratings = base_query.filter(
        ChatMessage.created_at >= today_start,
        ChatMessage.rating.isnot(None)
    ).count()
    
    positive_ratings = base_query.filter(
        ChatMessage.created_at >= today_start,
        ChatMessage.rating == 1
    ).count()
    
    satisfaction_rate = (positive_ratings / total_ratings) if total_ratings > 0 else 0.0
    
    # Fallback rate (messages with fallback intent / total assistant messages today)
    total_assistant_messages = base_query.filter(
        ChatMessage.created_at >= today_start,
        ChatMessage.message_type == MessageType.ASSISTANT
    ).count()
    
    fallback_messages = base_query.filter(
        ChatMessage.created_at >= today_start,
        ChatMessage.message_type == MessageType.ASSISTANT,
        or_(
            ChatMessage.intent == 'ollama_fallback',
            ChatMessage.intent == 'unhandled',
            ChatMessage.intent == 'unknown'
        )
    ).count()
    
    fallback_rate = (fallback_messages / total_assistant_messages) if total_assistant_messages > 0 else 0.0
    
    # Top intents today
    top_intents_result = base_query.filter(
        ChatMessage.created_at >= today_start,
        ChatMessage.message_type == MessageType.ASSISTANT,
        ChatMessage.intent.isnot(None)
    ).with_entities(
        ChatMessage.intent,
        func.count(ChatMessage.intent).label('count')
    ).group_by(ChatMessage.intent).order_by(desc('count')).limit(5).all()
    
    top_intents_today = [
        {"intent": intent, "count": count}
        for intent, count in top_intents_result
    ]
    
    stats = RealtimeStatsResponse(
        active_conversations=active_conversations,
        messages_today=messages_today,
        average_response_time=average_response_time,
        satisfaction_rate=satisfaction_rate,
        fallback_rate=fallback_rate,
        top_intents_today=top_intents_today
    )
    
    print(f"Stats: {stats.dict()}")
    return stats

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailsResponse)
def get_conversation_details(
    conversation_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed conversation information with full message history"""
    
    try:
        conversation_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    
    print(f"\n=== ADMIN CHAT MONITORING: GET CONVERSATION DETAILS ===")
    print(f"Conversation ID: {conversation_id}")
    
    # Get all messages in the conversation
    messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_uuid
    ).order_by(ChatMessage.created_at).all()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get user info from first message
    first_message = messages[0]
    user = db.query(User).filter(User.id == first_message.user_id).first()
    
    user_info = {
        "id": str(user.id) if user else str(first_message.user_id),
        "full_name": user.full_name if user else "Unknown User",
        "email": user.email if user else "unknown@example.com"
    }
    
    # Get conversation info if available
    conversation_info = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_uuid
    ).first()
    
    conversation_title = None
    if conversation_info:
        conversation_title = conversation_info.title
    elif messages:
        # Fallback: use truncated first message as title
        conversation_title = messages[0].content[:50] + "..." if len(messages[0].content) > 50 else messages[0].content
    
    # Get school info if available
    school_info = None
    if first_message.school_id:
        school = db.query(School).filter(School.id == first_message.school_id).first()
        if school:
            school_info = {
                "id": str(school.id),
                "name": school.name,
                "location": getattr(school, 'location', None)
            }
    
    # Convert messages to response format with school names
    school_ids = [str(msg.school_id) for msg in messages if msg.school_id]
    school_names = {}
    
    print(f"School IDs found in conversation: {school_ids}")
    
    if school_ids:
        schools = db.query(School).filter(School.id.in_(school_ids)).all()
        school_names = {str(school.id): school.name for school in schools}
        print(f"School names mapping: {school_names}")
    
    message_responses = []
    for msg in messages:
        school_name = None
        if msg.school_id and str(msg.school_id) in school_names:
            school_name = school_names[str(msg.school_id)]
            print(f"Message {msg.id}: school_id={msg.school_id}, school_name={school_name}")
            
        message_responses.append(ChatMessageResponse(
            id=str(msg.id),
            conversation_id=str(msg.conversation_id),
            user_id=str(msg.user_id),
            school_id=str(msg.school_id) if msg.school_id else None,
            school_name=school_name,
            content=msg.content,
            message_type=msg.message_type.value if msg.message_type else "unknown",
            intent=msg.intent,
            rating=msg.rating,
            rated_at=msg.rated_at,
            processing_time_ms=msg.processing_time_ms,
            created_at=msg.created_at
        ))
    
    print(f"Found {len(message_responses)} messages in conversation")
    
    return ConversationDetailsResponse(
        conversation_id=conversation_id,
        messages=message_responses,
        user_info=user_info,
        school_info=school_info,
        routing_logs=[]  # TODO: Add routing logs if needed
    )

# Add this test endpoint to debug the issue
@router.get("/debug/message-count")
def debug_message_count(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check message counts by time period"""
    
    now = datetime.utcnow()
    
    # Check various time periods
    time_periods = {
        "total": None,
        "last_1_hour": now - timedelta(hours=1),
        "last_24_hours": now - timedelta(hours=24),
        "last_week": now - timedelta(days=7),
        "last_month": now - timedelta(days=30),
        "last_year": now - timedelta(days=365)
    }
    
    results = {}
    
    for period_name, threshold in time_periods.items():
        if threshold is None:
            # Total count
            count = db.query(ChatMessage).count()
        else:
            count = db.query(ChatMessage).filter(
                ChatMessage.created_at >= threshold
            ).count()
        results[period_name] = count
    
    # Also get the date of the newest and oldest message
    newest = db.query(ChatMessage).order_by(desc(ChatMessage.created_at)).first()
    oldest = db.query(ChatMessage).order_by(ChatMessage.created_at).first()
    
    results["newest_message"] = newest.created_at.isoformat() if newest else None
    results["oldest_message"] = oldest.created_at.isoformat() if oldest else None
    results["newest_message_id"] = str(newest.id) if newest else None
    
    return results
def flag_conversation(
    conversation_id: str,
    reason: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Flag a conversation for review"""
    
    try:
        conversation_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    
    # Verify conversation exists
    message_exists = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_uuid
    ).first()
    
    if not message_exists:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # For now, just log the flag - you can implement a flags table later
    print(f"🚩 Conversation {conversation_id} flagged by {ctx['user'].full_name}: {reason}")
    
    return {"message": f"Conversation flagged for review: {reason}"}

@router.get("/analytics")
def get_chat_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    school_id: Optional[str] = Query(None, description="Filter by school ID"),
    group_by: str = Query("day", description="Group by: hour, day, week"),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get chat analytics for a time period"""
    
    # Default to last 7 days if no dates provided
    if not start_date or not end_date:
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=7)
    else:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include end date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    print(f"\n=== ADMIN CHAT MONITORING: GET ANALYTICS ===")
    print(f"Period: {start_dt} to {end_dt}")
    
    # Base query
    base_query = db.query(ChatMessage).filter(
        and_(
            ChatMessage.created_at >= start_dt,
            ChatMessage.created_at < end_dt
        )
    )
    
    if school_id:
        try:
            school_uuid = UUID(school_id)
            base_query = base_query.filter(ChatMessage.school_id == school_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school ID format")
    
    # This is a simplified analytics response - you can enhance it based on your needs
    total_messages = base_query.count()
    
    # Intent distribution
    intent_distribution = base_query.filter(
        ChatMessage.intent.isnot(None)
    ).with_entities(
        ChatMessage.intent,
        func.count(ChatMessage.intent).label('count')
    ).group_by(ChatMessage.intent).all()
    
    intent_dist_formatted = []
    for intent, count in intent_distribution:
        percentage = (count / total_messages * 100) if total_messages > 0 else 0
        intent_dist_formatted.append({
            "intent": intent,
            "count": count,
            "percentage": round(percentage, 2)
        })
    
    # Satisfaction trends (simplified)
    satisfaction_data = base_query.filter(
        ChatMessage.rating.isnot(None)
    ).with_entities(
        func.count(ChatMessage.rating).label('total'),
        func.sum(func.case([(ChatMessage.rating == 1, 1)], else_=0)).label('positive'),
        func.sum(func.case([(ChatMessage.rating == -1, 1)], else_=0)).label('negative')
    ).first()
    
    satisfaction_trends = [{
        "date": start_dt.strftime("%Y-%m-%d"),
        "positive": int(satisfaction_data.positive) if satisfaction_data.positive else 0,
        "negative": int(satisfaction_data.negative) if satisfaction_data.negative else 0,
        "total": int(satisfaction_data.total) if satisfaction_data.total else 0
    }]
    
    return {
        "message_volume": [{"date": start_dt.strftime("%Y-%m-%d"), "count": total_messages}],
        "intent_distribution": intent_dist_formatted,
        "satisfaction_trends": satisfaction_trends,
        "response_time_trends": [],  # TODO: Implement if needed
        "fallback_trends": []  # TODO: Implement if needed
    }