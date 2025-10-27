# handlers/enrollment/service.py
from ...base import ChatResponse
from .repo import EnrollmentRepo
from .views import EnrollmentViews
from .dataclasses import (
    row_to_student_enrollment, row_to_term, row_to_class,
    EnrollmentResult, BulkEnrollmentResult, group_students_by_class
)
from ..shared.parsing import extract_admission_number, extract_name

class EnrollmentService:
    """Business logic layer for enrollment operations"""
    
    def __init__(self, db, school_id, get_school_name):
        self.repo = EnrollmentRepo(db, school_id)
        self.views = EnrollmentViews(get_school_name)
    
    def initiate_single_enrollment(self, message):
        """Start single student enrollment with smart parsing"""
        try:
            # Parse student identifier from message
            admission_no = extract_admission_number(message)
            student_name = extract_name(message)
            
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
                student_row = self.repo.find_student_by_admission(admission_no)
                if student_row:
                    matched_students = [row_to_student_enrollment(student_row[0])]
            elif student_name:
                student_rows = self.repo.find_students_by_name(student_name)
                matched_students = [row_to_student_enrollment(row) for row in student_rows]
            
            if not matched_students:
                identifier = admission_no or student_name
                return self.views.student_not_found(identifier)
            
            # Multiple matches - need selection
            if len(matched_students) > 1:
                return self.views.multiple_students_selection(matched_students, message)
            
            # Single match - process enrollment
            return self._process_single_student_enrollment(matched_students[0])
            
        except Exception as e:
            return self.views.error("parsing enrollment request", str(e))
    
    def initiate_bulk_enrollment(self):
        """Start bulk enrollment process"""
        try:
            # Get active term
            active_term_row = self.repo.get_active_term()
            if not active_term_row:
                return self.views.no_active_term()
            
            active_term = row_to_term(active_term_row[0])
            
            # Get students ready for enrollment
            ready_student_rows = self.repo.get_students_ready_for_enrollment(active_term.id)
            
            if not ready_student_rows:
                return self.views.no_students_ready()
            
            ready_students = [row_to_student_enrollment(row) for row in ready_student_rows]
            
            # Group by class for better visualization
            class_breakdown = {}
            for student in ready_students:
                class_name = student.class_name or 'Unknown class'
                if class_name not in class_breakdown:
                    class_breakdown[class_name] = []
                class_breakdown[class_name].append(f"{student.first_name} {student.last_name}")
            
            return self.views.bulk_enrollment_confirmation(ready_students, active_term, class_breakdown)
            
        except Exception as e:
            return self.views.error("preparing bulk enrollment", str(e))
    
    def show_enrollment_statistics(self):
        """Show enrollment statistics"""
        try:
            stats = self.repo.get_enrollment_statistics()
            return self.views.enrollment_statistics(stats)
        except Exception as e:
            return self.views.error("getting enrollment statistics", str(e))
    
    def _process_single_student_enrollment(self, student):
        """Process enrollment for a specific student"""
        try:
            # Check active term
            active_term_row = self.repo.get_active_term()
            if not active_term_row:
                return self.views.no_active_term()
            
            active_term = row_to_term(active_term_row[0])
            
            # Check class assignment
            if not student.class_id:
                # Suggest appropriate class
                suggested_class_rows = self.repo.suggest_class_for_student(student.__dict__)
                
                if suggested_class_rows:
                    suggested_class = row_to_class(suggested_class_rows[0])
                    return self.views.student_needs_class_assignment(student, suggested_class)
                else:
                    # Show all available classes for selection
                    available_class_rows = self.repo.get_available_classes_for_assignment()
                    available_classes = [row_to_class(row) for row in available_class_rows]
                    return self.views.class_selection_for_student(student, available_classes)
            
            # Check existing enrollment
            if self.repo.is_already_enrolled(student.id, active_term.id):
                return self.views.already_enrolled(student, active_term)
            
            # Execute enrollment
            return self._execute_single_enrollment(student, active_term)
            
        except Exception as e:
            return self.views.error("processing student enrollment", str(e))
    
    def _execute_single_enrollment(self, student, active_term, was_just_assigned=False):
        """Execute single student enrollment"""
        try:
            # Create enrollment record
            result = self.repo.create_enrollment(student.id, student.class_id, active_term.id)
            
            if result['affected_rows'] == 0:
                return ChatResponse(
                    response="Failed to create enrollment record.",
                    intent="enrollment_failed",
                    data={"context": {}}
                )
            
            # Commit transaction
            self.repo.db.commit()
            
            # Build success result
            enrollment_result = EnrollmentResult(
                student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                admission_no=student.admission_no,
                class_name=student.class_name or "Unknown class",
                term_title=active_term.title,
                enrollment_id=result['enrollment_id'],
                was_just_assigned=was_just_assigned
            )
            
            return self.views.single_enrollment_success(enrollment_result)
            
        except Exception as e:
            self.repo.db.rollback()
            return self.views.error("enrolling student", str(e))
    
    def assign_and_enroll_student(self, student_dict, target_class_dict):
        """Assign student to class and then enroll them"""
        try:
            # Update student's class assignment
            affected_rows = self.repo.assign_student_to_class(student_dict['id'], target_class_dict['id'])
            
            if affected_rows == 0:
                return ChatResponse(
                    response="Failed to assign student to class.",
                    intent="assignment_failed",
                    data={"context": {}}
                )
            
            # Update student data with new class info
            student_dict['class_id'] = target_class_dict['id']
            student_dict['class_name'] = target_class_dict['name']
            
            # Convert back to dataclass
            student = row_to_student_enrollment((
                student_dict['id'], student_dict['first_name'], student_dict['last_name'],
                student_dict['admission_no'], student_dict['class_id'], 
                student_dict['class_name'], target_class_dict.get('level')
            ))
            
            # Get active term
            active_term_row = self.repo.get_active_term()
            if not active_term_row:
                return ChatResponse(
                    response="Class assignment successful, but no active term for enrollment.",
                    intent="assignment_success_no_term",
                    data={"context": {}},
                    suggestions=["Activate a term", "Show academic calendar"]
                )
            
            active_term = row_to_term(active_term_row[0])
            
            # Now proceed with enrollment
            return self._execute_single_enrollment(student, active_term, was_just_assigned=True)
            
        except Exception as e:
            self.repo.db.rollback()
            return self.views.error("assigning and enrolling student", str(e))
    
    def execute_bulk_enrollment(self, ready_students_dicts, term_dict):
        """Execute bulk enrollment for multiple students"""
        try:
            # Convert dicts back to student objects for consistency
            ready_students = [
                row_to_student_enrollment((
                    s['id'], s['first_name'], s['last_name'], s['admission_no'],
                    s['class_id'], s['class_name'], s.get('class_level')
                )) for s in ready_students_dicts
            ]
            
            # Execute bulk enrollment
            result = self.repo.create_bulk_enrollments(ready_students_dicts, term_dict['id'])
            
            if result['successful']:
                # Commit successful enrollments
                self.repo.db.commit()
                
                bulk_result = BulkEnrollmentResult(
                    successful_count=len(result['successful']),
                    failed_count=len(result['failed']),
                    successful_enrollments=result['successful'],
                    failed_enrollments=result['failed'],
                    term_title=term_dict['title']
                )
                
                return self.views.bulk_enrollment_success(bulk_result)
            else:
                # No successful enrollments
                self.repo.db.rollback()
                
                return ChatResponse(
                    response=f"Bulk enrollment failed - no students enrolled",
                    intent="bulk_enrollment_failed",
                    data={"context": {}},
                    suggestions=[
                        "Check database connectivity",
                        "Try individual enrollments", 
                        "Show enrollment status"
                    ]
                )
                
        except Exception as e:
            self.repo.db.rollback()
            return self.views.error("during bulk enrollment", str(e))