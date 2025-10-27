# app/api/routers/chat/endpoints/messages.py
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.chat_service import ChatService
from app.models.chat import MessageType
from app.schemas.chat import ChatMessage, ChatResponse, prepare_for_json_storage
from ..deps import verify_auth_and_get_context
from ..utils import serialize_blocks
from ..processor import IntentProcessor

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    message: ChatMessage,
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    try:
        start_time = time.time()
        chat_service = ChatService(db)

        # context action -> replace text
        if message.context and message.context.get("action"):
            action = message.context["action"]
            if action.get("type") == "query" and action.get("payload", {}).get("message"):
                message.message = action["payload"]["message"]

        # conversation
        if message.conversation_id:
            conversation = chat_service.get_conversation(message.conversation_id, ctx["user_id"], ctx["school_id"])
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conversation = chat_service.create_conversation(ctx["user_id"], ctx["school_id"], message.message)

        conversation_id = str(conversation.id)

        # store user msg
        user_message = chat_service.add_message(
            conversation_id=conversation_id,
            user_id=ctx["user_id"],
            school_id=ctx["school_id"],
            message_type=MessageType.USER,
            content=message.message,
            context_data=message.context
        )

        # merge context with stored
        context = message.context or {}
        if message.conversation_id or conversation.message_count > 0:
            stored_context = chat_service.get_conversation_context(conversation_id, ctx["user_id"], ctx["school_id"])
            if stored_context:
                context = {**context, **stored_context}

        # process with updated processor (LLM + ConfigRouter architecture)
        processor = IntentProcessor(db=db, user_id=ctx["user_id"], school_id=ctx["school_id"])
        response = processor.process_message(message.message, context)
        
        processing_time = int((time.time() - start_time) * 1000)

        # response_data + blocks
        response_data = response.data or {}
        if getattr(response, "blocks", None):
            response_data["blocks"] = serialize_blocks(response.blocks)

        # store assistant msg and get the created message object
        assistant_message = chat_service.add_message(
            conversation_id=conversation_id,
            user_id=ctx["user_id"],
            school_id=ctx["school_id"],
            message_type=MessageType.ASSISTANT,
            content=response.response,
            intent=response.intent,
            response_data=prepare_for_json_storage(response_data),
            processing_time_ms=processing_time
        )

        db.commit()
        
        # Set the conversation_id and message_id in the response
        response.conversation_id = conversation_id
        response.message_id = str(assistant_message.id)  # Include the message ID for rating buttons
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Chat error: {e}")
        import traceback; traceback.print_exc()
        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)}", 
            intent="error"
        )