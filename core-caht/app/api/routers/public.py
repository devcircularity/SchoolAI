# app/api/routers/public.py - Public chat router for unauthenticated users
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
import time
import uuid

from app.core.db import get_db
from app.services.ollama_service import OllamaService
from app.services.public_chat_service import PublicChatService

router = APIRouter(prefix="/api/public", tags=["Public"])

class PublicChatMessage(BaseModel):
    message: str
    session_id: str

class PublicChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool = True

@router.post("/chat", response_model=PublicChatResponse)
async def public_chat(
    message: PublicChatMessage,
    db: Session = Depends(get_db),
):
    """Handle public chat messages for unauthenticated users"""
    try:
        start_time = time.time()
        
        # Validate session
        if not message.session_id.startswith('pub_'):
            raise HTTPException(status_code=400, detail="Invalid session ID")
        
        # Initialize services
        ollama_service = OllamaService()
        public_chat_service = PublicChatService(db)
        
        # Get conversation history (last 10 messages)
        history = public_chat_service.get_session_history(message.session_id, limit=10)
        
        # Build context-aware prompt for Ollama
        prompt = build_public_chat_prompt(message.message, history)
        
        # Get AI response
        ollama_response = ollama_service.generate_response_sync(prompt)
        
        if not ollama_response.get("success", True):
            ai_response = "I'm having some technical difficulties right now. Please try again in a moment!"
        else:
            ai_response = ollama_response.get("response", "I'm not sure how to respond to that.")
        
        # Store the conversation
        public_chat_service.store_message(
            session_id=message.session_id,
            user_message=message.message,
            ai_response=ai_response,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        return PublicChatResponse(
            response=ai_response,
            session_id=message.session_id
        )
        
    except Exception as e:
        print(f"Public chat error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback response
        return PublicChatResponse(
            response="I apologize, but I'm experiencing some technical difficulties. Please try again or consider signing up for full access to our school management features!",
            session_id=message.session_id,
            success=False
        )

def build_public_chat_prompt(user_message: str, history: list) -> str:
    """Build a context-aware prompt for public chat"""
    
    # Build conversation context
    context = ""
    if history:
        context = "\n\nPREVIOUS CONVERSATION:\n"
        for entry in history[-5:]:  # Last 5 exchanges
            context += f"User: {entry['user_message']}\n"
            context += f"Assistant: {entry['ai_response']}\n\n"
    
    prompt = f"""You are Olaji Chat, an AI assistant for school management. You're talking to someone who hasn't signed up yet. Your goal is to be helpful while demonstrating Olaji's capabilities and encouraging them to sign up.

GUIDELINES:
1. Be friendly, helpful, and professional
2. Answer their questions but always relate back to school management capabilities
3. If they ask about features, explain them but mention they need to sign up for full access
4. If they ask general questions, answer but steer toward educational/school topics
5. Regularly mention the benefits of signing up (full school management, student tracking, invoicing, etc.)
6. Be enthusiastic about Olaji's school management features
7. Keep responses conversational and not too sales-y

OLAJI FEATURES TO HIGHLIGHT:
- Complete school management system
- Student enrollment and class management  
- Automated invoicing and payment tracking
- Academic calendar and term management
- Real-time school analytics and reports
- File upload and document processing
- WhatsApp integration for parent communication
- Multi-user access with different roles

{context}

CURRENT USER MESSAGE: "{user_message}"

Respond as Olaji Chat, being helpful while encouraging sign-up. Keep it conversational and under 150 words:"""

    return prompt

@router.get("/health")
def public_health():
    """Public health check endpoint"""
    return {"status": "healthy", "service": "public_chat"}