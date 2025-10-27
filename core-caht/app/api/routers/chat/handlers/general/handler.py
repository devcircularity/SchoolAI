# handlers/general/handler.py - Intent-first refactor
from typing import Dict, Optional
from ...base import BaseHandler, ChatResponse
from .service import GeneralService

class GeneralHandler(BaseHandler):
    """Intent-first general handler for system queries and guidance"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = GeneralService(db, school_id, self.get_school_name)
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle general operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'greeting', 'help', 'getting_started')
            message: Original user message
            entities: Extracted entities
            context: Conversation context
        """
        # Route based on intent
        if intent == 'greeting':
            return self.service.handle_greeting(message)
        
        elif intent == 'school_registration':
            return self.service.handle_school_registration_query(message)
        
        elif intent == 'getting_started':
            return self.service.handle_getting_started()
        
        elif intent == 'system_capabilities':
            return self.service.handle_system_capabilities()
        
        elif intent == 'help':
            return self.service.handle_help_request(message)
        
        elif intent == 'next_steps':
            return self.service.handle_next_steps_guidance()
        
        elif intent == 'school_management':
            return self.service.handle_general_intent(message)
        
        elif intent == 'casual_conversation':
            return self.service.handle_greeting(message)  # Treat like greeting
        
        elif intent == 'system_introduction':
            return self.service.handle_system_capabilities()  # Treat like capabilities
        
        else:
            # Default to general assistance for unknown intents
            return self.service.handle_general_intent(message)