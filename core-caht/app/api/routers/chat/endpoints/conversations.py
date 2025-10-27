# app/api/routers/chat/endpoints/conversations.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ConversationList, ConversationResponse, ConversationDetail,
    MessageResponse, UpdateConversation
)
from ..deps import verify_auth_and_get_context

router = APIRouter()

@router.get("/conversations", response_model=ConversationList)
def get_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    include_archived: bool = Query(False),
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    try:
        chat = ChatService(db)
        conversations, total = chat.get_user_conversations(ctx["user_id"], ctx["school_id"], page, limit, include_archived)
        return ConversationList(
            conversations=[ConversationResponse.from_attributes(c) for c in conversations],
            total=total, page=page, limit=limit, has_next=(page * limit) < total
        )
    except Exception as e:
        print(f"Get conversations error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation_detail(
    conversation_id: str,
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    try:
        chat = ChatService(db)
        conv = chat.get_conversation(conversation_id, ctx["user_id"], ctx["school_id"])
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = chat.get_conversation_messages(conversation_id, ctx["user_id"], ctx["school_id"])
        detail = ConversationDetail.from_attributes(conv)
        detail.messages = [MessageResponse.from_attributes(m) for m in messages]
        return detail
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get conversation detail error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    update_data: UpdateConversation,
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    try:
        chat = ChatService(db)
        conv = chat.update_conversation(conversation_id, ctx["user_id"], ctx["school_id"],
                                        title=update_data.title, is_archived=update_data.is_archived)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        db.commit()
        return ConversationResponse.from_attributes(conv)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Update conversation error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update conversation: {str(e)}")

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    try:
        chat = ChatService(db)
        ok = chat.delete_conversation(conversation_id, ctx["user_id"], ctx["school_id"])
        if not ok:
            raise HTTPException(status_code=404, detail="Conversation not found")
        db.commit()
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Delete conversation error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@router.get("/conversations/recent", response_model=list[ConversationResponse])
def get_recent_conversations(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    try:
        chat = ChatService(db)
        convs = chat.get_recent_conversations(ctx["user_id"], ctx["school_id"], days, limit)
        return [ConversationResponse.from_attributes(c) for c in convs]
    except Exception as e:
        print(f"Get recent conversations error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get recent conversations: {str(e)}")

@router.get("/conversations/search", response_model=list[ConversationResponse])
def search_conversations(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    try:
        chat = ChatService(db)
        convs = chat.search_conversations(ctx["user_id"], ctx["school_id"], q, limit)
        return [ConversationResponse.from_attributes(c) for c in convs]
    except Exception as e:
        print(f"Search conversations error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to search conversations: {str(e)}")