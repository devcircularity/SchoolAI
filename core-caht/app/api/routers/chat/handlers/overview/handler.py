# handlers/overview/handler.py - Intent-first refactor
from typing import Optional, Dict
from ...base import BaseHandler, ChatResponse
from .service import OverviewService

class OverviewHandler(BaseHandler):
    """Intent-first overview handler"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = OverviewService(db, school_id, self.get_school_name)
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle overview operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'school_overview', 'dashboard')
            message: Original user message
            entities: Extracted entities
            context: Conversation context
        """
        # All overview intents map to the same comprehensive overview
        if intent in ['school_overview', 'dashboard', 'school_summary', 'school_stats']:
            return self.service.get_school_overview()
        
        else:
            # Default to overview for unknown intents
            return self.service.get_school_overview()