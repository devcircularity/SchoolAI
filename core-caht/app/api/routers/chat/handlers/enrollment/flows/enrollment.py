# app/api/routers/chat/handlers/flows/enrollment.py - Enrollment flow management
import uuid
import re
from typing import Dict, List, Optional
from datetime import datetime
from ....base import ChatResponse, db_execute_safe, db_execute_non_select

class EnrollmentFlow:
    """Handles multi-step enrollment processes with context management"""
    
    def __init__(self, db, school_id: str, user_id: str):
        self.db = db
        self.school_id = school_id
        self.user_id = user_id
    
    def initiate_single_enrollment(self, message: str) -> ChatResponse:
        """Start single student enrollment with smart parsing"""
        # Try to parse student identifier from message
        admission_no = self._extract_admission_number(message)
        student_name = self._extract_student_name(message)
        
        if not admission_no and not student_name:
            return ChatResponse(
                response="Please specify a student by admission number (e.g., 'enroll student 4444') or name (e.g., 'enroll Mary Smith').",
                intent="enrollment_parse_error",
                suggestions=[
                    "enroll student 4444",
                    "enroll Mary Smith", 
                    "Show unassigned students"
                ]
            )
        
        # Find matching students
        matched_students = []
        
        if admission_no:
            student = self._find_student_by_admission(admission_no)
            if student:
                matched_students = [student]
        elif student_name:
            matched_students = self._find_students_by_name(student_name)
        
        if not matched_students:
            identifier = admission_no or student_name
            return ChatResponse(
                response=f"No student found: {identifier}",
                intent="student_not_found",
                suggestions=["List all students", "Show unassigned students", "Create new student"]
            )
        
        # Multiple matches - need selection
        if len(matched_students) > 1:
            return self._show_student_selection(matched_students, message)
        
        # Single match - process enrollment
        return self._process_single_student_enrollment(matched_students[0])
    
    def initiate_bulk_enrollment(self) -> ChatResponse:
        """Start bulk enrollment process with confirmation"""
        try:
            # Get active term
            active_term = self._get_active_term()
            if not active_term:
                return ChatResponse(
                    response="No active term for bulk enrollment.\n\nPlease activate a term first.",
                    intent="no_active_term",
                    data={
                        "context": {
                            "handler": "enrollment",
                            "flow": "bulk_enrollment", 
                            "step": "activate_term_first"
                        }
                    },
                    suggestions=["Show available terms", "Activate a term", "Cancel"]
                )
            
            # Get students ready for enrollment
            ready_students = self._get_students_ready_for_enrollment(active_term['id'])
            
            if not ready_students:
                return ChatResponse(
                    response="No students ready for enrollment.\n\nAll eligible students may already be enrolled.",
                    intent="no_students_ready",
                    suggestions=["Show enrollment status", "Check for unassigned students", "Show current term"]
                )
            
            # Show confirmation with details
            response_text = f"Bulk Enrollment - {active_term['title']}\n\n"
            response_text += f"Ready to enroll {len(ready_students)} students:\n\n"
            
            # Group by class for better visualization
            by_class = {}
            for student in ready_students:
                class_name = student.get('class_name', 'Unknown class')
                if class_name not in by_class:
                    by_class[class_name] = []
                by_class[class_name].append(f"{student['first_name']} {student['last_name']}")
            
            for class_name, students in by_class.items():
                response_text += f"{class_name}: {len(students)} students\n"
                for student_name in students[:3]:  # Show first 3
                    response_text += f"  • {student_name}\n"
                if len(students) > 3:
                    response_text += f"  ... and {len(students) - 3} more\n"
                response_text += "\n"
            
            response_text += f"This will create {len(ready_students)} enrollment records.\nProceed with bulk enrollment?"
            
            return ChatResponse(
                response=response_text,
                intent="bulk_enrollment_confirmation",
                data={
                    "context": {
                        "handler": "enrollment",
                        "flow": "bulk_enrollment",
                        "step": "confirm_bulk",
                        "ready_students": ready_students,
                        "term": active_term,
                        "class_breakdown": by_class
                    }
                },
                suggestions=["Yes, enroll all", "No, cancel", "Show student details"]
            )
            
        except Exception as e:
            return ChatResponse(
                response=f"Error preparing bulk enrollment: {str(e)}",
                intent="error"
            )
    
    def handle_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle enrollment flow steps"""
        flow = context.get('flow')
        step = context.get('step')
        
        print(f"EnrollmentFlow: {flow}, step: {step}")
        
        if flow == 'single_enrollment':
            if step == 'select_from_multiple':
                return self._process_student_selection(message, context)
            elif step == 'confirm_class_assignment':
                return self._process_class_assignment_confirmation(message, context)
            elif step == 'activate_term_first':
                return self._process_term_activation_for_enrollment(message, context)
            elif step == 'select_class':
                return self._process_class_selection_for_enrollment(message, context)
        elif flow == 'bulk_enrollment':
            if step == 'confirm_bulk':
                return self._process_bulk_confirmation(message, context)
            elif step == 'activate_term_first':
                return self._process_term_activation_for_enrollment(message, context)
        elif flow == 'class_assignment':
            if step == 'select_class':
                return self._process_class_selection_for_assignment(message, context)
            elif step == 'confirm_assignment':
                return self._process_assignment_confirmation(message, context)
        
        # Unknown flow, reset
        return ChatResponse(
            response="Enrollment flow completed or reset.",
            intent="enrollment_flow_reset", 
            data={"context": {}},
            suggestions=["Show enrollment status", "Enroll students", "List students"]
        )
    
    def _process_student_selection(self, message: str, context: Dict) -> ChatResponse:
        """Process student selection from multiple matches"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Enrollment cancelled.",
                intent="enrollment_cancelled",
                data={"context": {}},
                suggestions=["Show enrollment status", "List students"]
            )
        
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
            selection = int(message_lower)
            if 1 <= selection <= len(matched_students):
                selected_student = matched_students[selection - 1]
        except ValueError:
            # Try to match by partial name
            for student in matched_students:
                student_name = f"{student['first_name']} {student['last_name']}"
                if message_lower in student_name.lower():
                    selected_student = student
                    break
        
        if not selected_student:
            return ChatResponse(
                response=f"Please select a valid number (1-{len(matched_students)}) or say 'cancel'.",
                intent="invalid_student_selection",
                data={"context": context},
                suggestions=[f"Select {i}" for i in range(1, min(len(matched_students) + 1, 4))] + ["Cancel"]
            )
        
        # Process enrollment for selected student
        return self._process_single_student_enrollment(selected_student)
    
    def _process_class_assignment_confirmation(self, message: str, context: Dict) -> ChatResponse:
        """Process confirmation to assign student to class before enrollment"""
        message_lower = message.lower().strip()
        
        if message_lower in ['no', 'cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Enrollment cancelled.",
                intent="enrollment_cancelled",
                data={"context": {}},
                suggestions=["Show enrollment status", "List students"]
            )
        
        if message_lower in ['show other classes', 'other classes', 'show classes']:
            # Show class selection instead
            student = context.get('student')
            return self._show_class_selection_for_student(student)
        
        if message_lower in ['yes', 'assign', 'ok', 'proceed', 'yes, assign and enroll']:
            # Execute assignment and enrollment
            student = context.get('student')
            suggested_class = context.get('suggested_class')
            
            if not student or not suggested_class:
                return ChatResponse(
                    response="Error: Missing assignment data.",
                    intent="error",
                    data={"context": {}}
                )
            
            return self._assign_and_enroll_student(student, suggested_class)
        
        # Default to proceeding
        return self._assign_and_enroll_student(
            context.get('student'), 
            context.get('suggested_class')
        )
    
    def _process_bulk_confirmation(self, message: str, context: Dict) -> ChatResponse:
        """Process bulk enrollment confirmation"""
        message_lower = message.lower().strip()
        
        if message_lower in ['no', 'cancel', 'exit', 'stop', 'no, cancel']:
            return ChatResponse(
                response="Bulk enrollment cancelled.",
                intent="bulk_enrollment_cancelled",
                data={"context": {}},
                suggestions=["Show enrollment status", "Enroll individual students"]
            )
        
        if message_lower in ['show student details', 'show details', 'details']:
            ready_students = context.get('ready_students', [])
            return self._show_detailed_enrollment_list(ready_students, context.get('term'))
        
        if message_lower in ['yes', 'enroll', 'proceed', 'confirm', 'ok', 'yes, enroll all']:
            # Execute the bulk enrollment
            ready_students = context.get('ready_students', [])
            term = context.get('term')
            return self._execute_bulk_enrollment(ready_students, term)
        
        # Default to proceeding
        ready_students = context.get('ready_students', [])
        term = context.get('term')
        return self._execute_bulk_enrollment(ready_students, term)
    
    def _process_term_activation_for_enrollment(self, message: str, context: Dict) -> ChatResponse:
        """Handle term activation in enrollment context"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Enrollment cancelled.",
                intent="enrollment_cancelled", 
                data={"context": {}},
                suggestions=["Show enrollment status"]
            )
        
        if message_lower in ['show available terms', 'show terms', 'available terms']:
            # Delegate to academic handler for term management
            return ChatResponse(
                response="Please use the academic term management to activate a term first, then return to enrollment.",
                intent="delegate_to_academic",
                suggestions=["Show academic calendar", "Activate a term", "Current term status"]
            )
        
        # Default suggestion
        return ChatResponse(
            response="Please activate an academic term first before enrolling students.",
            intent="term_activation_needed",
            data={"context": {}},
            suggestions=["Show academic calendar", "Activate a term", "Current term status"]
        )
    
    def _show_student_selection(self, matched_students: list, original_message: str) -> ChatResponse:
        """Show student selection when multiple matches found"""
        response_text = f"Found {len(matched_students)} students matching your search:\n\n"
        
        for i, student in enumerate(matched_students, 1):
            name = f"{student['first_name']} {student['last_name']}"
            admission = student['admission_no'] or "No admission #"
            class_info = f" - {student['class_name']}" if student.get('class_name') else " - No class assigned"
            response_text += f"{i}. {name} (#{admission}){class_info}\n"
        
        response_text += f"\nWhich student would you like to enroll?"
        
        return ChatResponse(
            response=response_text,
            intent="multiple_students_for_enrollment",
            data={
                "context": {
                    "handler": "enrollment",
                    "flow": "single_enrollment", 
                    "step": "select_from_multiple",
                    "matched_students": matched_students,
                    "original_message": original_message
                }
            },
            suggestions=[f"Select {i}" for i in range(1, min(len(matched_students) + 1, 4))] + ["Cancel"]
        )
    
    def _show_class_selection_for_student(self, student: dict) -> ChatResponse:
        """Show class selection for student assignment"""
        try:
            available_classes = self._get_available_classes_for_assignment()
            
            if not available_classes:
                return ChatResponse(
                    response="No classes available for assignment.\n\nPlease create classes first.",
                    intent="no_classes_available",
                    data={"context": {}},
                    suggestions=["Create new class", "Show class setup guide"]
                )
            
            student_name = f"{student['first_name']} {student['last_name']}"
            response_text = f"Available classes for {student_name}:\n\n"
            
            # Group by academic year
            classes_by_year = {}
            for cls in available_classes:
                year = cls['academic_year']
                if year not in classes_by_year:
                    classes_by_year[year] = []
                classes_by_year[year].append(cls)
            
            index = 1
            class_options = []
            for year in sorted(classes_by_year.keys(), reverse=True):
                response_text += f"Academic Year {year}:\n"
                for cls in classes_by_year[year]:
                    stream_info = f" ({cls['stream']})" if cls.get('stream') else ""
                    capacity_info = f" [{cls['current_students']}/40 students]"
                    response_text += f"  {index}. {cls['name']}{stream_info} - {cls['level']}{capacity_info}\n"
                    class_options.append(cls)
                    index += 1
                response_text += "\n"
            
            response_text += f"Which class should I assign {student_name} to?"
            
            return ChatResponse(
                response=response_text,
                intent="class_selection_for_student",
                data={
                    "context": {
                        "handler": "enrollment",
                        "flow": "single_enrollment",
                        "step": "select_class", 
                        "student": student,
                        "available_classes": class_options
                    }
                },
                suggestions=[f"Select {i}" for i in range(1, min(len(class_options) + 1, 4))] + ["Cancel"]
            )
            
        except Exception as e:
            return ChatResponse(
                response=f"Error getting class options: {str(e)}",
                intent="error",
                data={"context": {}}
            )
    
    def _process_class_selection_for_enrollment(self, message: str, context: Dict) -> ChatResponse:
        """Process class selection for student before enrollment"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Enrollment cancelled.",
                intent="enrollment_cancelled",
                data={"context": {}},
                suggestions=["Show enrollment status", "List students"]
            )
        
        available_classes = context.get('available_classes', [])
        student = context.get('student')
        
        if not available_classes or not student:
            return ChatResponse(
                response="Error: Missing class selection data.",
                intent="error",
                data={"context": {}}
            )
        
        # Parse selection
        selected_class = None
        try:
            selection = int(message_lower)
            if 1 <= selection <= len(available_classes):
                selected_class = available_classes[selection - 1]
        except ValueError:
            # Try to match by class name
            for cls in available_classes:
                if message_lower in cls['name'].lower():
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
        return self._assign_and_enroll_student(student, selected_class)
    
    def _show_detailed_enrollment_list(self, ready_students: list, term: dict) -> ChatResponse:
        """Show detailed list of students ready for enrollment"""
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
            data={
                "context": {
                    "handler": "enrollment",
                    "flow": "bulk_enrollment", 
                    "step": "confirm_bulk",
                    "ready_students": ready_students,
                    "term": term
                }
            },
            suggestions=["Yes, enroll all", "No, cancel"]
        )
    
    def _process_single_student_enrollment(self, student: dict) -> ChatResponse:
        """Process enrollment for a specific student with context awareness"""
        try:
            # Check active term
            active_term = self._get_active_term()
            if not active_term:
                return ChatResponse(
                    response="No active academic term found.\n\nPlease activate a term before enrolling students.",
                    intent="no_active_term_for_enrollment",
                    data={
                        "context": {
                            "handler": "enrollment",
                            "flow": "single_enrollment",
                            "step": "activate_term_first",
                            "student": student
                        }
                    },
                    suggestions=["Show available terms", "Activate a term", "Cancel"]
                )
            
            # Check class assignment
            if not student.get('class_id'):
                # Suggest appropriate class
                suggested_class = self._suggest_class_for_student(student)
                
                if suggested_class:
                    student_name = f"{student['first_name']} {student['last_name']}"
                    return ChatResponse(
                        response=f"{student_name} is not assigned to any class.\n\nI suggest: {suggested_class['name']} ({suggested_class['level']})\n\nShould I assign them to this class and then enroll?",
                        intent="student_needs_class_assignment",
                        data={
                            "context": {
                                "handler": "enrollment", 
                                "flow": "single_enrollment",
                                "step": "confirm_class_assignment",
                                "student": student,
                                "suggested_class": suggested_class
                            }
                        },
                        suggestions=["Yes, assign and enroll", "Show other classes", "Cancel"]
                    )
                else:
                    # Show all available classes for selection
                    return self._show_class_selection_for_student(student)
            
            # Check existing enrollment
            if self._is_already_enrolled(student['id'], active_term['id']):
                student_name = f"{student['first_name']} {student['last_name']}"
                return ChatResponse(
                    response=f"{student_name} is already enrolled in {active_term['title']}.",
                    intent="already_enrolled",
                    data={"context": {}},
                    suggestions=["Show enrollment status", "Enroll different student"]
                )
            
            # Execute enrollment
            return self._execute_single_enrollment(student, active_term)
            
        except Exception as e:
            return ChatResponse(
                response=f"Error processing student enrollment: {str(e)}",
                intent="error",
                data={"context": {}}
            )
    
    def _assign_and_enroll_student(self, student: dict, target_class: dict) -> ChatResponse:
        """Assign student to class and then enroll them"""
        try:
            # Update student's class assignment
            affected_rows = db_execute_non_select(self.db,
                """UPDATE students 
                   SET class_id = :class_id, updated_at = CURRENT_TIMESTAMP
                   WHERE id = :student_id AND school_id = :school_id""",
                {
                    "class_id": target_class['id'],
                    "student_id": student['id'],
                    "school_id": self.school_id
                }
            )
            
            if affected_rows == 0:
                return ChatResponse(
                    response="Failed to assign student to class.",
                    intent="assignment_failed",
                    data={"context": {}}
                )
            
            # Update student data with new class info
            student['class_id'] = target_class['id']
            student['class_name'] = target_class['name']
            
            # Get active term
            active_term = self._get_active_term()
            if not active_term:
                return ChatResponse(
                    response="Class assignment successful, but no active term for enrollment.",
                    intent="assignment_success_no_term",
                    data={"context": {}},
                    suggestions=["Activate a term", "Show academic calendar"]
                )
            
            # Now proceed with enrollment
            return self._execute_single_enrollment(student, active_term, was_just_assigned=True)
            
        except Exception as e:
            self.db.rollback()
            return ChatResponse(
                response=f"Failed to assign and enroll student: {str(e)}",
                intent="assignment_enrollment_failed",
                data={"context": {}}
            )
    
    def _execute_single_enrollment(self, student: dict, active_term: dict, was_just_assigned: bool = False) -> ChatResponse:
        """Execute single student enrollment"""
        try:
            student_id = student['id']
            class_id = student['class_id']
            term_id = active_term['id']
            
            # Generate enrollment ID
            enrollment_id = str(uuid.uuid4())
            
            # Create enrollment record
            affected_rows = db_execute_non_select(self.db,
                """INSERT INTO enrollments (id, school_id, student_id, class_id, term_id, status, created_at, updated_at)
                   VALUES (:id, :school_id, :student_id, :class_id, :term_id, 'ENROLLED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                {
                    "id": enrollment_id,
                    "school_id": self.school_id,
                    "student_id": student_id,
                    "class_id": class_id,
                    "term_id": term_id
                }
            )
            
            if affected_rows == 0:
                return ChatResponse(
                    response="Failed to create enrollment record.",
                    intent="enrollment_failed",
                    data={"context": {}}
                )
            
            # Commit transaction
            self.db.commit()
            
            # Build success response
            student_name = f"{student['first_name']} {student['last_name']}"
            admission_no = student['admission_no'] or "No admission #"
            class_name = student.get('class_name', 'Unknown class')
            
            response_text = f"✅ Enrollment Successful!\n\n"
            
            if was_just_assigned:
                response_text += f"✓ Assigned to class: {class_name}\n"
            
            response_text += f"Student: {student_name} (#{admission_no})\n"
            response_text += f"Class: {class_name}\n"
            response_text += f"Term: {active_term['title']}\n"
            response_text += f"Status: ENROLLED\n\n"
            response_text += f"Next steps:\n"
            response_text += f"• Generate invoice for {student_name}\n"
            response_text += f"• Notify parent about enrollment"
            
            return ChatResponse(
                response=response_text,
                intent="single_enrollment_successful",
                data={
                    "student_id": student_id,
                    "student_name": student_name,
                    "admission_no": student['admission_no'],
                    "class_name": class_name,
                    "term_id": term_id,
                    "term_title": active_term['title'],
                    "enrollment_id": enrollment_id,
                    "was_just_assigned": was_just_assigned,
                    "context": {}  # Clear context - enrollment complete
                },
                suggestions=[
                    f"Generate invoice for student {admission_no}",
                    "Show enrollment status",
                    "Enroll more students"
                ]
            )
            
        except Exception as e:
            self.db.rollback()
            return ChatResponse(
                response=f"Error enrolling student: {str(e)}",
                intent="error",
                data={"context": {}}
            )
    
    def _execute_bulk_enrollment(self, ready_students: list, term: dict) -> ChatResponse:
        """Execute bulk enrollment for multiple students"""
        try:
            term_id = term['id']
            successful_enrollments = []
            failed_enrollments = []
            
            response_text = f"Bulk Enrollment Progress - {term['title']}\n\n"
            
            for student in ready_students:
                try:
                    student_id = student['id']
                    class_id = student['class_id']
                    enrollment_id = str(uuid.uuid4())
                    
                    # Create enrollment record
                    affected_rows = db_execute_non_select(self.db,
                        """INSERT INTO enrollments (id, school_id, student_id, class_id, term_id, status, created_at, updated_at)
                           VALUES (:id, :school_id, :student_id, :class_id, :term_id, 'ENROLLED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                        {
                            "id": enrollment_id,
                            "school_id": self.school_id,
                            "student_id": student_id,
                            "class_id": class_id,
                            "term_id": term_id
                        }
                    )
                    
                    if affected_rows > 0:
                        successful_enrollments.append({
                            "name": f"{student['first_name']} {student['last_name']}",
                            "admission_no": student['admission_no'],
                            "class": student.get('class_name', 'Unknown'),
                            "enrollment_id": enrollment_id
                        })
                    else:
                        failed_enrollments.append(f"{student['first_name']} {student['last_name']} - No rows affected")
                        
                except Exception as e:
                    failed_enrollments.append(f"{student['first_name']} {student['last_name']} - {str(e)}")
                    continue
            
            if successful_enrollments:
                # Commit successful enrollments
                self.db.commit()
                
                response_text += f"✅ Successfully enrolled {len(successful_enrollments)} students:\n\n"
                
                # Group by class for better display
                by_class = {}
                for enrollment in successful_enrollments:
                    class_name = enrollment['class']
                    if class_name not in by_class:
                        by_class[class_name] = []
                    by_class[class_name].append(enrollment['name'])
                
                for class_name, students in by_class.items():
                    response_text += f"{class_name}: {len(students)} students\n"
                    for student_name in students[:5]:  # Show first 5
                        response_text += f"  ✓ {student_name}\n"
                    if len(students) > 5:
                        response_text += f"  ... and {len(students) - 5} more\n"
                    response_text += "\n"
                
                if failed_enrollments:
                    response_text += f"❌ Failed: {len(failed_enrollments)} students\n"
                    for failure in failed_enrollments[:3]:
                        response_text += f"  ✗ {failure}\n"
                    if len(failed_enrollments) > 3:
                        response_text += f"  ... and {len(failed_enrollments) - 3} more failures\n"
                
                response_text += f"\nNext steps:\n"
                response_text += f"• Generate invoices for enrolled students\n"
                response_text += f"• Notify parents about enrollment"
                
                return ChatResponse(
                    response=response_text,
                    intent="bulk_enrollment_successful",
                    data={
                        "term_id": term_id,
                        "term_title": term['title'],
                        "successful_count": len(successful_enrollments),
                        "failed_count": len(failed_enrollments),
                        "successful_enrollments": successful_enrollments,
                        "failed_enrollments": failed_enrollments,
                        "context": {}  # Clear context - enrollment complete
                    },
                    suggestions=[
                        "Generate invoices for all students",
                        "Show enrollment status",
                        "Show class enrollments"
                    ]
                )
            else:
                # No successful enrollments
                self.db.rollback()
                
                response_text += f"❌ Bulk enrollment failed - no students enrolled\n\n"
                response_text += f"Failures:\n"
                for failure in failed_enrollments[:5]:
                    response_text += f"  ✗ {failure}\n"
                if len(failed_enrollments) > 5:
                    response_text += f"  ... and {len(failed_enrollments) - 5} more failures\n"
                
                return ChatResponse(
                    response=response_text,
                    intent="bulk_enrollment_failed",
                    data={"context": {}},
                    suggestions=[
                        "Check database connectivity",
                        "Try individual enrollments",
                        "Show enrollment status"
                    ]
                )
                
        except Exception as e:
            self.db.rollback()
            return ChatResponse(
                response=f"Error during bulk enrollment: {str(e)}",
                intent="error",
                data={"context": {}}
            )
    
    # Helper methods
    def _extract_admission_number(self, message: str) -> Optional[str]:
        """Extract admission number from message"""
        patterns = [
            r'student\s+(\d{4,7})',  # student followed by 4-7 digits
            r'enroll\s+student\s+(\d+)',  # enroll student followed by digits
            r'student\s+(\d+)\s+in',  # student digits in
            r'(\d{7})',  # any 7-digit number
            r'(\d{6})',  # any 6-digit number
            r'(\d{5})',  # any 5-digit number
            r'(\d{4})'   # any 4-digit number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None
    
    def _extract_student_name(self, message: str) -> Optional[str]:
        """Extract student name from message"""
        patterns = [
            r'enroll\s+([a-zA-Z\s]+?)(?:\s+in|\s*$)',  # enroll [name] in/end
            r'student\s+([a-zA-Z\s]+?)(?:\s+in|\s*$)',  # student [name] in/end
            r'^([a-zA-Z\s]+?)\s+in\s+term'  # [name] in term
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out obvious non-names
                if len(name) >= 3 and not any(word in name.lower() for word in ['enroll', 'student', 'current', 'term']):
                    return name
        return None
    
    def _find_student_by_admission(self, admission_no: str) -> Optional[dict]:
        """Find student by admission number"""
        try:
            result = db_execute_safe(self.db,
                """SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id, 
                          c.name as class_name, c.level
                   FROM students s
                   LEFT JOIN classes c ON s.class_id = c.id
                   WHERE s.school_id = :school_id AND s.admission_no = :admission_no 
                   AND s.status = 'ACTIVE'
                   LIMIT 1""",
                {"school_id": self.school_id, "admission_no": admission_no}
            )
            
            if result:
                student = result[0]
                return {
                    'id': str(student[0]),
                    'first_name': student[1],
                    'last_name': student[2],
                    'admission_no': student[3],
                    'class_id': str(student[4]) if student[4] else None,
                    'class_name': student[5],
                    'class_level': student[6]
                }
            return None
        except Exception as e:
            print(f"Error finding student by admission: {e}")
            return None
    
    def _find_students_by_name(self, name: str) -> List[dict]:
        """Find students by name (fuzzy matching)"""
        try:
            # Split name for first/last matching
            name_parts = name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
                
                result = db_execute_safe(self.db,
                    """SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id,
                              c.name as class_name, c.level
                       FROM students s
                       LEFT JOIN classes c ON s.class_id = c.id
                       WHERE s.school_id = :school_id AND s.status = 'ACTIVE'
                       AND (LOWER(s.first_name) LIKE :first_pattern 
                            OR LOWER(s.last_name) LIKE :last_pattern
                            OR LOWER(s.first_name || ' ' || s.last_name) LIKE :full_pattern)
                       ORDER BY s.first_name, s.last_name
                       LIMIT 10""",
                    {
                        "school_id": self.school_id,
                        "first_pattern": f"%{first_name.lower()}%",
                        "last_pattern": f"%{last_name.lower()}%", 
                        "full_pattern": f"%{name.lower()}%"
                    }
                )
            else:
                # Single name - search both first and last
                result = db_execute_safe(self.db,
                    """SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id,
                              c.name as class_name, c.level
                       FROM students s
                       LEFT JOIN classes c ON s.class_id = c.id
                       WHERE s.school_id = :school_id AND s.status = 'ACTIVE'
                       AND (LOWER(s.first_name) LIKE :pattern OR LOWER(s.last_name) LIKE :pattern)
                       ORDER BY s.first_name, s.last_name
                       LIMIT 10""",
                    {
                        "school_id": self.school_id,
                        "pattern": f"%{name.lower()}%"
                    }
                )
            
            students = []
            for student in result:
                students.append({
                    'id': str(student[0]),
                    'first_name': student[1],
                    'last_name': student[2],
                    'admission_no': student[3],
                    'class_id': str(student[4]) if student[4] else None,
                    'class_name': student[5],
                    'class_level': student[6]
                })
            
            return students
        except Exception as e:
            print(f"Error finding students by name: {e}")
            return []
    
    def _get_active_term(self) -> Optional[dict]:
        """Get active academic term"""
        try:
            result = db_execute_safe(self.db,
                """SELECT t.id, t.title, y.year
                   FROM academic_terms t
                   JOIN academic_years y ON t.year_id = y.id
                   WHERE t.school_id = :school_id AND t.state = 'ACTIVE'
                   LIMIT 1""",
                {"school_id": self.school_id}
            )
            
            if result:
                term = result[0]
                return {
                    'id': str(term[0]),
                    'title': term[1],
                    'year': term[2]
                }
            return None
        except Exception as e:
            print(f"Error getting active term: {e}")
            return None
    
    def _get_students_ready_for_enrollment(self, term_id: str) -> List[dict]:
        """Get students ready for enrollment (assigned to classes but not enrolled in term)"""
        try:
            result = db_execute_safe(self.db,
                """SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id,
                          c.name as class_name, c.level
                   FROM students s
                   JOIN classes c ON s.class_id = c.id
                   WHERE s.school_id = :school_id 
                   AND s.status = 'ACTIVE'
                   AND NOT EXISTS (
                       SELECT 1 FROM enrollments e 
                       WHERE e.student_id = s.id AND e.term_id = :term_id
                   )
                   ORDER BY c.name, s.first_name, s.last_name""",
                {"school_id": self.school_id, "term_id": term_id}
            )
            
            students = []
            for student in result:
                students.append({
                    'id': str(student[0]),
                    'first_name': student[1],
                    'last_name': student[2],
                    'admission_no': student[3],
                    'class_id': str(student[4]),
                    'class_name': student[5],
                    'class_level': student[6]
                })
            
            return students
        except Exception as e:
            print(f"Error getting students ready for enrollment: {e}")
            return []
    
    def _suggest_class_for_student(self, student: dict) -> Optional[dict]:
        """Suggest appropriate class for student based on available info"""
        try:
            # Get classes with capacity
            result = db_execute_safe(self.db,
                """SELECT c.id, c.name, c.level, c.academic_year, c.stream,
                          COUNT(s.id) as current_students
                   FROM classes c
                   LEFT JOIN students s ON c.id = s.class_id AND s.status = 'ACTIVE'
                   WHERE c.school_id = :school_id
                   GROUP BY c.id, c.name, c.level, c.academic_year, c.stream
                   HAVING COUNT(s.id) < 40
                   ORDER BY c.academic_year DESC, c.level, c.name
                   LIMIT 5""",
                {"school_id": self.school_id}
            )
            
            if result:
                # Return first available class with capacity
                cls = result[0]
                return {
                    'id': str(cls[0]),
                    'name': cls[1],
                    'level': cls[2],
                    'academic_year': cls[3],
                    'stream': cls[4],
                    'current_students': cls[5]
                }
            return None
        except Exception as e:
            print(f"Error suggesting class: {e}")
            return None
    
    def _get_available_classes_for_assignment(self) -> List[dict]:
        """Get all available classes for student assignment"""
        try:
            result = db_execute_safe(self.db,
                """SELECT c.id, c.name, c.level, c.academic_year, c.stream,
                          COUNT(s.id) as current_students
                   FROM classes c
                   LEFT JOIN students s ON c.id = s.class_id AND s.status = 'ACTIVE'
                   WHERE c.school_id = :school_id
                   GROUP BY c.id, c.name, c.level, c.academic_year, c.stream
                   ORDER BY c.academic_year DESC, c.level, c.name""",
                {"school_id": self.school_id}
            )
            
            classes = []
            for cls in result:
                classes.append({
                    'id': str(cls[0]),
                    'name': cls[1],
                    'level': cls[2],
                    'academic_year': cls[3],
                    'stream': cls[4],
                    'current_students': cls[5]
                })
            
            return classes
        except Exception as e:
            print(f"Error getting available classes: {e}")
            return []
    
    def _is_already_enrolled(self, student_id: str, term_id: str) -> bool:
        """Check if student is already enrolled in the term"""
        try:
            result = db_execute_safe(self.db,
                """SELECT id FROM enrollments 
                   WHERE school_id = :school_id 
                   AND student_id = :student_id 
                   AND term_id = :term_id
                   LIMIT 1""",
                {
                    "school_id": self.school_id,
                    "student_id": student_id,
                    "term_id": term_id
                }
            )
            return bool(result)
        except Exception as e:
            print(f"Error checking enrollment status: {e}")
            return False