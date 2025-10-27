# app/api/routers/chat/endpoints/feedback.py - Fixed paths
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List
import uuid

from app.core.db import get_db
from app.models.chat import ChatMessage, MessageType
from app.schemas.chat import MessageResponse
from ..deps import verify_auth_and_get_context

router = APIRouter()

class RateMessageRequest(BaseModel):
    rating: int  # -1 (thumbs down) or +1 (thumbs up)

class MessageRatingResponse(BaseModel):
    message_id: str
    rating: int
    rated_at: datetime
    message: str

class FeedbackStatsResponse(BaseModel):
    total_rated: int
    thumbs_up: int
    thumbs_down: int
    unrated: int

# FIXED: Remove the /chat prefix since it's already added in __init__.py
@router.post("/messages/{message_id}/rate", response_model=MessageRatingResponse)
def rate_message(
    message_id: str,
    request: RateMessageRequest,
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db)
):
    """Rate an assistant message with thumbs up (+1) or thumbs down (-1)."""
    
    print(f"=== RATING MESSAGE DEBUG ===")
    print(f"Raw Message ID: {message_id}")
    print(f"Message ID type: {type(message_id)}")
    print(f"Rating: {request.rating}")
    print(f"User ID: {ctx['user_id']}")
    print(f"User ID type: {type(ctx['user_id'])}")
    print(f"School ID: {ctx['school_id']}")
    print(f"School ID type: {type(ctx['school_id'])}")
    
    if request.rating not in [-1, 1]:
        raise HTTPException(status_code=400, detail="Rating must be -1 (thumbs down) or +1 (thumbs up)")
    
    # Convert message_id to UUID if it's a string
    try:
        if isinstance(message_id, str):
            message_uuid = uuid.UUID(message_id)
            print(f"Converted message ID to UUID: {message_uuid}")
        else:
            message_uuid = message_id
    except ValueError as e:
        print(f"Invalid UUID format: {message_id}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    # Debug: First, let's see ALL messages for this user to understand the data
    print(f"\n=== DEBUGGING USER MESSAGES ===")
    all_user_messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == ctx["user_id"],
        ChatMessage.school_id == ctx["school_id"]
    ).all()
    print(f"Total messages for user: {len(all_user_messages)}")
    
    assistant_messages = [msg for msg in all_user_messages if msg.message_type == MessageType.ASSISTANT]
    print(f"Assistant messages for user: {len(assistant_messages)}")
    
    for i, msg in enumerate(assistant_messages[-5:]):  # Show last 5 assistant messages
        print(f"  Message {i+1}: ID={msg.id}, Type={msg.message_type}, Content='{msg.content[:50]}...'")
        if str(msg.id) == message_id:
            print(f"    ✓ FOUND MATCH for message_id: {message_id}")
    
    # Now try the actual query
    print(f"\n=== ACTUAL QUERY ===")
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_uuid,
        ChatMessage.user_id == ctx["user_id"],
        ChatMessage.school_id == ctx["school_id"]
    ).first()
    
    print(f"Query result: {message}")
    
    if not message:
        print(f"Message not found with exact query. Let's try without user/school filters...")
        
        # Try finding the message without user/school constraints
        any_message = db.query(ChatMessage).filter(ChatMessage.id == message_uuid).first()
        if any_message:
            print(f"Message exists but belongs to different user/school:")
            print(f"  Message user_id: {any_message.user_id} (ctx user_id: {ctx['user_id']})")
            print(f"  Message school_id: {any_message.school_id} (ctx school_id: {ctx['school_id']})")
            print(f"  User match: {any_message.user_id == ctx['user_id']}")
            print(f"  School match: {any_message.school_id == ctx['school_id']}")
        else:
            print(f"Message {message_uuid} does not exist in database at all")
        
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.message_type != MessageType.ASSISTANT:
        print(f"Message is not assistant type: {message.message_type}")
        raise HTTPException(status_code=400, detail="Only assistant messages can be rated")
    
    # Update the rating
    old_rating = message.rating
    message.rating = request.rating
    message.rated_at = datetime.utcnow()
    
    try:
        db.commit()
        print(f"Successfully rated message {message_id}: {old_rating} -> {request.rating}")
        return MessageRatingResponse(
            message_id=str(message.id),
            rating=message.rating,
            rated_at=message.rated_at,
            message=message.content[:100] + "..." if len(message.content) > 100 else message.content
        )
    except Exception as e:
        db.rollback()
        print(f"Failed to save rating: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save rating: {str(e)}")

# FIXED: Remove the /chat prefix
@router.get("/messages/{message_id}/rating")
def get_message_rating(
    message_id: str,
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db)
):
    """Get the current rating for a message."""
    
    try:
        message_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")
    
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_uuid,
        ChatMessage.user_id == ctx["user_id"],
        ChatMessage.school_id == ctx["school_id"]
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {
        "message_id": str(message.id),
        "rating": message.rating,
        "rated_at": message.rated_at
    }

# FIXED: Remove the /chat prefix
@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
def get_feedback_stats(
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db)
):
    """Get feedback statistics for the current user's messages."""
    
    base_query = db.query(ChatMessage).filter(
        ChatMessage.user_id == ctx["user_id"],
        ChatMessage.school_id == ctx["school_id"],
        ChatMessage.message_type == MessageType.ASSISTANT
    )
    
    total_rated = base_query.filter(ChatMessage.rating.isnot(None)).count()
    thumbs_up = base_query.filter(ChatMessage.rating == 1).count()
    thumbs_down = base_query.filter(ChatMessage.rating == -1).count()
    unrated = base_query.filter(ChatMessage.rating.is_(None)).count()
    
    return FeedbackStatsResponse(
        total_rated=total_rated,
        thumbs_up=thumbs_up,
        thumbs_down=thumbs_down,
        unrated=unrated
    )

# FIXED: Remove the /chat prefix
@router.get("/feedback/negative", response_model=List[MessageResponse])
def get_negative_feedback_messages(
    limit: int = 20,
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db)
):
    """Get assistant messages that received thumbs down ratings."""
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == ctx["user_id"],
        ChatMessage.school_id == ctx["school_id"],
        ChatMessage.message_type == MessageType.ASSISTANT,
        ChatMessage.rating == -1
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
    
    return [MessageResponse.from_attributes(msg) for msg in messages]