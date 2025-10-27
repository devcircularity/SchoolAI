# app/api/routers/chat/__init__.py
from fastapi import APIRouter
from .endpoints import messages, messages_with_files, feedback, conversations, suggestions, health

router = APIRouter(prefix="/chat", tags=["Chat"])
router.include_router(messages.router)
router.include_router(messages_with_files.router)
router.include_router(conversations.router)
router.include_router(feedback.router)
router.include_router(suggestions.router)
router.include_router(health.router)

__all__ = ["router"]