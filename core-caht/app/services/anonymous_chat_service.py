# app/services/anonymous_chat_service.py - Anonymous Chat Service

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from app.models.chat import MessageType

class AnonymousChatService:
    """Service for managing anonymous chat sessions and rate limiting"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Rate limiting settings for anonymous users
        self.max_messages_per_session = 20  # Max messages per anonymous session
        self.max_sessions_per_ip = 5  # Max sessions per IP (if we implement IP tracking)
        self.session_expiry_hours = 24  # Anonymous sessions expire after 24 hours
        
    def add_message(
        self,
        session_id: str,
        message_type: MessageType,
        content: str,
        intent: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None
    ) -> str:
        """Add message to anonymous session"""
        
        # Serialize JSON data
        context_json = json.dumps(context_data) if context_data else None
        response_json = json.dumps(response_data) if response_data else None
        
        # Insert message into anonymous_messages table
        result = self.db.execute(
            text("""
                INSERT INTO anonymous_messages (
                    session_id, message_type, content, intent,
                    context_data, response_data, processing_time_ms, created_at
                ) VALUES (
                    :session_id, :message_type, :content, :intent,
                    :context_data, :response_data, :processing_time_ms, :created_at
                ) RETURNING id
            """),
            {
                "session_id": session_id,
                "message_type": message_type.value,
                "content": content,
                "intent": intent,
                "context_data": context_json,
                "response_data": response_json,
                "processing_time_ms": processing_time_ms,
                "created_at": datetime.utcnow()
            }
        )
        
        message_id = result.scalar()
        return str(message_id)
    
    def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get all messages for an anonymous session"""
        
        result = self.db.execute(
            text("""
                SELECT id, session_id, message_type, content, intent,
                       context_data, response_data, processing_time_ms, created_at
                FROM anonymous_messages 
                WHERE session_id = :session_id
                ORDER BY created_at ASC
                LIMIT :limit
            """),
            {"session_id": session_id, "limit": limit}
        )
        
        messages = []
        for row in result:
            # Parse JSON data
            context_data = None
            if row.context_data:
                try:
                    context_data = json.loads(row.context_data)
                except:
                    pass
            
            response_data = None
            if row.response_data:
                try:
                    response_data = json.loads(row.response_data)
                except:
                    pass
            
            messages.append({
                "id": row.id,
                "session_id": row.session_id,
                "message_type": row.message_type,
                "content": row.content,
                "intent": row.intent,
                "context_data": context_data,
                "response_data": response_data,
                "processing_time_ms": row.processing_time_ms,
                "created_at": row.created_at
            })
        
        return messages
    
    def get_recent_messages(self, session_id: str, limit: int = 5) -> List[Dict]:
        """Get recent messages for context"""
        
        result = self.db.execute(
            text("""
                SELECT id, session_id, message_type, content, intent,
                       context_data, response_data, processing_time_ms, created_at
                FROM anonymous_messages 
                WHERE session_id = :session_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"session_id": session_id, "limit": limit}
        )
        
        messages = []
        for row in result:
            messages.append({
                "id": row.id,
                "session_id": row.session_id,
                "message_type": row.message_type,
                "content": row.content,
                "intent": row.intent,
                "created_at": row.created_at
            })
        
        # Return in chronological order
        return list(reversed(messages))
    
    def get_message_count(self, session_id: str) -> int:
        """Get total message count for session"""
        
        result = self.db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM anonymous_messages 
                WHERE session_id = :session_id
            """),
            {"session_id": session_id}
        )
        
        return result.scalar() or 0
    
    def check_rate_limit(self, session_id: str) -> bool:
        """Check if session is within rate limits"""
        
        message_count = self.get_message_count(session_id)
        
        # Check message limit per session
        if message_count >= self.max_messages_per_session:
            return False
        
        # Check session age
        if not self._is_session_valid(session_id):
            return False
        
        return True
    
    def _is_session_valid(self, session_id: str) -> bool:
        """Check if session is still valid (not expired)"""
        
        # Get oldest message in session
        result = self.db.execute(
            text("""
                SELECT MIN(created_at) as first_message
                FROM anonymous_messages 
                WHERE session_id = :session_id
            """),
            {"session_id": session_id}
        )
        
        first_message_time = result.scalar()
        
        if not first_message_time:
            # No messages yet, session is valid
            return True
        
        # Check if session has expired
        expiry_time = first_message_time + timedelta(hours=self.session_expiry_hours)
        return datetime.utcnow() < expiry_time
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired anonymous sessions - run periodically"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=self.session_expiry_hours)
        
        result = self.db.execute(
            text("""
                DELETE FROM anonymous_messages 
                WHERE created_at < :cutoff_time
            """),
            {"cutoff_time": cutoff_time}
        )
        
        deleted_count = result.rowcount
        self.db.commit()
        
        return deleted_count
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for an anonymous session"""
        
        result = self.db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN message_type = 'USER' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN message_type = 'ASSISTANT' THEN 1 END) as assistant_messages,
                    MIN(created_at) as first_message_at,
                    MAX(created_at) as last_message_at,
                    AVG(processing_time_ms) as avg_processing_time
                FROM anonymous_messages 
                WHERE session_id = :session_id
            """),
            {"session_id": session_id}
        )
        
        row = result.first()
        
        if not row or row.total_messages == 0:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "session_duration_minutes": 0,
                "avg_processing_time_ms": 0,
                "messages_remaining": self.max_messages_per_session
            }
        
        # Calculate session duration
        session_duration = 0
        if row.first_message_at and row.last_message_at:
            duration_delta = row.last_message_at - row.first_message_at
            session_duration = duration_delta.total_seconds() / 60  # Convert to minutes
        
        return {
            "total_messages": row.total_messages,
            "user_messages": row.user_messages,
            "assistant_messages": row.assistant_messages,
            "session_duration_minutes": round(session_duration, 2),
            "avg_processing_time_ms": round(row.avg_processing_time or 0, 2),
            "messages_remaining": max(0, self.max_messages_per_session - row.total_messages),
            "first_message_at": row.first_message_at,
            "last_message_at": row.last_message_at
        }