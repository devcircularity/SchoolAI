# app/services/public_chat_service.py - Service for managing public chat sessions
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

class PublicChatService:
    """Service for managing temporary public chat sessions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def store_message(
        self, 
        session_id: str,
        user_message: str,
        ai_response: str,
        processing_time_ms: int = None
    ) -> bool:
        """Store a public chat message exchange"""
        try:
            # Create table if it doesn't exist
            self._ensure_table_exists()
            
            # Insert the message exchange
            self.db.execute(
                text("""
                    INSERT INTO public_chat_messages 
                    (session_id, user_message, ai_response, processing_time_ms, created_at)
                    VALUES (:session_id, :user_message, :ai_response, :processing_time_ms, :created_at)
                """),
                {
                    "session_id": session_id,
                    "user_message": user_message,
                    "ai_response": ai_response,
                    "processing_time_ms": processing_time_ms,
                    "created_at": datetime.utcnow()
                }
            )
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error storing public chat message: {e}")
            self.db.rollback()
            return False
    
    def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        try:
            self._ensure_table_exists()
            
            result = self.db.execute(
                text("""
                    SELECT user_message, ai_response, created_at
                    FROM public_chat_messages 
                    WHERE session_id = :session_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"session_id": session_id, "limit": limit}
            ).fetchall()
            
            # Return in chronological order (oldest first)
            return [
                {
                    "user_message": row.user_message,
                    "ai_response": row.ai_response,
                    "created_at": row.created_at
                }
                for row in reversed(result)
            ]
            
        except Exception as e:
            print(f"Error getting session history: {e}")
            return []
    
    def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """Clean up old public chat sessions"""
        try:
            self._ensure_table_exists()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            result = self.db.execute(
                text("""
                    DELETE FROM public_chat_messages 
                    WHERE created_at < :cutoff_date
                """),
                {"cutoff_date": cutoff_date}
            )
            
            deleted_count = result.rowcount
            self.db.commit()
            
            print(f"Cleaned up {deleted_count} old public chat messages")
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old sessions: {e}")
            self.db.rollback()
            return 0
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        try:
            self._ensure_table_exists()
            
            result = self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as message_count,
                        MIN(created_at) as first_message,
                        MAX(created_at) as last_message,
                        AVG(processing_time_ms) as avg_processing_time
                    FROM public_chat_messages 
                    WHERE session_id = :session_id
                """),
                {"session_id": session_id}
            ).fetchone()
            
            if result:
                return {
                    "message_count": result.message_count,
                    "first_message": result.first_message,
                    "last_message": result.last_message,
                    "avg_processing_time": result.avg_processing_time
                }
            else:
                return {"message_count": 0}
                
        except Exception as e:
            print(f"Error getting session stats: {e}")
            return {"message_count": 0}