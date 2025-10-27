# handlers/fee/handler.py - Intent-first refactor
from typing import Dict, Optional
from ...base import BaseHandler, ChatResponse
from .service import FeeService
from .flows.fee_update import FeeUpdateFlow

class FeeHandler(BaseHandler):
    """Intent-first fee handler"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = FeeService(db, school_id, self.get_school_name)
        self.fee_update_flow = FeeUpdateFlow(db, school_id, user_id)
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle fee operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'fee_structure', 'fee_update')
            message: Original user message
            entities: Extracted entities (grade_name, fee_amount, etc.)
            context: Conversation context including flows
        """
        # Handle context flows first (multi-step processes)
        if context.get('flow') == 'update_fee':
            return self.fee_update_flow.handle_flow(message, context)
        
        # Route based on intent
        if intent == 'fee_structure':
            return self.service.show_fee_structures()
        
        elif intent == 'fee_overview':
            return self.service.show_comprehensive_overview()
        
        elif intent == 'fee_grade_specific':
            # Use entities if available for grade lookup
            if entities.get('grade_name'):
                return self.service.show_grade_fees(entities['grade_name'])
            else:
                # Extract from message as fallback
                return self._handle_grade_fees(message)
        
        elif intent == 'fee_update':
            return self.fee_update_flow.initiate_update(message)
        
        elif intent == 'fee_items':
            return self.service.show_fee_items()
        
        elif intent == 'fee_student_invoice':
            # Use entities if available for student lookup
            if entities.get('admission_no'):
                return self.service.show_student_invoice(entities['admission_no'])
            else:
                # Extract from message as fallback
                return self._handle_student_invoice(message)
        
        else:
            # Default to system overview for unknown intents
            return self.service.show_system_overview()
    
    def _handle_grade_fees(self, message: str) -> ChatResponse:
        """Handle grade-specific fee queries - fallback extraction"""
        grade_name = self.service.extract_grade_from_message(message)
        
        if not grade_name:
            return ChatResponse(
                response="Please specify which grade you'd like to see fees for",
                intent="grade_not_specified",
                suggestions=["Show all fee structures", "Fees overview", "Update fee amounts"]
            )
        
        return self.service.show_grade_fees(grade_name)
    
    def _handle_student_invoice(self, message: str) -> ChatResponse:
        """Handle student invoice queries - fallback extraction"""
        admission_no = self.service.extract_student_from_message(message)
        
        if not admission_no:
            return ChatResponse(
                response="Please specify which student's invoice you'd like to see",
                intent="student_not_specified",
                suggestions=["Show pending invoices", "List enrolled students", "Generate invoices"]
            )
        
        return self.service.show_student_invoice(admission_no)