# handlers/invoice/handler.py - Intent-first refactor
from typing import Dict, Optional
from ...base import BaseHandler, ChatResponse
from .service import InvoiceService

class InvoiceHandler(BaseHandler):
    """Intent-first invoice handler"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = InvoiceService(db, school_id, self.get_school_name)
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle invoice operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'invoice_generate_student', 'invoice_pending')
            message: Original user message
            entities: Extracted entities (student_name, admission_no, etc.)
            context: Conversation context
        """
        # Route based on intent
        if intent == 'invoice_generate_student':
            return self.service.generate_student_invoice(message)
        
        elif intent == 'invoice_generate_bulk':
            return self.service.generate_bulk_invoices()
        
        elif intent == 'invoice_pending':
            return self.service.show_pending_invoices()
        
        elif intent == 'invoice_show_student':
            # Use entities if available for specific student lookup
            return self.service.show_student_invoice(message)
        
        elif intent == 'invoice_list':
            return self.service.show_pending_invoices()  # Default to pending
        
        elif intent == 'invoice_overview':
            return self.service.show_overview()
        
        else:
            # Default to overview for unknown intents
            return self.service.show_overview()