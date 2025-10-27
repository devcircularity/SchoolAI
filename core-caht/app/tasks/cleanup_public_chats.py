# app/tasks/cleanup_public_chats.py - Cleanup task for old public chat sessions
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import get_db_session
from app.services.public_chat_service import PublicChatService

def cleanup_old_public_chats():
    """Cleanup old public chat sessions - run this periodically"""
    try:
        db = next(get_db_session())
        public_chat_service = PublicChatService(db)
        
        # Clean up sessions older than 7 days
        deleted_count = public_chat_service.cleanup_old_sessions(days_old=7)
        
        print(f"[{datetime.utcnow()}] Cleaned up {deleted_count} old public chat messages")
        
        db.close()
        return deleted_count
        
    except Exception as e:
        print(f"Error in cleanup task: {e}")
        return 0

if __name__ == "__main__":
    cleanup_old_public_chats()