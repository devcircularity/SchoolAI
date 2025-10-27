#app/state/memory.py
from app.core.redis import get_redis
from app.core.config import settings
import json
from typing import Any, Dict

def _key(session_id: str) -> str:
    return f"chat_state:{session_id}"

async def get_state(session_id: str) -> Dict[str, Any] | None:
    r = await get_redis()
    raw = await r.get(_key(session_id))
    return json.loads(raw) if raw else None

async def set_state(session_id: str, value: Dict[str, Any]):
    r = await get_redis()
    await r.set(_key(session_id), json.dumps(value), ex=settings.SLOT_TTL_SECONDS)

async def clear_state(session_id: str):
    r = await get_redis()
    await r.delete(_key(session_id))
