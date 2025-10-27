# handlers/academic/handler.py - Intent-first refactor
from typing import Optional, Dict
from ...base import BaseHandler, ChatResponse
from .service import AcademicService

class AcademicHandler(BaseHandler):
    """Intent-first academic handler"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = AcademicService(db, school_id, self.get_school_name)
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle academic operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'academic_current_term', 'academic_calendar')
            message: Original user message
            entities: Extracted entities (term_name, year, etc.)
            context: Conversation context including flows
        """
        # Handle context flows first (multi-step processes)
        if context.get('handler') == 'academic' and context.get('step'):
            return self._handle_context_flow(message, context)
        
        # Route based on intent
        if intent == 'academic_current_term':
            return self.service.get_current_term()
        
        elif intent == 'academic_activate_term':
            return self.service.initiate_term_activation(message)
        
        elif intent == 'academic_calendar':
            return self.service.get_academic_calendar()
        
        elif intent == 'academic_setup':
            return self.service.get_setup_status()
        
        elif intent == 'academic_overview':
            return self.service.get_overview()
        
        else:
            # Default to overview for unknown intents
            return self.service.get_overview()
    
    def _handle_context_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle multi-step context flows"""
        flow = context.get('flow')
        step = context.get('step')
        
        print(f"Academic context flow: {flow}, step: {step}")
        
        if flow == 'activate_term':
            if step == 'confirm_switch':
                return self.service.handle_switch_confirmation(message, context)
            elif step == 'select_term':
                return self.service.handle_term_selection(message, context)
        
        return self.service.get_overview()