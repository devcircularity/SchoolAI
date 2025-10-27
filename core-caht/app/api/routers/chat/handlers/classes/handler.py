# handlers/class/handler.py - Intent-first refactor
from typing import Dict, Optional
from ...base import BaseHandler, ChatResponse
from .service import ClassService
from .flows.class_creation import ClassCreationFlow
from .flows.grade_creation import GradeCreationFlow

class ClassHandler(BaseHandler):
    """Intent-first class handler"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = ClassService(db, school_id, self.get_school_name)
        
        # Initialize flow handlers with error handling
        try:
            self.class_creation_flow = ClassCreationFlow(db, school_id, user_id)
            self.grade_creation_flow = GradeCreationFlow(db, school_id, user_id)
        except ImportError as e:
            print(f"Warning: Could not import flow handlers: {e}")
            self.class_creation_flow = None
            self.grade_creation_flow = None
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle class operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'class_create', 'class_list')
            message: Original user message
            entities: Extracted entities (class_name, grade_level, etc.)
            context: Conversation context including flows
        """
        # Handle context flows first (multi-step processes)
        if self._has_active_context(context):
            print(f"Active context detected: {context}")
            return self._handle_context_flow(message, context)
        
        # Route based on intent
        if intent == 'class_create':
            if self.class_creation_flow:
                return self.class_creation_flow.initiate_creation()
            else:
                return self._fallback_class_creation()
        
        elif intent == 'grade_create':
            if self.grade_creation_flow:
                return self.grade_creation_flow.initiate_creation()
            else:
                return self._fallback_grade_creation()
        
        elif intent == 'class_details':
            # Use entities if available for class lookup
            if entities.get('class_name'):
                return self.service.show_class_details(entities['class_name'])
            else:
                # Extract from message as fallback
                return self._handle_class_details(message)
        
        elif intent == 'grade_list':
            return self.service.list_grades()
        
        elif intent == 'class_list':
            return self.service.list_classes()
        
        elif intent == 'class_count':
            return self.service.show_class_statistics()
        
        elif intent == 'class_empty':
            return self.service.show_empty_classes()
        
        else:
            # Default to overview for unknown intents
            return self.service.show_overview()
    
    def _has_active_context(self, context):
        """Check if context indicates an active flow"""
        return (context.get('handler') == 'class' and 
                context.get('flow') in ['create_class', 'create_grade'] and
                context.get('step'))
    
    def _handle_context_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle multi-step context flows"""
        flow = context.get('flow')
        
        print(f"Handling context flow: {flow} with step: {context.get('step')}")
        
        try:
            if flow == 'create_class':
                if self.class_creation_flow:
                    return self.class_creation_flow.handle_flow(message, context)
                else:
                    return self._fallback_class_creation_flow(message, context)
            elif flow == 'create_grade':
                if self.grade_creation_flow:
                    return self.grade_creation_flow.handle_flow(message, context)
                else:
                    return self._fallback_grade_creation_flow(message, context)
            else:
                print(f"Unknown flow: {flow}, falling back")
                return self.service.show_overview()
        except Exception as e:
            print(f"Context flow error: {e}")
            return self._create_error_recovery_response(context, str(e))
    
    def _handle_class_details(self, message: str) -> ChatResponse:
        """Handle class details requests with name extraction - fallback"""
        class_name = self._extract_class_name(message)
        if class_name:
            return self.service.show_class_details(class_name)
        else:
            return ChatResponse(
                response="Please specify which class you'd like to see details for.",
                intent="class_details_missing_name",
                suggestions=[
                    "List all classes", 
                    "Show class 10 A details", 
                    "Show Grade 2 Blue details",
                    "Class statistics"
                ]
            )
    
    def _extract_class_name(self, message: str) -> str:
        """Extract class name from message like 'show class 10 A details'"""
        import re
        patterns = [
            r'show.*class\s+([^\d]+?)(?:\s+detail|$)',   # "show class 10 A details"
            r'class\s+([^\d]+?)\s+detail',               # "class 10 A details"
            r'details.*class\s+(.+)',                    # "details for class 10 A"
            r'view.*class\s+(.+)',                       # "view class 10 A"
            r'info.*class\s+(.+)',                       # "info for class 10 A"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                class_name = match.group(1).strip()
                # Clean up common words that might be captured
                class_name = re.sub(r'\b(for|of|about)\b', '', class_name).strip()
                return class_name
        
        return ""
    
    def _fallback_class_creation(self) -> ChatResponse:
        """Simple class creation without flow handler"""
        return ChatResponse(
            response="I'll help you create a new class. What grade level is this class for?",
            intent="class_creation_grade_selection",
            data={
                "context": {
                    "handler": "class",
                    "flow": "create_class",
                    "step": "select_grade"
                }
            },
            suggestions=["Grade 1", "PP1", "Form 1", "Show available grades", "Cancel"]
        )
    
    def _fallback_grade_creation(self) -> ChatResponse:
        """Simple grade creation without flow handler"""
        return ChatResponse(
            response="I'll help you create a new grade level. What would you like to name this grade?",
            intent="grade_creation_name_input",
            data={
                "context": {
                    "handler": "class",
                    "flow": "create_grade",
                    "step": "enter_grade_name"
                }
            },
            suggestions=["Grade 1", "PP1", "Form 1", "Nursery", "Cancel"]
        )
    
    def _fallback_class_creation_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle simple class creation flow without complex flow handler"""
        step = context.get('step')
        
        if step == 'select_grade':
            # User selected a grade, now ask for class name
            available_grades = context.get('grades', [])
            selected_grade = self._extract_grade_from_message(message, available_grades)
            if selected_grade:
                return ChatResponse(
                    response=f"Creating a class for {selected_grade['label']}. What should we name this class?",
                    intent="class_creation_name_input",
                    data={
                        "context": {
                            "handler": "class",
                            "flow": "create_class",
                            "step": "enter_class_name",
                            "selected_grade": selected_grade
                        }
                    },
                    suggestions=[
                        f"{selected_grade['label']} A",
                        f"{selected_grade['label']} East", 
                        f"{selected_grade['label']} Red",
                        "Cancel"
                    ]
                )
            else:
                return ChatResponse(
                    response="I didn't catch which grade you selected. Please try again.",
                    intent="grade_selection_unclear",
                    suggestions=["List grades", "Try again", "Cancel"]
                )
        
        elif step == 'enter_class_name':
            # User provided class name, create the class
            return self._create_class_with_details(message, context)
        
        return self.service.show_overview()
    
    def _fallback_grade_creation_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle simple grade creation flow without complex flow handler"""
        step = context.get('step')
        
        if step == 'enter_grade_name':
            # User provided grade name, ask for grade group
            grade_name = message.strip()
            if len(grade_name) < 2:
                return ChatResponse(
                    response="Grade name seems too short. Please provide a proper grade name.",
                    intent="grade_name_too_short",
                    suggestions=["Grade 1", "PP1", "Form 1", "Try again", "Cancel"]
                )
            
            return ChatResponse(
                response=f"Creating grade '{grade_name}'. Which grade group should this belong to?",
                intent="grade_creation_group_selection",
                data={
                    "context": {
                        "handler": "class",
                        "flow": "create_grade",
                        "step": "select_grade_group",
                        "grade_name": grade_name
                    }
                },
                suggestions=[
                    "Pre-Primary",
                    "Primary", 
                    "Secondary",
                    "Other",
                    "Cancel"
                ]
            )
        
        elif step == 'select_grade_group':
            # User selected group, create the grade
            return self._create_grade_with_details(message, context)
        
        return self.service.show_overview()
    
    def _extract_grade_from_message(self, message: str, available_grades) -> Optional[Dict]:
        """Extract selected grade from user message"""
        message_lower = message.lower()
        
        # Try exact match first
        for grade in available_grades:
            if grade['label'].lower() == message_lower:
                return grade
        
        # Try partial match
        for grade in available_grades:
            if grade['label'].lower() in message_lower or message_lower in grade['label'].lower():
                return grade
        
        return None
    
    def _create_class_with_details(self, message: str, context: Dict) -> ChatResponse:
        """Create a class with the provided details"""
        from ...base import db_execute_safe
        from datetime import datetime
        import uuid
        
        selected_grade = context.get('selected_grade')
        class_name = message.strip()
        
        if not selected_grade or not class_name:
            return ChatResponse(
                response="Missing required information to create the class.",
                intent="class_creation_missing_info",
                suggestions=["Start over", "Cancel", "List grades"]
            )
        
        try:
            # Check if class name already exists
            existing_class = self.service.repo.check_class_exists(class_name)
            
            if existing_class:
                return ChatResponse(
                    response=f"A class named '{class_name}' already exists. Please choose a different name.",
                    intent="class_name_already_exists",
                    suggestions=[
                        f"{class_name} A",
                        f"{class_name} 2", 
                        "Try different name",
                        "Cancel"
                    ]
                )
            
            # Create the class
            class_id = str(uuid.uuid4())
            current_year = self.service.repo.get_current_academic_year() or datetime.now().year
            
            rows_affected = db_execute_safe(self.db, """
                INSERT INTO classes (id, school_id, name, level, academic_year, created_at, updated_at)
                VALUES (:id, :school_id, :name, :level, :academic_year, :created_at, :updated_at)
            """, {
                "id": class_id,
                "school_id": self.school_id,
                "name": class_name,
                "level": selected_grade['label'],
                "academic_year": current_year,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            if rows_affected:
                self.db.commit()
                
                return ChatResponse(
                    response=f"Successfully created class '{class_name}' for {selected_grade['label']}!",
                    intent="class_created_successfully",
                    data={"context": {}},  # Clear context
                    suggestions=[
                        f"Assign students to {class_name}",
                        "List all classes",
                        "Create another class",
                        "Show class details"
                    ]
                )
            else:
                return ChatResponse(
                    response="Failed to create class. Please try again.",
                    intent="class_creation_failed",
                    suggestions=["Try again", "Cancel"]
                )
            
        except Exception as e:
            print(f"Error creating class: {e}")
            return ChatResponse(
                response=f"Error creating class: {str(e)}",
                intent="class_creation_error",
                suggestions=["Try again", "Cancel", "Contact support"]
            )
    
    def _create_grade_with_details(self, message: str, context: Dict) -> ChatResponse:
        """Create a grade with the provided details"""
        from ...base import db_execute_safe
        from datetime import datetime
        import uuid
        
        grade_name = context.get('grade_name', '').strip()
        group_selection = message.strip().lower()
        
        # Map group selection to proper group name
        group_mapping = {
            'pre-primary': 'Pre-Primary',
            'preprimary': 'Pre-Primary', 
            'primary': 'Primary',
            'secondary': 'Secondary',
            'other': 'Other'
        }
        
        group_name = group_mapping.get(group_selection, 'Other')
        
        if not grade_name:
            return ChatResponse(
                response="Missing grade name. Please start over.",
                intent="grade_creation_missing_name",
                suggestions=["Create new grade", "Cancel"]
            )
        
        try:
            # Check if grade already exists
            existing_grade = self.service.repo.check_grade_exists(grade_name)
            
            if existing_grade:
                return ChatResponse(
                    response=f"Grade '{grade_name}' already exists. Please choose a different name.",
                    intent="grade_already_exists",
                    suggestions=[
                        f"{grade_name} A",
                        f"{grade_name} 2",
                        "Try different name", 
                        "Cancel"
                    ]
                )
            
            # Create the grade
            grade_id = str(uuid.uuid4())
            
            rows_affected = db_execute_safe(self.db, """
                INSERT INTO cbc_level (id, school_id, label, group_name, created_at, updated_at)
                VALUES (:id, :school_id, :label, :group_name, :created_at, :updated_at)
            """, {
                "id": grade_id,
                "school_id": self.school_id,
                "label": grade_name,
                "group_name": group_name,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            if rows_affected:
                self.db.commit()
                
                return ChatResponse(
                    response=f"Successfully created grade '{grade_name}' in {group_name} group!",
                    intent="grade_created_successfully",
                    data={"context": {}},  # Clear context
                    suggestions=[
                        f"Create class for {grade_name}",
                        "List all grades",
                        "Create another grade",
                        "Show grade details"
                    ]
                )
            else:
                return ChatResponse(
                    response="Failed to create grade. Please try again.",
                    intent="grade_creation_failed",
                    suggestions=["Try again", "Cancel"]
                )
            
        except Exception as e:
            print(f"Error creating grade: {e}")
            return ChatResponse(
                response=f"Error creating grade: {str(e)}",
                intent="grade_creation_error", 
                suggestions=["Try again", "Cancel", "Contact support"]
            )
    
    def _create_error_recovery_response(self, context: Dict, error_message: str) -> ChatResponse:
        """Create error response while preserving context"""
        flow = context.get('flow', '')
        step = context.get('step', '')
        
        recovery_suggestions = []
        if flow == 'create_class':
            if step == 'select_grade':
                recovery_suggestions = ["Show available grades", "Create new grade", "Start over", "Cancel"]
            elif step == 'enter_class_name':
                recovery_suggestions = ["Try different name", "Go back to grade selection", "Cancel"]
        elif flow == 'create_grade':
            if step == 'enter_grade_name':
                recovery_suggestions = ["Try again", "Show examples", "Cancel"]
            elif step == 'select_grade_group':
                recovery_suggestions = ["Show grade groups", "Try again", "Cancel"]
        else:
            recovery_suggestions = ["Try again", "Start over", "Cancel"]
        
        return ChatResponse(
            response=f"I encountered a technical issue, but let's continue where we left off. We were working on: {flow.replace('_', ' ')}. What would you like to do?",
            intent="flow_error_recovery",
            data={"context": context},  # Preserve context for recovery
            suggestions=recovery_suggestions
        )