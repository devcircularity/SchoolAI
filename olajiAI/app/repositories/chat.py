# app/repositories/chat.py
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.chat import Chat, Message
from datetime import datetime, timezone

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_chat(self, title: str, user_id: str, school_id: str, system_facts_seeded: bool = False) -> Chat:
        """Create a new chat"""
        chat = Chat(
            title=title,
            user_id=user_id,
            school_id=school_id,
            system_facts_seeded=system_facts_seeded
        )
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat
    
    def get_chat(self, chat_id: str, user_id: str, school_id: str) -> Optional[Chat]:
        """Get a chat by ID, ensuring it belongs to the user/school"""
        return self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.school_id == school_id
        ).first()
    
    def list_chats(self, user_id: str, school_id: str, limit: int = 20) -> List[Chat]:
        """List chats for a user/school, ordered by most recent"""
        return self.db.query(Chat).filter(
            Chat.user_id == user_id,
            Chat.school_id == school_id
        ).order_by(desc(Chat.updated_at)).limit(limit).all()
    
    def add_message(
        self, 
        chat_id: str, 
        role: str, 
        content: str, 
        message_id: Optional[str] = None,
        tool_call: Optional[dict] = None,
        tool_result: Optional[dict] = None
    ) -> Message:
        """Add a message to a chat"""
        message = Message(
            id=message_id or None,  # Will auto-generate if None
            chat_id=chat_id,
            role=role,
            content=content,
            tool_call=json.dumps(tool_call) if tool_call else None,
            tool_result=json.dumps(tool_result) if tool_result else None
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # Update chat's updated_at timestamp
        chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if chat:
            chat.updated_at = datetime.now(timezone.utc)
            self.db.commit()
        
        return message
    
    def get_messages(self, chat_id: str, before_id: Optional[str] = None) -> List[Message]:
        """Get messages for a chat"""
        query = self.db.query(Message).filter(Message.chat_id == chat_id)
        
        if before_id:
            # Get messages before a specific message (for pagination)
            before_message = self.db.query(Message).filter(Message.id == before_id).first()
            if before_message:
                query = query.filter(Message.created_at < before_message.created_at)
        
        return query.order_by(Message.created_at).all()
    
    def chat_exists(self, chat_id: str, user_id: str, school_id: str) -> bool:
        """Check if a chat exists for the user/school"""
        return self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.school_id == school_id
        ).first() is not None
    
    def update_chat_title(self, chat_id: str, title: str) -> None:
        """Update a chat's title"""
        chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if chat:
            chat.title = title
            chat.updated_at = datetime.now(timezone.utc)
            self.db.commit()
    
    def generate_chat_title_from_content(self, content: str) -> str:
        """Generate a chat title from the first user message - use the message directly with smart truncation"""
        # Clean the content
        content = content.strip()
        
        # If it's short enough, use it as-is
        if len(content) <= 35:
            return content
    
    def delete_chat(self, chat_id: str, user_id: str, school_id: str) -> bool:
        """Delete a chat and all its messages"""
        chat = self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.school_id == school_id
        ).first()
        
        if chat:
            self.db.delete(chat)  # Cascade will delete messages
            self.db.commit()
            return True
        return False
    
    def toggle_chat_star(self, chat_id: str, user_id: str, school_id: str) -> bool:
        """Toggle the starred status of a chat"""
        chat = self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.school_id == school_id
        ).first()
        
        if chat:
            chat.starred = not chat.starred
            chat.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return chat.starred
        return False
    
    def rename_chat(self, chat_id: str, new_title: str, user_id: str, school_id: str) -> bool:
        """Rename a chat"""
        chat = self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.school_id == school_id
        ).first()
        
        if chat:
            chat.title = new_title.strip()
            chat.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False
        
        # For longer content, truncate intelligently
        # Try to break at word boundaries
        if len(content) > 35:
            # Find the last space before the 35-character mark
            truncated = content[:35]
            last_space = truncated.rfind(' ')
            
            if last_space > 25:  # If we can break at a reasonable word boundary
                return content[:last_space] + "..."
            else:
                # Otherwise, just truncate at 32 chars and add "..."
                return content[:32] + "..."
        
        return content