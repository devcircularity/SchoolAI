# handlers/enrollment/handler.py - Intent-first refactor
from typing import Dict, Optional
from ...base import BaseHandler, ChatResponse
from .service import EnrollmentService

class EnrollmentHandler(BaseHandler):
    """Intent-first enrollment handler"""
    
    def __init__(self, db, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.service = EnrollmentService(db, school_id, self.get_school_name)
        
        # Import flow handler with error handling
        try:
            from .flows.enrollment import EnrollmentFlow
            self.enrollment_flow = EnrollmentFlow(db, school_id, user_id)
        except ImportError as e:
            print(f"Warning: Could not import enrollment flow: {e}")
            self.enrollment_flow = None
    
    def handle_intent(self, intent: str, message: str, entities: Dict, context: Dict) -> ChatResponse:
        """
        Handle enrollment operations based on intent classification
        
        Args:
            intent: The classified intent (e.g., 'enrollment_single', 'enrollment_bulk')
            message: Original user message
            entities: Extracted entities (student_name, admission_no, etc.)
            context: Conversation context including flows
        """
        # Handle context flows first (multi-step processes)
        if self._has_active_context(context):
            return self._handle_context_flow(message, context)
        
        # Route based on intent
        if intent == 'enrollment_single':
            return self.service.initiate_single_enrollment(message)
        
        elif intent == 'enrollment_bulk':
            return self.service.initiate_bulk_enrollment()
        
        elif intent == 'enrollment_status':
            return self.service.show_enrollment_statistics()
        
        elif intent == 'enrollment_list':
            return self.service.show_enrollment_statistics()  # Same as status
        
        else:
            # Default to enrollment statistics for unknown intents
            return self.service.show_enrollment_statistics()
    
    def _has_active_context(self, context):
        """Check if context indicates an active enrollment flow"""
        return (context.get('handler') == 'enrollment' and 
                context.get('flow') in ['single_enrollment', 'bulk_enrollment'] and
                context.get('step'))
    
    def _handle_context_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle multi-step context flows"""
        if self.enrollment_flow:
            return self.enrollment_flow.handle_flow(message, context)
        else:
            # Fallback handling without flow handler
            return self._fallback_flow_handling(message, context)
    
    def _fallback_flow_handling(self, message: str, context: Dict) -> ChatResponse:
        """Handle flows without the flow handler"""
        flow = context.get('flow')
        step = context.get('step')
        message_lower = message.lower().strip()
        
        # Handle cancellation
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Enrollment cancelled.",
                intent="enrollment_cancelled",
                data={"context": {}},
                suggestions=["Show enrollment status", "Enroll students"]
            )
        
        if flow == 'single_enrollment':
            if step == 'select_from_multiple':
                return self._handle_student_selection_fallback(message, context)
            elif step == 'confirm_class_assignment':
                return self._handle_class_assignment_confirmation_fallback(message, context)
            elif step == 'select_class':
                return self._handle_class_selection_fallback(message, context)
                
        elif flow == 'bulk_enrollment':
            if step == 'confirm_bulk':
                return self._handle_bulk_confirmation_fallback(message, context)
        
        # Unknown flow step
        return ChatResponse(
            response="Enrollment flow completed or reset.",
            intent="enrollment_flow_reset", 
            data={"context": {}},
            suggestions=["Show enrollment status", "Enroll students"]
        )
    
    def _handle_student_selection_fallback(self, message: str, context: Dict) -> ChatResponse:
        """Handle student selection from multiple matches"""
        matched_students = context.get('matched_students', [])
        if not matched_students:
            return ChatResponse(
                response="Error: No students in selection context.",
                intent="error",
                data={"context": {}}
            )
        
        # Parse selection
        selected_student = None
        try:
            selection = int(message.lower().strip())
            if 1 <= selection <= len(matched_students):
                selected_student = matched_students[selection - 1]
        except ValueError:
            # Try to match by partial name
            for student in matched_students:
                student_name = f"{student['first_name']} {student['last_name']}"
                if message.lower() in student_name.lower():
                    selected_student = student
                    break
        
        if not selected_student:
            return ChatResponse(
                response=f"Please select a valid number (1-{len(matched_students)}) or say 'cancel'.",
                intent="invalid_student_selection",
                data={"context": context},
                suggestions=[f"Select {i}" for i in range(1, min(len(matched_students) + 1, 4))] + ["Cancel"]
            )
        
        # Convert dict back to student enrollment data for processing
        from .dataclasses import row_to_student_enrollment
        student = row_to_student_enrollment((
            selected_student['id'], selected_student['first_name'], selected_student['last_name'],
            selected_student['admission_no'], selected_student['class_id'], 
            selected_student['class_name'], selected_student.get('class_level')
        ))
        
        return self.service._process_single_student_enrollment(student)
    
    def _handle_class_assignment_confirmation_fallback(self, message: str, context: Dict) -> ChatResponse:
        """Handle class assignment confirmation"""
        message_lower = message.lower().strip()
        
        if message_lower in ['show other classes', 'other classes', 'show classes']:
            # Redirect to class selection
            student_dict = context.get('student')
            available_class_rows = self.service.repo.get_available_classes_for_assignment()
            
            from .dataclasses import row_to_class, row_to_student_enrollment
            available_classes = [row_to_class(row) for row in available_class_rows]
            student = row_to_student_enrollment((
                student_dict['id'], student_dict['first_name'], student_dict['last_name'],
                student_dict['admission_no'], student_dict['class_id'], 
                student_dict['class_name'], student_dict.get('class_level')
            ))
            
            return self.service.views.class_selection_for_student(student, available_classes)
        
        if message_lower in ['yes', 'assign', 'ok', 'proceed', 'yes, assign and enroll']:
            # Execute assignment and enrollment
            student_dict = context.get('student')
            suggested_class_dict = context.get('suggested_class')
            
            if not student_dict or not suggested_class_dict:
                return ChatResponse(
                    response="Error: Missing assignment data.",
                    intent="error",
                    data={"context": {}}
                )
            
            return self.service.assign_and_enroll_student(student_dict, suggested_class_dict)
        
        # Default to proceeding
        return self.service.assign_and_enroll_student(
            context.get('student'), 
            context.get('suggested_class')
        )
    
    def _handle_class_selection_fallback(self, message: str, context: Dict) -> ChatResponse:
        """Handle class selection for student"""
        available_classes = context.get('available_classes', [])
        student_dict = context.get('student')
        
        if not available_classes or not student_dict:
            return ChatResponse(
                response="Error: Missing class selection data.",
                intent="error",
                data={"context": {}}
            )
        
        # Parse selection
        selected_class = None
        try:
            selection = int(message.lower().strip())
            if 1 <= selection <= len(available_classes):
                selected_class = available_classes[selection - 1]
        except ValueError:
            # Try to match by class name
            for cls in available_classes:
                if message.lower() in cls['name'].lower():
                    selected_class = cls
                    break
        
        if not selected_class:
            return ChatResponse(
                response=f"Please select a valid class number (1-{len(available_classes)}) or say 'cancel'.",
                intent="invalid_class_selection",
                data={"context": context},
                suggestions=[f"Select {i}" for i in range(1, min(len(available_classes) + 1, 4))] + ["Cancel"]
            )
        
        # Assign student to selected class and then enroll
        return self.service.assign_and_enroll_student(student_dict, selected_class)
    
    def _handle_bulk_confirmation_fallback(self, message: str, context: Dict) -> ChatResponse:
        """Handle bulk enrollment confirmation"""
        message_lower = message.lower().strip()
        
        if message_lower in ['show student details', 'show details', 'details']:
            ready_students = context.get('ready_students', [])
            term = context.get('term')
            
            # Show detailed list
            response_text = f"Students Ready for Enrollment - {term['title']}\n\n"
            
            for i, student in enumerate(ready_students, 1):
                name = f"{student['first_name']} {student['last_name']}"
                admission = student['admission_no'] or "No admission #"
                class_name = student.get('class_name', 'Unknown class')
                
                response_text += f"{i:2d}. {name} (#{admission}) → {class_name}\n"
            
            response_text += f"\nTotal: {len(ready_students)} students\nProceed with enrollment?"
            
            return ChatResponse(
                response=response_text,
                intent="detailed_enrollment_list",
                data={"context": context},
                suggestions=["Yes, enroll all", "No, cancel"]
            )
        
        if message_lower in ['yes', 'enroll', 'proceed', 'confirm', 'ok', 'yes, enroll all']:
            # Execute the bulk enrollment
            ready_students = context.get('ready_students', [])
            term = context.get('term')
            return self.service.execute_bulk_enrollment(ready_students, term)
        
        # Default to proceeding
        ready_students = context.get('ready_students', [])
        term = context.get('term')
        return self.service.execute_bulk_enrollment(ready_students, term)