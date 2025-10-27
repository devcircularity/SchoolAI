# app/services/chat_service.py - Updated with message ID return functionality
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
from sqlalchemy.exc import SQLAlchemyError

from app.models.chat import ChatConversation, ChatMessage, MessageType

class ChatService:
    """Enhanced service for managing chat conversations with context cleanup"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    def generate_conversation_title(self, first_message: str) -> str:
        """Generate a concise title from the first message"""
        try:
            cleaned = re.sub(r'[^\w\s]', '', first_message).strip()
            words = [w for w in cleaned.split() if len(w) > 2][:6]
            
            if not words:
                return "New Conversation"
            
            title = ' '.join(words)
            title = title.capitalize()
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title or "New Conversation"
        except Exception as e:
            print(f"Error generating title: {e}")
            return "New Conversation"
    
    def create_conversation(
        self, 
        user_id: str, 
        school_id: str, 
        first_message: str
    ) -> ChatConversation:
        """Create a new conversation with proper error handling"""
        try:
            title = self.generate_conversation_title(first_message)
            
            conversation = ChatConversation(
                user_id=uuid.UUID(user_id),
                school_id=uuid.UUID(school_id),
                title=title,
                first_message=first_message,
                last_activity=datetime.utcnow(),
                message_count=0,
                context_data={}
            )
            
            self.db.add(conversation)
            self.db.flush()
            print(f"Created conversation with ID: {conversation.id}")
            return conversation
            
        except SQLAlchemyError as e:
            print(f"Database error creating conversation: {e}")
            self._rollback_safe()
            raise
        except Exception as e:
            print(f"Error creating conversation: {e}")
            self._rollback_safe()
            raise
    
    def get_conversation(
        self, 
        conversation_id: str, 
        user_id: str, 
        school_id: str
    ) -> Optional[ChatConversation]:
        """Get a conversation by ID (with access control)"""
        try:
            if not self.is_valid_uuid(conversation_id):
                print(f"Invalid UUID format: {conversation_id}")
                return None
            
            return self.db.query(ChatConversation).filter(
                ChatConversation.id == uuid.UUID(conversation_id),
                ChatConversation.user_id == uuid.UUID(user_id),
                ChatConversation.school_id == uuid.UUID(school_id)
            ).first()
            
        except SQLAlchemyError as e:
            print(f"Database error getting conversation: {e}")
            self._rollback_safe()
            return None
        except Exception as e:
            print(f"Error getting conversation: {e}")
            return None
    
    def update_conversation_context(
        self,
        conversation_id: str,
        user_id: str,
        school_id: str,
        context_data: Dict[str, Any]
    ) -> bool:
        """Update conversation context data"""
        try:
            print(f"Updating context for conversation {conversation_id}")
            print(f"New context data: {context_data}")
            
            conversation = self.get_conversation(conversation_id, user_id, school_id)
            if not conversation:
                print(f"No conversation found to update context: {conversation_id}")
                return False
            
            # Merge with existing context, new data takes precedence
            existing_context = conversation.context_data or {}
            print(f"Existing context: {existing_context}")
            
            merged_context = {**existing_context, **context_data}
            print(f"Merged context: {merged_context}")
            
            conversation.context_data = merged_context
            conversation.updated_at = datetime.utcnow()
            
            self.db.flush()
            print(f"Context updated successfully in database")
            return True
            
        except Exception as e:
            print(f"Error updating conversation context: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_conversation_context(
        self,
        conversation_id: str,
        user_id: str,
        school_id: str,
        include_recent_messages: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive conversation context - FIXED to prioritize database context"""
        try:
            if not self.is_valid_uuid(conversation_id):
                print(f"Invalid conversation_id UUID format: {conversation_id}")
                return {}
            
            conversation = self.get_conversation(conversation_id, user_id, school_id)
            if not conversation:
                print(f"No conversation found for ID: {conversation_id}")
                return {}
            
            # DEBUG: Check what's stored in database
            print(f"Raw conversation context_data from DB: {conversation.context_data}")
            
            # CRITICAL: Start with stored context as primary source
            context = conversation.context_data or {}
            print(f"Parsed stored context: {context}")
            
            # Add conversation metadata
            context.update({
                "conversation_id": conversation_id,
                "conversation_title": conversation.title,
                "message_count": conversation.message_count
            })
            
            # Include recent messages for reference only
            if include_recent_messages:
                recent_messages = self.get_conversation_messages(
                    conversation_id, user_id, school_id, limit=5
                )
                
                if recent_messages:
                    context["recent_messages"] = [
                        {
                            "type": msg.message_type.value,
                            "content": msg.content,
                            "intent": msg.intent,
                            "timestamp": msg.created_at.isoformat()
                        }
                        for msg in recent_messages[-5:]
                    ]
                    
                    # CRITICAL FIX: DO NOT override database context with message context
                    # Database context is authoritative for flow state
                    last_assistant_msg = next(
                        (msg for msg in reversed(recent_messages) 
                         if msg.message_type == MessageType.ASSISTANT),
                        None
                    )
                    
                    if last_assistant_msg and last_assistant_msg.response_data:
                        print(f"Last assistant response_data: {last_assistant_msg.response_data}")
                        response_context = last_assistant_msg.response_data.get('context', {})
                        if response_context:
                            print(f"Available response context: {response_context}")
                            
                            # ONLY merge NON-PROTECTED fields from response context
                            # NEVER override: handler, flow, step, selected_grade, class_name, grade_name
                            protected_fields = [
                                'handler', 'flow', 'step', 
                                'selected_grade', 'class_name', 'grade_name', 'selected_group'
                            ]
                            
                            for key, value in response_context.items():
                                if key not in protected_fields and key not in context:
                                    # Only add if not already in database context
                                    context[key] = value
                                    print(f"Added non-protected field from response: {key}")
                                elif key in protected_fields:
                                    print(f"Skipped protected field from response: {key}")
            
            print(f"Final retrieved context (database takes precedence): {context}")
            return context
            
        except Exception as e:
            print(f"Error getting conversation context: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def clear_conversation_context(
        self,
        conversation_id: str,
        user_id: str,
        school_id: str
    ) -> bool:
        """Clear conversation context (for ending flows)"""
        try:
            conversation = self.get_conversation(conversation_id, user_id, school_id)
            if not conversation:
                print(f"No conversation found to clear context: {conversation_id}")
                return False
            
            conversation.context_data = {}
            conversation.updated_at = datetime.utcnow()
            
            self.db.flush()
            print(f"Cleared conversation context for: {conversation_id}")
            return True
            
        except Exception as e:
            print(f"Error clearing conversation context: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_message(
        self,
        conversation_id: str,
        user_id: str,
        school_id: str,
        message_type: MessageType,
        content: str,
        intent: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None
    ) -> ChatMessage:
        """Add a message to a conversation with enhanced context management - NOW RETURNS THE MESSAGE OBJECT"""
        try:
            # DEBUG: Log the message type being stored
            print(f"ChatService.add_message - Storing message_type: {message_type}")
            print(f"ChatService.add_message - message_type type: {type(message_type)}")
            print(f"ChatService.add_message - message_type value: {message_type.value if hasattr(message_type, 'value') else 'NO VALUE'}")
            
            # Validate UUID format
            if not self.is_valid_uuid(conversation_id):
                raise ValueError(f"Invalid conversation_id UUID format: {conversation_id}")
            
            # Check if we're in an aborted transaction state
            if self._is_transaction_aborted():
                print("Transaction is aborted, rolling back before proceeding")
                self.db.rollback()
            
            message = ChatMessage(
                conversation_id=uuid.UUID(conversation_id),
                user_id=uuid.UUID(user_id),
                school_id=uuid.UUID(school_id),
                message_type=message_type,
                content=content,
                intent=intent,
                context_data=context_data,
                response_data=response_data,
                processing_time_ms=processing_time_ms
            )
            
            self.db.add(message)
            self.db.flush()  # CRITICAL: This ensures the ID is generated before return
            print(f"Added message with ID: {message.id}")
            
            # Update conversation stats
            conversation_uuid = uuid.UUID(conversation_id)
            
            affected_rows = self.db.execute(
                text("""
                    UPDATE chat_conversations 
                    SET last_activity = :last_activity,
                        message_count = message_count + 1,
                        updated_at = :updated_at
                    WHERE id = :conversation_id
                """),
                {
                    "last_activity": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "conversation_id": conversation_uuid
                }
            ).rowcount
            
            if affected_rows == 0:
                print(f"Warning: Conversation update affected 0 rows for ID: {conversation_id}")
            
            # CRITICAL: Handle context management for assistant messages
            if (message_type == MessageType.ASSISTANT and 
                response_data and 
                'context' in response_data):
                
                context_to_store = response_data['context']
                
                # If context is empty dict, clear the conversation context
                if context_to_store == {}:
                    print("Clearing conversation context - flow completed")
                    self.clear_conversation_context(conversation_id, user_id, school_id)
                else:
                    # Update with new context
                    print(f"Storing context in conversation: {context_to_store}")
                    self.update_conversation_context(
                        conversation_id, user_id, school_id, context_to_store
                    )
            
            # CRITICAL: Return the message object with its ID
            return message
            
        except SQLAlchemyError as e:
            print(f"Database error adding message: {e}")
            self._rollback_safe()
            raise
        except Exception as e:
            print(f"Error adding message: {e}")
            self._rollback_safe()
            raise
    
    def get_user_conversations(
        self, 
        user_id: str, 
        school_id: str,
        page: int = 1,
        limit: int = 20,
        include_archived: bool = False
    ) -> Tuple[List[ChatConversation], int]:
        """Get paginated conversations for a user"""
        try:
            print(f"Getting conversations for user_id: {user_id}, school_id: {school_id}")
            
            query = self.db.query(ChatConversation).filter(
                ChatConversation.user_id == uuid.UUID(user_id),
                ChatConversation.school_id == uuid.UUID(school_id)
            )
            
            if not include_archived:
                query = query.filter(ChatConversation.is_archived == False)
            
            total = query.count()
            print(f"Conversations for this user/school: {total}")
            
            conversations = query.order_by(
                desc(ChatConversation.last_activity)
            ).offset((page - 1) * limit).limit(limit).all()
            
            print(f"Retrieved {len(conversations)} conversations")
            return conversations, total
            
        except SQLAlchemyError as e:
            print(f"Database error getting user conversations: {e}")
            self._rollback_safe()
            return [], 0
        except Exception as e:
            print(f"Error getting user conversations: {e}")
            return [], 0
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        school_id: str,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get messages for a conversation with message type debugging"""
        try:
            if not self.is_valid_uuid(conversation_id):
                print(f"Invalid conversation_id UUID format: {conversation_id}")
                return []
            
            # Verify access
            conversation = self.get_conversation(conversation_id, user_id, school_id)
            if not conversation:
                return []
            
            query = self.db.query(ChatMessage).filter(
                ChatMessage.conversation_id == uuid.UUID(conversation_id)
            ).order_by(ChatMessage.created_at)
            
            if limit:
                query = query.limit(limit)
            
            messages = query.all()
            
            # DEBUG: Log what message types we're getting from database
            print(f"ChatService.get_conversation_messages - Retrieved {len(messages)} messages:")
            for i, msg in enumerate(messages):
                print(f"  Message {i}: message_type={msg.message_type}, type={type(msg.message_type)}, content_preview='{msg.content[:20]}...'")
                if hasattr(msg.message_type, 'value'):
                    print(f"    Enum value: {msg.message_type.value}")
            
            return messages
            
        except SQLAlchemyError as e:
            print(f"Database error getting conversation messages: {e}")
            self._rollback_safe()
            return []
        except Exception as e:
            print(f"Error getting conversation messages: {e}")
            return []
    
    def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        school_id: str,
        title: Optional[str] = None,
        is_archived: Optional[bool] = None
    ) -> Optional[ChatConversation]:
        """Update conversation properties"""
        try:
            if not self.is_valid_uuid(conversation_id):
                print(f"Invalid conversation_id UUID format: {conversation_id}")
                return None
            
            conversation = self.get_conversation(conversation_id, user_id, school_id)
            if not conversation:
                return None
            
            if title is not None:
                conversation.title = title
            if is_archived is not None:
                conversation.is_archived = is_archived
            
            conversation.updated_at = datetime.utcnow()
            return conversation
            
        except SQLAlchemyError as e:
            print(f"Database error updating conversation: {e}")
            self._rollback_safe()
            return None
        except Exception as e:
            print(f"Error updating conversation: {e}")
            return None
    
    def delete_conversation(
        self,
        conversation_id: str,
        user_id: str,
        school_id: str
    ) -> bool:
        """Delete a conversation and all its messages"""
        try:
            if not self.is_valid_uuid(conversation_id):
                print(f"Invalid conversation_id UUID format: {conversation_id}")
                return False
            
            conversation = self.get_conversation(conversation_id, user_id, school_id)
            if not conversation:
                return False
            
            self.db.delete(conversation)
            return True
            
        except SQLAlchemyError as e:
            print(f"Database error deleting conversation: {e}")
            self._rollback_safe()
            return False
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False
    
    def get_recent_conversations(
        self,
        user_id: str,
        school_id: str,
        days: int = 7,
        limit: int = 10
    ) -> List[ChatConversation]:
        """Get recent conversations within specified days"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            return self.db.query(ChatConversation).filter(
                ChatConversation.user_id == uuid.UUID(user_id),
                ChatConversation.school_id == uuid.UUID(school_id),
                ChatConversation.last_activity >= since_date,
                ChatConversation.is_archived == False
            ).order_by(desc(ChatConversation.last_activity)).limit(limit).all()
            
        except SQLAlchemyError as e:
            print(f"Database error getting recent conversations: {e}")
            self._rollback_safe()
            return []
        except Exception as e:
            print(f"Error getting recent conversations: {e}")
            return []
    
    def search_conversations(
        self,
        user_id: str,
        school_id: str,
        query: str,
        limit: int = 20
    ) -> List[ChatConversation]:
        """Search conversations by title or first message"""
        try:
            search_term = f"%{query}%"
            
            return self.db.query(ChatConversation).filter(
                ChatConversation.user_id == uuid.UUID(user_id),
                ChatConversation.school_id == uuid.UUID(school_id),
                (ChatConversation.title.ilike(search_term) | 
                 ChatConversation.first_message.ilike(search_term))
            ).order_by(desc(ChatConversation.last_activity)).limit(limit).all()
            
        except SQLAlchemyError as e:
            print(f"Database error searching conversations: {e}")
            self._rollback_safe()
            return []
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []
    
    def _rollback_safe(self):
        """Safely rollback transaction"""
        try:
            self.db.rollback()
        except Exception as rollback_error:
            print(f"Error during rollback: {rollback_error}")
    
    def _is_transaction_aborted(self) -> bool:
        """Check if the current transaction is in an aborted state"""
        try:
            self.db.execute(text("SELECT 1")).fetchone()
            return False
        except SQLAlchemyError as e:
            error_msg = str(e).lower()
            return "current transaction is aborted" in error_msg or "failed sql transaction" in error_msg
        except Exception:
            return True
    
    def ensure_transaction_health(self):
        """Ensure transaction is in a healthy state"""
        try:
            if self._is_transaction_aborted():
                print("Detected aborted transaction, rolling back")
                self.db.rollback()
        except Exception as e:
            print(f"Error ensuring transaction health: {e}")