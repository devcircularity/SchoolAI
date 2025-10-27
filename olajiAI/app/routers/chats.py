# app/routers/chats.py - FIXED to include table data in response

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional, List
import json
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.deps.auth import get_auth_ctx, AuthContext
from app.deps.tenant import get_school_id
from app.state.memory import get_state, set_state, clear_state
from app.ai.orchestrator import Orchestrator
from app.core.http import CoreHTTP
from app.core.logging import log
from app.core.database import get_db_session
from app.repositories.chat import ChatRepository

router = APIRouter(prefix="/ai")

class ChatCreate(BaseModel):
    title: Optional[str] = None

class Chat(BaseModel):
    id: str
    title: str
    created_at: str
    system_facts_seeded: bool

class MessageCreate(BaseModel):
    content: str
    message_id: Optional[str] = None

class Message(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

class ChatRename(BaseModel):
    title: str

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    ctx: AuthContext = Depends(get_auth_ctx),
    school_id: str = Depends(get_school_id)
):
    """Delete a chat"""
    with get_db_session() as db:
        repo = ChatRepository(db)
        deleted = repo.delete_chat(chat_id, ctx.user_id, school_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {"success": True}

@router.patch("/chats/{chat_id}/star")
async def toggle_chat_star(
    chat_id: str,
    ctx: AuthContext = Depends(get_auth_ctx),
    school_id: str = Depends(get_school_id)
):
    """Toggle chat starred status"""
    with get_db_session() as db:
        repo = ChatRepository(db)
        starred = repo.toggle_chat_star(chat_id, ctx.user_id, school_id)
        
        return {"starred": starred}

@router.patch("/chats/{chat_id}/rename")
async def rename_chat(
    chat_id: str,
    body: ChatRename,
    ctx: AuthContext = Depends(get_auth_ctx),
    school_id: str = Depends(get_school_id)
):
    """Rename a chat"""
    with get_db_session() as db:
        repo = ChatRepository(db)
        renamed = repo.rename_chat(chat_id, body.title, ctx.user_id, school_id)
        
        if not renamed:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {"success": True, "title": body.title}

@router.get("/chats", response_model=List[Chat])
async def list_chats(
    limit: int = Query(20, ge=1, le=100),
    ctx: AuthContext = Depends(get_auth_ctx), 
    school_id: str = Depends(get_school_id)
):
    """List user's chats"""
    with get_db_session() as db:
        repo = ChatRepository(db)
        chats = repo.list_chats(ctx.user_id, school_id, limit)
        
        return [
            Chat(
                id=chat.id,
                title=chat.title,
                created_at=chat.created_at.isoformat(),
                system_facts_seeded=chat.system_facts_seeded
            )
            for chat in chats
        ]

@router.post("/chats", response_model=Chat)
async def create_chat(
    body: ChatCreate, 
    request: Request,
    ctx: AuthContext = Depends(get_auth_ctx), 
    school_id: str = Depends(get_school_id)
):
    """Create a new chat"""
    # Debug: Log all incoming headers
    log.info(
        "create_chat_headers",
        authorization_present=bool(request.headers.get("authorization")),
        school_header_present=bool(request.headers.get("x-school-id")),
        user_id=ctx.user_id,
        school_id=school_id,
        bearer_token_present=bool(ctx.raw_bearer),
    )
    
    # Use a temporary title that will be updated with first message
    title = body.title or "New Chat"
    
    # Debug: log incoming create chat with auth context
    log.info(
        "chat_create_request",
        title=title,
        user_id=ctx.user_id,
        school_id=school_id,
    )

    # Get school facts
    http = CoreHTTP()
    seeded = False
    school_facts = {"school_id": school_id}
    
    try:
        log.info(
            "attempting_schools_mine_call",
            bearer_present=bool(ctx.raw_bearer),
            school_id=school_id,
        )
        
        r = await http.get("/schools/mine", bearer=ctx.raw_bearer, school_id=None)
        
        log.info(
            "schools_mine_response",
            status_code=r.status_code,
            has_content=bool(r.content),
            response_preview=str(r.content)[:200] if r.content else None,
        )
        
        if r.status_code == 200 and r.content:
            items = r.json() or []
            current = next((x for x in items if x.get("id") == school_id), None)
            if current and current.get("name"):
                school_facts["school_name"] = current["name"]
                seeded = True
    except Exception as e:
        log.error(
            "schools_mine_error",
            error=str(e),
            error_type=type(e).__name__,
        )

    # Create chat in database
    with get_db_session() as db:
        repo = ChatRepository(db)
        chat_record = repo.create_chat(title, ctx.user_id, school_id, seeded)
        
        # Extract values while still in session
        chat_id = chat_record.id
        chat_title = chat_record.title
        chat_created_at = chat_record.created_at
        chat_system_facts_seeded = chat_record.system_facts_seeded
        
        # persist school facts into slot state so orchestrator/LLM can ground answers
        state = await get_state(chat_id) or {}
        state["facts"] = school_facts
        await set_state(chat_id, state)

        # Add a system message with the school context for immediate grounding
        repo.add_message(
            chat_id=chat_id,
            role="system",
            content=f"School context → id: {school_facts.get('school_id')}, name: {school_facts.get('school_name', '(unknown)')}"
        )

    log.info(
        "chat_create_seeded",
        chat_id=chat_id,
        seeded=seeded,
        school_id=school_id,
        school_name=school_facts.get("school_name"),
    )

    return Chat(
        id=chat_id, 
        title=chat_title, 
        created_at=chat_created_at.isoformat(), 
        system_facts_seeded=chat_system_facts_seeded
    )

@router.get("/chats/{chat_id}/messages", response_model=List[Message])
async def list_messages(
    chat_id: str, 
    before_id: Optional[str] = Query(None),
    ctx: AuthContext = Depends(get_auth_ctx), 
    school_id: str = Depends(get_school_id)
):
    """Get messages for a chat"""
    with get_db_session() as db:
        repo = ChatRepository(db)
        
        # Verify chat exists and belongs to user
        if not repo.chat_exists(chat_id, ctx.user_id, school_id):
            raise HTTPException(status_code=404, detail="Chat not found")
        
        messages = repo.get_messages(chat_id, before_id)
        
        return [
            Message(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat()
            )
            for msg in messages
        ]

_orch = Orchestrator()

@router.post("/chats/{chat_id}/messages")
async def post_message(
    chat_id: str, 
    body: MessageCreate, 
    request: Request,
    ctx: AuthContext = Depends(get_auth_ctx), 
    school_id: str = Depends(get_school_id)
):
    """Send a message to a chat"""
    # Debug: Log headers for message endpoint too
    log.info(
        "post_message_headers",
        authorization_present=bool(request.headers.get("authorization")),
        school_header_present=bool(request.headers.get("x-school-id")),
        bearer_token_present=bool(ctx.raw_bearer),
    )

    log.info(
        "message_inbound",
        chat_id=chat_id,
        user_id=ctx.user_id,
        school_id=school_id,
        content_preview=(body.content[:120] if body and body.content else None),
    )

    # Verify chat exists and belongs to user
    with get_db_session() as db:
        repo = ChatRepository(db)
        
        if not repo.chat_exists(chat_id, ctx.user_id, school_id):
            raise HTTPException(status_code=404, detail="Chat not found")

        # Check if this is the first user message and update title accordingly
        existing_messages = repo.get_messages(chat_id)
        is_first_user_message = not any(msg.role == "user" for msg in existing_messages)
        
        # Add user message to database
        mid = body.message_id or str(uuid4())
        user_msg = repo.add_message(
            chat_id=chat_id,
            role="user",
            content=body.content,
            message_id=mid
        )
        
        # Update chat title based on first user message
        if is_first_user_message:
            new_title = repo.generate_chat_title_from_content(body.content)
            repo.update_chat_title(chat_id, new_title)
            log.info(
                "chat_title_updated",
                chat_id=chat_id,
                new_title=new_title,
                from_content=body.content[:50]
            )

    log.info(
        "message_recorded",
        chat_id=chat_id,
        message_id=mid,
        role="user",
    )

    # Handle confirmation workflow for fees and other operations
    lower = body.content.strip().lower()
    state = await get_state(chat_id)
    
    # Enhanced confirmation handling for fees
    if state and state.get("intent") == "modify_fee" and "_confirmed" not in state.get("slots", {}):
        if lower in ("yes", "y"):
            state["slots"]["_confirmed"] = True
            await set_state(chat_id, state)
        elif lower in ("no", "n"):
            await clear_state(chat_id)
            
            # Add assistant response to database
            with get_db_session() as db:
                repo = ChatRepository(db)
                assistant_msg = repo.add_message(
                    chat_id=chat_id,
                    role="assistant",
                    content="Cancelled."
                )
                
                # Extract values while in session
                assistant_id = assistant_msg.id
                assistant_role = assistant_msg.role
                assistant_content = assistant_msg.content
                assistant_created_at = assistant_msg.created_at
            
            return {
                "assistant": {
                    "id": assistant_id,
                    "role": assistant_role,
                    "content": assistant_content,
                    "created_at": assistant_created_at.isoformat(),
                }
            }

    # Run orchestrator with fees support
    result = await _orch.run_chat_turn(
        session_id=chat_id, 
        message=body.content, 
        bearer=ctx.raw_bearer, 
        school_id=school_id, 
        message_id=mid
    )

    log.info(
        "assistant_result",
        chat_id=chat_id,
        message_id=mid,
        tool=result.get("tool"),
        tool_status=(result.get("result", {}) or {}).get("status"),
        content_preview=result.get("content", "")[:100],
        # NEW: Log if table data is present
        has_table=bool(result.get("table"))
    )

    # Add assistant response to database
    updated_chat_title = None
    with get_db_session() as db:
        repo = ChatRepository(db)
        assistant_msg = repo.add_message(
            chat_id=chat_id,
            role="assistant",
            content=result.get("content", ""),
            tool_call=result.get("tool"),
            tool_result=result.get("result")
        )
        
        # Extract values while in session
        assistant_id = assistant_msg.id
        assistant_role = assistant_msg.role
        assistant_content = assistant_msg.content
        assistant_created_at = assistant_msg.created_at
        
        # Get updated chat title if it was changed
        if is_first_user_message:
            chat = repo.get_chat(chat_id, ctx.user_id, school_id)
            if chat:
                updated_chat_title = chat.title

    # FIXED: Include table data in response
    response = {
        "assistant": {
            "id": assistant_id,
            "role": assistant_role,
            "content": assistant_content,
            "created_at": assistant_created_at.isoformat(),
            "tool_call": result.get("tool"),
            "tool_result": result.get("result"),
            # NEW: Include table data if present
            **({} if not result.get("table") else {"table": result.get("table")})
        }
    }
    
    # Include updated chat title if this was the first message
    if updated_chat_title:
        response["chat_title_updated"] = updated_chat_title
    
    log.info(
        "sending_response",
        chat_id=chat_id,
        response_keys=list(response.keys()),
        assistant_keys=list(response["assistant"].keys()),
        has_title_update=bool(updated_chat_title),
        # NEW: Log if table is being sent
        sending_table=bool(result.get("table"))
    )
    
    return response