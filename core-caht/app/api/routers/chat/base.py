# app/api/routers/chat/base.py - Fixed with proper UUID handling
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid

# Pydantic models for chat
class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    action_taken: Optional[str] = None
    suggestions: Optional[List[str]] = None
    conversation_id: Optional[str] = None
    
    class Config:
        extra = "allow"

def db_execute_safe(db: Session, query: str, params: dict = None):
    """Safely execute a database query and return results with UUID handling"""
    try:
        # Convert UUID objects to strings in parameters
        safe_params = {}
        if params:
            for key, value in params.items():
                if isinstance(value, uuid.UUID):
                    safe_params[key] = str(value)
                else:
                    safe_params[key] = value
        
        result = db.execute(text(query), safe_params or {})
        return result.fetchall()
    except Exception as e:
        print(f"Database query error: {e}")
        print(f"Query: {query}")
        print(f"Params: {params}")
        # Check if transaction is aborted
        if "current transaction is aborted" in str(e).lower():
            print("Transaction aborted, rolling back")
            try:
                db.rollback()
            except:
                pass
        raise

def db_execute_non_select(db: Session, query: str, params: dict = None):
    """Execute non-SELECT queries with UUID handling"""
    try:
        # Convert UUID objects to strings in parameters
        safe_params = {}
        if params:
            for key, value in params.items():
                if isinstance(value, uuid.UUID):
                    safe_params[key] = str(value)
                else:
                    safe_params[key] = value
        
        result = db.execute(text(query), safe_params or {})
        return result.rowcount
    except Exception as e:
        print(f"Database query error: {e}")
        print(f"Query: {query}")
        print(f"Params: {params}")
        # Check if transaction is aborted
        if "current transaction is aborted" in str(e).lower():
            print("Transaction aborted, rolling back")
            try:
                db.rollback()
            except:
                pass
        raise

def safe_uuid_cast(value: Any) -> str:
    """Safely convert any value to UUID string"""
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, str):
        # Validate it's a proper UUID format
        try:
            uuid.UUID(value)
            return value
        except ValueError:
            raise ValueError(f"Invalid UUID format: {value}")
    raise TypeError(f"Cannot convert {type(value)} to UUID: {value}")

class BaseHandler:
    """Base class for all chat handlers with improved UUID handling"""
    
    def __init__(self, db: Session, school_id: str, user_id: str):
        self.db = db
        # Ensure IDs are strings
        self.school_id = safe_uuid_cast(school_id)
        self.user_id = safe_uuid_cast(user_id)
    
    def get_school_name(self) -> str:
        """Get school name for responses - FIXED UUID casting"""
        try:
            # FIXED: Remove ::uuid casting, let SQLAlchemy handle it
            result = db_execute_safe(self.db, 
                "SELECT name FROM schools WHERE id = :school_id",
                {"school_id": self.school_id}
            )
            return result[0][0] if result else "Your School"
        except Exception as e:
            print(f"Error getting school name: {e}")
            return "Your School"
    
    def ensure_transaction_health(self):
        """Ensure database transaction is in good state"""
        try:
            # Test transaction state
            self.db.execute(text("SELECT 1")).fetchone()
        except Exception as e:
            error_msg = str(e).lower()
            if "current transaction is aborted" in error_msg:
                print("Detected aborted transaction, rolling back")
                try:
                    self.db.rollback()
                except:
                    pass
    
    def can_handle(self, message: str) -> bool:
        """Override in subclasses"""
        raise NotImplementedError
    
    def handle(self, message: str, context: Optional[Dict] = None) -> ChatResponse:
        """Override in subclasses"""
        raise NotImplementedError