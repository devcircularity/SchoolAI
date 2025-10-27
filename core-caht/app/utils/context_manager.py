# app/api/routers/chat/utils/context_manager.py - Enhanced context preservation
from typing import Dict, Any, Optional, Callable
from ..base import ChatResponse

class FlowContextManager:
    """Manages conversation flow context with robust error handling"""
    
    @staticmethod
    def preserve_context_on_error(
        context: Dict[str, Any],
        error_message: str,
        recovery_suggestions: list = None
    ) -> ChatResponse:
        """Create error response while preserving context for recovery"""
        
        default_suggestions = [
            "Try again",
            "Start over",
            "Show available options", 
            "Cancel"
        ]
        
        suggestions = recovery_suggestions or default_suggestions
        
        return ChatResponse(
            response=f"I encountered an issue: {error_message}\n\n"
                     "Don't worry, I remember where we were. What would you like to do?",
            intent="flow_error_with_context",
            data={"context": context},
            suggestions=suggestions
        )
    
    @staticmethod
    def execute_with_context_preservation(
        flow_method: Callable,
        message: str,
        context: Dict[str, Any],
        fallback_message: str = "Let's continue with what we were doing"
    ) -> ChatResponse:
        """Execute flow method with automatic context preservation on error"""
        
        try:
            return flow_method(message, context)
        except Exception as e:
            print(f"Flow execution error: {e}")
            
            # Determine appropriate recovery suggestions based on context
            suggestions = FlowContextManager._get_context_appropriate_suggestions(context)
            
            return FlowContextManager.preserve_context_on_error(
                context=context,
                error_message=f"Technical issue occurred. {fallback_message}",
                recovery_suggestions=suggestions
            )
    
    @staticmethod
    def _get_context_appropriate_suggestions(context: Dict[str, Any]) -> list:
        """Get contextually appropriate suggestions based on current flow state"""
        
        flow = context.get('flow', '')
        step = context.get('step', '')
        
        if flow == 'create_class':
            if step == 'select_grade':
                return ["Show available grades", "Create new grade", "Try again", "Cancel"]
            elif step == 'enter_class_name':
                return ["Try different name", "Go back to grade selection", "Cancel"]
            elif step == 'confirm_creation':
                return ["Yes, create it", "Change details", "Cancel"]
                
        elif flow == 'create_grade':
            if step == 'enter_grade_name':
                return ["Try again", "Show examples", "Cancel"]
            elif step == 'select_grade_group':
                return ["Show grade groups", "Try again", "Cancel"]
                
        # Default suggestions
        return ["Try again", "Start over", "Show available options", "Cancel"]
    
    @staticmethod
    def validate_context_integrity(context: Dict[str, Any]) -> tuple[bool, str]:
        """Validate that context has required fields for the current step"""
        
        if not isinstance(context, dict):
            return False, "Context must be a dictionary"
        
        required_fields = ['handler', 'flow', 'step']
        missing_fields = [field for field in required_fields if field not in context]
        
        if missing_fields:
            return False, f"Missing required context fields: {', '.join(missing_fields)}"
        
        # Validate specific flow requirements
        flow = context.get('flow')
        step = context.get('step')
        
        if flow == 'create_class':
            if step == 'enter_class_name' and 'selected_grade' not in context:
                return False, "Missing selected_grade for class name entry"
            elif step == 'confirm_creation' and 'class_name' not in context:
                return False, "Missing class_name for confirmation"
                
        elif flow == 'create_grade':
            if step == 'select_grade_group' and 'grade_name' not in context:
                return False, "Missing grade_name for group selection"
            elif step == 'confirm_grade_creation' and 'selected_group' not in context:
                return False, "Missing selected_group for confirmation"
        
        return True, "Context is valid"
    
    @staticmethod
    def repair_context(context: Dict[str, Any], handler_instance) -> Dict[str, Any]:
        """Attempt to repair broken context by fetching missing data"""
        
        repaired_context = context.copy()
        
        try:
            # If we're missing grades data in class creation, fetch it
            if (context.get('flow') == 'create_class' and 
                context.get('step') == 'select_grade' and 
                'grades' not in context):
                
                grades = handler_instance._get_available_grades()
                if grades:
                    repaired_context['grades'] = grades
                    repaired_context['grade_options'] = [
                        f"{grade['label']} ({grade['group_name']})" for grade in grades
                    ]
                    repaired_context['grade_options'].append("Create new grade")
            
        except Exception as e:
            print(f"Context repair failed: {e}")
        
        return repaired_context

# Decorator for automatic context preservation
def with_context_preservation(fallback_message: str = "Let's continue"):
    """Decorator to automatically preserve context on method errors"""
    def decorator(method):
        def wrapper(self, message: str, context: Dict[str, Any]) -> ChatResponse:
            return FlowContextManager.execute_with_context_preservation(
                lambda msg, ctx: method(self, msg, ctx),
                message,
                context,
                fallback_message
            )
        return wrapper
    return decorator

# Usage in your flow classes:
"""
from .utils.context_manager import with_context_preservation, FlowContextManager

class ClassCreationFlow:
    @with_context_preservation("Let's continue creating your class")
    def _process_grade_selection(self, message: str, context: Dict) -> ChatResponse:
        # Your existing logic here
        pass
        
    def handle_flow(self, message: str, context: Dict) -> ChatResponse:
        # Validate context first
        is_valid, error_msg = FlowContextManager.validate_context_integrity(context)
        if not is_valid:
            print(f"Context validation failed: {error_msg}")
            context = FlowContextManager.repair_context(context, self)
        
        # Continue with normal flow handling
        step = context.get('step')
        if step == 'select_grade':
            return self._process_grade_selection(message, context)
        # ... rest of your logic
"""