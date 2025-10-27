# app/api/routers/chat/endpoints/suggestions.py
from fastapi import APIRouter, Depends
from ..deps import verify_auth_and_get_context

router = APIRouter()

@router.get("/suggestions")
def get_chat_suggestions(ctx = Depends(verify_auth_and_get_context)):
    return {
        "suggestions": [
            "School overview",
            "How many students do we have?",
            "List all classes",
            "Show current academic term",
            "Check enrollment status",
            "Show unassigned students",
            "Academic calendar overview",
            "Generate invoices for all students",
            "Show payment summary",
            "Show fee structures",
            "Upload and analyze document"
        ]
    }