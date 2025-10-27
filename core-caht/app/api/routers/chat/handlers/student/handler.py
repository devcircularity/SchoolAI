# handlers/student/handler.py - Intent-first refactor
from typing import Dict, Optional
from ...base import BaseHandler, ChatResponse
from .service import StudentService
from .flows.student_creation import StudentCreationFlow

class StudentHandler(BaseHandler):
    """Intent-first student handler"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = StudentService(db, school_id, self.get_school_name)
        self.student_creation_flow = StudentCreationFlow(db, school_id, user_id)
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle student operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'student_create', 'student_search')
            message: Original user message
            entities: Extracted entities (admission_no, student_name, etc.)
            context: Conversation context including flows
        """
        # Handle context flows first (multi-step processes)
        if context.get('flow') == 'create_student':
            return self.student_creation_flow.handle_flow(message, context)
        
        # Route based on intent
        if intent == 'student_create':
            return self.student_creation_flow.initiate_creation(message)
        
        elif intent == 'student_search':
            # Use entities to determine search type
            if entities.get('admission_no'):
                return self.service.search_by_admission(entities['admission_no'])
            elif entities.get('student_name'):
                return self.service.search_by_name(entities['student_name'])
            else:
                # Fallback - try to extract from message
                return self._handle_fallback_search(message)
        
        elif intent == 'student_list':
            return self.service.list_students()
        
        elif intent == 'unassigned_students':
            return self.service.show_unassigned()
        
        elif intent == 'student_count':
            return self.service.show_count()
        
        else:
            # Default to overview for unknown intents
            return self.service.show_overview()
    
    def _handle_fallback_search(self, message: str) -> ChatResponse:
        """Fallback search when entities aren't clear"""
        import re
        
        # Try to extract admission number
        admission_match = re.search(r'(\d{3,7})', message)
        if admission_match:
            return self.service.search_by_admission(admission_match.group(1))
        
        # Try to extract name patterns
        name_patterns = [
            r'find.*student\s+([a-zA-Z\s]+)',
            r'search.*student\s+([a-zA-Z\s]+)',
            r'show.*student\s+([a-zA-Z\s]+)',
            r'student\s+([a-zA-Z\s]+)\s+details'
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, message.lower())
            if name_match:
                name = name_match.group(1).strip()
                if len(name) >= 3:
                    return self.service.search_by_name(name)
        
        # If nothing found, guide user
        return ChatResponse(
            response="Please specify either an admission number (e.g., 'show student 4444') or student name (e.g., 'find student Mary Kimani').",
            intent="student_search_unclear",
            suggestions=["Show student 4444", "Find student Mary Kimani", "List all students"]
        )