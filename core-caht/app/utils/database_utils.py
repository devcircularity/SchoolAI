# app/utils/database_utils.py - Robust database utilities
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

class DatabaseUtils:
    """Utilities for robust database operations with UUID handling"""
    
    @staticmethod
    def safe_uuid_convert(value: Any) -> str:
        """Safely convert any value to UUID string"""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, str):
            try:
                # Validate UUID format
                uuid.UUID(value)
                return value
            except ValueError:
                raise ValueError(f"Invalid UUID format: {value}")
        raise TypeError(f"Cannot convert {type(value)} to UUID: {value}")
    
    @staticmethod
    def prepare_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for database queries, handling UUIDs"""
        safe_params = {}
        for key, value in params.items():
            if isinstance(value, uuid.UUID):
                safe_params[key] = str(value)
            else:
                safe_params[key] = value
        return safe_params
    
    @staticmethod
    def execute_with_fallback(
        db: Session, 
        query_text: str, 
        params: Dict[str, Any], 
        description: str = "query"
    ) -> List:
        """Execute database query with multiple fallback strategies for UUID issues"""
        
        # Strategy 1: Direct parameter substitution
        try:
            safe_params = DatabaseUtils.prepare_params(params)
            result = db.execute(text(query_text), safe_params)
            return result.fetchall()
        except SQLAlchemyError as e:
            print(f"Strategy 1 failed for {description}: {e}")
            
            # Strategy 2: Add explicit UUID casting to query
            try:
                db.rollback()
                # Modify query to add ::uuid casting where needed
                modified_query = DatabaseUtils._add_uuid_casting(query_text)
                result = db.execute(text(modified_query), safe_params)
                return result.fetchall()
            except SQLAlchemyError as e2:
                print(f"Strategy 2 failed for {description}: {e2}")
                
                # Strategy 3: Convert columns to text for comparison
                try:
                    db.rollback()
                    text_query = DatabaseUtils._modify_for_text_comparison(query_text)
                    result = db.execute(text(text_query), safe_params)
                    return result.fetchall()
                except SQLAlchemyError as e3:
                    print(f"All strategies failed for {description}: {e3}")
                    db.rollback()
                    return []
    
    @staticmethod
    def _add_uuid_casting(query: str) -> str:
        """Add UUID casting to query parameters"""
        # Simple approach: add ::uuid to common UUID parameter patterns
        import re
        # Replace :param_name with :param_name::uuid for known UUID params
        uuid_params = ['school_id', 'user_id', 'class_id', 'student_id', 'conversation_id']
        for param in uuid_params:
            pattern = f":{param}(?!::)"  # Match :param but not :param::
            replacement = f":{param}::uuid"
            query = re.sub(pattern, replacement, query)
        return query
    
    @staticmethod
    def _modify_for_text_comparison(query: str) -> str:
        """Modify query to use text comparison for UUID columns"""
        import re
        # Replace column = :param with column::text = :param
        uuid_columns = ['school_id', 'user_id', 'class_id', 'student_id', 'conversation_id']
        for column in uuid_columns:
            # Match patterns like "WHERE school_id = :school_id"
            pattern = f"{column}\\s*=\\s*:{column}"
            replacement = f"{column}::text = :{column}"
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        return query
    
    @staticmethod
    def execute_non_select_with_fallback(
        db: Session,
        query_text: str,
        params: Dict[str, Any],
        description: str = "update"
    ) -> int:
        """Execute non-SELECT queries with fallback strategies"""
        try:
            safe_params = DatabaseUtils.prepare_params(params)
            result = db.execute(text(query_text), safe_params)
            return result.rowcount
        except SQLAlchemyError as e:
            print(f"Non-select {description} failed: {e}")
            try:
                db.rollback()
                # Try with UUID casting
                modified_query = DatabaseUtils._add_uuid_casting(query_text)
                result = db.execute(text(modified_query), safe_params)
                return result.rowcount
            except SQLAlchemyError as e2:
                print(f"Fallback non-select {description} failed: {e2}")
                db.rollback()
                return 0

class TransactionManager:
    """Context manager for robust transaction handling"""
    
    def __init__(self, db: Session, description: str = "operation"):
        self.db = db
        self.description = description
        
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                self.db.commit()
            except SQLAlchemyError as e:
                print(f"Commit failed for {self.description}: {e}")
                self.db.rollback()
                raise
        else:
            print(f"Exception in {self.description}: {exc_val}")
            try:
                self.db.rollback()
            except SQLAlchemyError as rollback_error:
                print(f"Rollback failed: {rollback_error}")

# Usage examples:
"""
# In your handlers:
from app.utils.database_utils import DatabaseUtils, TransactionManager

# Safe query execution
grades = DatabaseUtils.execute_with_fallback(
    self.db,
    "SELECT id, label, group_name FROM cbc_level WHERE school_id = :school_id ORDER BY group_name, label",
    {"school_id": self.school_id},
    "get_grades"
)

# Safe transaction handling
with TransactionManager(self.db, "create_class"):
    class_id = str(uuid.uuid4())
    DatabaseUtils.execute_non_select_with_fallback(
        self.db,
        "INSERT INTO classes (id, school_id, name, level) VALUES (:id, :school_id, :name, :level)",
        {"id": class_id, "school_id": self.school_id, "name": class_name, "level": grade_level},
        "create_class"
    )
"""