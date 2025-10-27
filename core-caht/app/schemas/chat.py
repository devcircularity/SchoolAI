# app/schemas/chat.py - Fixed with proper JSON serialization

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid
import json

# Import block types
from app.schemas.blocks import Block

class FileAttachment(BaseModel):
    """File attachment metadata"""
    attachment_id: str
    original_filename: str
    content_type: str
    file_size: int
    cloudinary_url: str
    cloudinary_public_id: str
    upload_timestamp: str  # Changed from datetime to str for JSON serialization
    ocr_processed: bool = False
    ocr_data: Optional[Dict[str, Any]] = None
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Override dict method to ensure proper serialization"""
        result = super().dict(**kwargs)
        # Ensure upload_timestamp is a string
        if isinstance(result.get('upload_timestamp'), datetime):
            result['upload_timestamp'] = result['upload_timestamp'].isoformat()
        return result

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    attachments: Optional[List[FileAttachment]] = None

class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    action_taken: Optional[str] = None
    suggestions: Optional[List[str]] = None
    conversation_id: Optional[str] = None
    blocks: Optional[List[Block]] = None
    attachment_processed: Optional[bool] = None
    message_id: Optional[str] = None  # ADD THIS LINE
    
    class Config:
        extra = "allow"

class ChatSuggestion(BaseModel):
    text: str
    intent: Optional[str] = None

class ChatContext(BaseModel):
    user_id: str
    school_id: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None

class ConversationCreate(BaseModel):
    title: str
    first_message: str

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    first_message: str
    last_activity: datetime
    message_count: int
    is_archived: bool
    created_at: datetime
    
    @classmethod
    def from_attributes(cls, obj):
        """Convert SQLAlchemy object to Pydantic model"""
        return cls(
            id=str(obj.id),
            title=obj.title,
            first_message=obj.first_message,
            last_activity=obj.last_activity,
            message_count=obj.message_count,
            is_archived=obj.is_archived,
            created_at=obj.created_at
        )

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    conversation_id: str
    message_type: str  # 'USER' or 'ASSISTANT'
    content: str
    intent: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime
    attachments: Optional[List[FileAttachment]] = None
    
    @classmethod
    def from_attributes(cls, obj):
        """Convert SQLAlchemy object to Pydantic model with proper message_type"""
        print(f"MessageResponse.from_attributes - Raw message_type: {obj.message_type}")
        print(f"MessageResponse.from_attributes - Type of message_type: {type(obj.message_type)}")
        
        # Handle enum properly
        if hasattr(obj.message_type, 'value'):
            message_type_str = obj.message_type.value
            print(f"MessageResponse.from_attributes - Enum value: {message_type_str}")
        else:
            message_type_str = str(obj.message_type)
            print(f"MessageResponse.from_attributes - String value: {message_type_str}")
        
        # Ensure we return exactly 'USER' or 'ASSISTANT'
        if message_type_str == 'MessageType.USER' or message_type_str.endswith('.USER'):
            message_type_str = 'USER'
        elif message_type_str == 'MessageType.ASSISTANT' or message_type_str.endswith('.ASSISTANT'):
            message_type_str = 'ASSISTANT'
        elif message_type_str.upper() == 'USER':
            message_type_str = 'USER'
        elif message_type_str.upper() == 'ASSISTANT':
            message_type_str = 'ASSISTANT'
        
        print(f"MessageResponse.from_attributes - Final message_type: {message_type_str}")
        
        # Parse attachments from response_data if present
        attachments = None
        if obj.response_data and 'attachments' in obj.response_data:
            try:
                attachments = []
                for attachment_data in obj.response_data['attachments']:
                    # Ensure upload_timestamp is a string
                    if 'upload_timestamp' in attachment_data:
                        if isinstance(attachment_data['upload_timestamp'], datetime):
                            attachment_data['upload_timestamp'] = attachment_data['upload_timestamp'].isoformat()
                    attachments.append(FileAttachment(**attachment_data))
            except Exception as e:
                print(f"Error parsing attachments from response_data: {e}")
        
        return cls(
            id=str(obj.id),
            conversation_id=str(obj.conversation_id),
            message_type=message_type_str,
            content=obj.content,
            intent=obj.intent,
            context_data=obj.context_data,
            response_data=obj.response_data,
            processing_time_ms=obj.processing_time_ms,
            created_at=obj.created_at,
            attachments=attachments
        )

class ConversationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    first_message: str
    last_activity: datetime
    message_count: int
    is_archived: bool
    created_at: datetime
    messages: List[MessageResponse] = []
    
    @classmethod
    def from_attributes(cls, obj):
        """Convert SQLAlchemy object to Pydantic model"""
        return cls(
            id=str(obj.id),
            title=obj.title,
            first_message=obj.first_message,
            last_activity=obj.last_activity,
            message_count=obj.message_count,
            is_archived=obj.is_archived,
            created_at=obj.created_at,
            messages=[]
        )

class ConversationList(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    page: int = 1
    limit: int = 20
    has_next: bool = False

class UpdateConversation(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None

# Utility function to ensure datetime objects are converted to ISO strings for JSON storage
def prepare_for_json_storage(data: Any) -> Any:
    """
    Recursively convert datetime objects to ISO string format for JSON storage
    """
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: prepare_for_json_storage(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [prepare_for_json_storage(item) for item in data]
    elif hasattr(data, 'dict') and callable(data.dict):
        # Handle Pydantic models
        return prepare_for_json_storage(data.dict())
    else:
        return data