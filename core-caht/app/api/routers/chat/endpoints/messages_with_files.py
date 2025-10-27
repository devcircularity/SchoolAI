# app/api/routers/chat/endpoints/messages_with_files.py
import time
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.chat_service import ChatService
from app.services.file_service import FileService
from app.models.chat import MessageType
from app.schemas.chat import ChatResponse, FileAttachment, prepare_for_json_storage
from ..deps import verify_auth_and_get_context
from ..utils import serialize_blocks
from ..handlers.document_handler import DocumentHandler

router = APIRouter()

@router.post("/message-with-files", response_model=ChatResponse)
async def chat_message_with_files(
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    ctx = Depends(verify_auth_and_get_context),
    db: Session = Depends(get_db),
):
    try:
        start_time = time.time()
        
        # Validate file count
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 files allowed per message")

        chat_service = ChatService(db)
        file_service = FileService()

        # Process file attachments
        processed, errors = [], []
        for f in files:
            try:
                att = await file_service.process_file_attachment(f)
                fa = FileAttachment(
                    attachment_id=att['attachment_id'],
                    original_filename=att['file_metadata']['original_filename'],
                    content_type=att['file_metadata']['content_type'],
                    file_size=att['file_metadata']['bytes'],
                    cloudinary_url=att['file_metadata']['secure_url'],
                    cloudinary_public_id=att['file_metadata']['public_id'],
                    upload_timestamp=att['file_metadata']['created_at'],
                    ocr_processed=att['ocr_result']['success'],
                    ocr_data=att['ocr_result']['ocr_data'] if att['ocr_result']['success'] else None
                )
                processed.append({'file_attachment': fa, 'attachment_data': att})
            except Exception as e:
                errors.append({'filename': f.filename, 'error': str(e)})

        # Ensure at least one file was processed successfully
        if not processed:
            raise HTTPException(status_code=400, detail=f"No files could be processed. Errors: {errors}")

        # Handle conversation - create new if needed or validate existing
        if conversation_id:
            conv = chat_service.get_conversation(conversation_id, ctx["user_id"], ctx["school_id"])
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conv = chat_service.create_conversation(ctx["user_id"], ctx["school_id"], message)
        
        conv_id = str(conv.id)

        # Store USER message with attachments in response_data
        prepared_attachments = prepare_for_json_storage([att['file_attachment'].dict() for att in processed])
        user_message = chat_service.add_message(
            conversation_id=conv_id,
            user_id=ctx["user_id"],
            school_id=ctx["school_id"],
            message_type=MessageType.USER,
            content=message,
            context_data=None,
            response_data={"attachments": prepared_attachments}
        )

        # Process the primary attachment with AI
        handler = DocumentHandler(db, ctx["school_id"], ctx["user_id"])
        primary = processed[0]
        ai_response = await handler.handle_with_attachment(
            message=message, 
            attachment_data=primary['attachment_data'], 
            context=None
        )

        # Add info about additional files if present
        if len(processed) > 1:
            ai_response.data = ai_response.data or {}
            ai_response.data['additional_attachments'] = len(processed) - 1
            ai_response.response += f"\n\n*Note: Processed {len(processed)} files. Analysis focused on: {primary['file_attachment'].original_filename}*"

        processing_time = int((time.time() - start_time) * 1000)

        # Prepare response data for assistant message
        response_data = ai_response.data or {}
        if getattr(ai_response, "blocks", None):
            response_data["blocks"] = serialize_blocks(ai_response.blocks)

        # Store ASSISTANT message (no attachments - those are on the user message)
        assistant_message = chat_service.add_message(
            conversation_id=conv_id,
            user_id=ctx["user_id"],
            school_id=ctx["school_id"],
            message_type=MessageType.ASSISTANT,
            content=ai_response.response,
            intent=ai_response.intent,
            response_data=prepare_for_json_storage(response_data),
            processing_time_ms=processing_time
        )

        # Commit all database changes
        db.commit()
        
        # Prepare final response
        ai_response.conversation_id = conv_id
        ai_response.message_id = str(assistant_message.id)  # CRITICAL: Include message ID for rating buttons
        ai_response.attachment_processed = True
        
        # Add attachment errors to response if any occurred
        if errors:
            ai_response.data = ai_response.data or {}
            ai_response.data['attachment_errors'] = errors

        return ai_response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Rollback on any other error
        db.rollback()
        print(f"Chat with files error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a user-friendly error response
        return ChatResponse(
            response=f"Sorry, I encountered an error processing your files: {str(e)}", 
            intent="file_processing_error"
        )