# app/api/routers/chat/endpoints/health.py
from fastapi import APIRouter, Depends
from ..deps import verify_auth_and_get_context

router = APIRouter()

@router.get("/health/ollama")
async def check_ollama_health(ctx = Depends(verify_auth_and_get_context)):
    from app.services.ollama_service import OllamaService
    ollama = OllamaService()
    is_healthy = await ollama.health_check()
    return {"ollama_available": is_healthy, "model": ollama.model, "base_url": ollama.base_url}