# handlers/enrollment/views.py
from ...blocks import (
    text, kpis, count_kpi, table, status_column, action_row, 
    error_block, empty_state, button_group, button_item
)
from ...base import ChatResponse
from .dataclasses import (
    StudentEnrollmentData, TermData, ClassData, EnrollmentResult, BulkEnrollmentResult,
    format_student_name, format_student_identifier, group_students_by_class
)

class EnrollmentViews:
    """Pure presentation layer for enrollment responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def student_not_found(self, identifier):
        """Student not found response"""
        return ChatResponse(
            response=f"No student found: {identifier}",
            intent="student_not_found",
            blocks=[
                text(f"**Student Not Found**\n\nI couldn't find a student matching '{identifier}' in your school."),
                text("**What you can do:**\n• Check the spelling of the name or admission number\n• View all students to browse available options\n• Check if the student needs to be created first")
            ],
            suggestions=[
                "List all students", 
                "Show unassigned students", 
                "Create new student"
            ]
        )
    
    def multiple_students_selection(self, students, original_message):
        """Show student selection when multiple matches found"""
        response_text = f"Found {len(students)} students matching your search:\n\n"
        
        for i, student in enumerate(students, 1):
            name = format_student_name(student)
            admission = student.admission_no or "No admission #"
            class_info = f" - {student.class_name}" if student.class_name else " - No class assigned"
            response_text += f"{i}. {name} (#{admission}){class_info}\n"
        
        response_text += "\nWhich student would you like to enroll?"
        
        context = {
            "handler": "enrollment",
            "flow": "single_enrollment", 
            "step": "select_from_multiple",
            "matched_students": [student.__dict__ for student in students],
            "original_message": original_message
        }
        
        return ChatResponse(
            response=response_text,
            intent="multiple_students_for_enrollment",
            data={"context": context},
            suggestions=[f"Select {i}" for i in range(1, min(len(students) + 1, 4))] + ["Cancel"]
        )
    
    def no_active_term(self):
        """No active term for enrollment"""
        return ChatResponse(
            response="No active term for enrollment.\n\nPlease activate a term first.",
            intent="no_active_term",
            blocks=[
                empty_state("No Active Term", "An active academic term is required for student enrollment"),
                text("**Academic terms** organize your school year into periods like Term 1, Term 2, etc. Students must be enrolled in the active term to generate invoices and track attendance."),
                text("**Next Steps:**\n• Check your academic calendar\n• Activate the current term\n• Then return to enroll students")
            ],
            suggestions=[
                "Show available terms", 
                "Activate a term", 
                "Show academic calendar"
            ]
        )
    
    def no_students_ready(self):
        """No students ready for enrollment"""
        return ChatResponse(
            response="No students ready for enrollment.\n\nAll eligible students may already be enrolled.",
            intent="no_students_ready",
            blocks=[
                empty_state("No Students Ready", "All students with class assignments appear to be enrolled"),
                text("**Students need two things to be enrolled:**\n1. **Class Assignment** - They must be assigned to a specific class\n2. **Not Already Enrolled** - They shouldn't already be enrolled in the current term"),
                text("**Check for:**\n• Students without class assignments\n• New students who need enrollment\n• Students who were unenrolled and need re-enrollment")
            ],
            suggestions=[
                "Show enrollment status", 
                "Check for unassigned students", 
                "Show current term"
            ]
        )
    
    def student_needs_class_assignment(self, student, suggested_class):
        """Student needs class assignment before enrollment"""
        student_name = format_student_name(student)
        
        blocks = []
        blocks.append(text(f"**{student_name} - Class Assignment Required**\n\n{student_name} is not assigned to any class. Students must be assigned to a class before they can be enrolled in a term."))
        
        if suggested_class:
            blocks.append(text(f"**Suggested Class:**\n• **{suggested_class.name}** ({suggested_class.level})\n• Current students: {suggested_class.current_students}/40\n• Academic year: {suggested_class.academic_year}"))
            
            confirmation_buttons = [
                button_item("Yes, assign and enroll", "query", {"message": "yes"}, "success", "md", "check"),
                button_item("Show other classes", "query", {"message": "show other classes"}, "outline", "md", "list"),
                button_item("Cancel", "query", {"message": "cancel"}, "secondary", "md", "x")
            ]
            
            blocks.append(button_group(confirmation_buttons, "horizontal", "center"))
        
        context = {
            "handler": "enrollment", 
            "flow": "single_enrollment",
            "step": "confirm_class_assignment",
            "student": student.__dict__,
            "suggested_class": suggested_class.__dict__ if suggested_class else None
        }
        
        return ChatResponse(
            response=f"{student_name} needs class assignment before enrollment.",
            intent="student_needs_class_assignment",
            data={"context": context},
            blocks=blocks,
            suggestions=[
                "Yes, assign and enroll", 
                "Show other classes", 
                "Cancel"
            ]
        )
    
    def class_selection_for_student(self, student, classes):
        """Show class selection for student assignment"""
        student_name = format_student_name(student)
        
        blocks = []
        blocks.append(text(f"**Class Assignment for {student_name}**\n\nSelect which class to assign {student_name} to before enrollment."))
        
        # Group by academic year for better organization
        classes_by_year = {}
        for cls in classes:
            year = cls.academic_year
            if year not in classes_by_year:
                classes_by_year[year] = []
            classes_by_year[year].append(cls)
        
        # Build class selection table
        columns = [
            {"key": "option", "label": "#", "width": 60, "align": "center"},
            {"key": "class_name", "label": "Class", "sortable": True},
            {"key": "level", "label": "Grade Level", "sortable": True},
            {"key": "capacity", "label": "Capacity", "align": "center"},
            {"key": "year", "label": "Year", "align": "center"}
        ]
        
        rows = []
        index = 1
        for year in sorted(classes_by_year.keys(), reverse=True):
            for cls in classes_by_year[year]:
                stream_info = f" ({cls.stream})" if cls.stream else ""
                capacity_info = f"{cls.current_students}/40"
                
                row_data = {
                    "option": str(index),
                    "class_name": f"{cls.name}{stream_info}",
                    "level": cls.level,
                    "capacity": capacity_info,
                    "year": str(cls.academic_year)
                }
                
                rows.append(action_row(row_data, "query", {"message": str(index)}))
                index += 1
        
        blocks.append(table("Available Classes", columns, rows))
        
        context = {
            "handler": "enrollment",
            "flow": "single_enrollment",
            "step": "select_class", 
            "student": student.__dict__,
            "available_classes": [cls.__dict__ for cls in classes]
        }
        
        return ChatResponse(
            response=f"Select a class for {student_name}",
            intent="class_selection_for_student",
            data={"context": context},
            blocks=blocks,
            suggestions=[f"Select {i}" for i in range(1, min(len(classes) + 1, 4))] + ["Cancel"]
        )
    
    def already_enrolled(self, student, term):
        """Student is already enrolled"""
        student_name = format_student_name(student)
        
        return ChatResponse(
            response=f"{student_name} is already enrolled in {term.title}.",
            intent="already_enrolled",
            blocks=[
                text(f"**Already Enrolled**\n\n{student_name} is already enrolled in {term.title}."),
                text("**What you can do:**\n• Check enrollment status for other students\n• Enroll a different student\n• View current enrollments")
            ],
            suggestions=[
                "Show enrollment status", 
                "Enroll different student",
                "Show current enrollments"
            ]
        )
    
    def bulk_enrollment_confirmation(self, students, term, class_breakdown):
        """Show bulk enrollment confirmation"""
        blocks = []
        
        # Header
        blocks.append(text(f"**Bulk Enrollment - {term.title}**\n\nReady to enroll {len(students)} students in the current term."))
        
        # Summary KPIs
        kpi_items = [
            count_kpi("Students Ready", len(students), "primary"),
            count_kpi("Classes Involved", len(class_breakdown), "info"),
            count_kpi("Term", term.title, "success")
        ]
        blocks.append(kpis(kpi_items))
        
        # Class breakdown table
        columns = [
            {"key": "class_name", "label": "Class", "sortable": True},
            {"key": "student_count", "label": "Students", "align": "center"},
            {"key": "sample_students", "label": "Sample Students"}
        ]
        
        rows = []
        for class_name, student_names in class_breakdown.items():
            sample = student_names[:3]
            sample_text = ", ".join(sample)
            if len(student_names) > 3:
                sample_text += f" (+{len(student_names) - 3} more)"
            
            row_data = {
                "class_name": class_name,
                "student_count": len(student_names),
                "sample_students": sample_text
            }
            
            rows.append(action_row(row_data, "query", {"message": f"show {class_name} details"}))
        
        blocks.append(table("Enrollment by Class", columns, rows))
        
        # Confirmation buttons
        confirmation_buttons = [
            button_item("Yes, enroll all", "query", {"message": "yes"}, "success", "lg", "check"),
            button_item("Show details", "query", {"message": "show details"}, "outline", "md", "list"),
            button_item("Cancel", "query", {"message": "cancel"}, "secondary", "md", "x")
        ]
        blocks.append(button_group(confirmation_buttons, "horizontal", "center"))
        
        context = {
            "handler": "enrollment",
            "flow": "bulk_enrollment",
            "step": "confirm_bulk",
            "ready_students": [student.__dict__ for student in students],
            "term": term.__dict__,
            "class_breakdown": class_breakdown
        }
        
        return ChatResponse(
            response=f"Bulk enrollment ready - {len(students)} students",
            intent="bulk_enrollment_confirmation",
            data={"context": context},
            blocks=blocks,
            suggestions=["Yes, enroll all", "No, cancel", "Show student details"]
        )
    
    def single_enrollment_success(self, result: EnrollmentResult):
        """Single student enrollment success"""
        blocks = []
        
        # Success header
        blocks.append(text(f"**Enrollment Successful! ✅**\n\n{result.student_name} has been successfully enrolled."))
        
        # Success details
        detail_items = [
            {"label": "Student", "value": result.student_name, "variant": "success"},
            {"label": "Admission #", "value": result.admission_no or "Not assigned", "variant": "primary"}
        ]
        
        if result.was_just_assigned:
            detail_items.append({"label": "Class Assignment", "value": f"✓ {result.class_name}", "variant": "success"})
        
        detail_items.extend([
            {"label": "Class", "value": result.class_name, "variant": "primary"},
            {"label": "Term", "value": result.term_title, "variant": "info"}
        ])
        
        blocks.append(kpis(detail_items))
        
        # Next steps
        next_steps = f"**Next Steps:**\n• Generate invoice for {result.student_name}\n• Notify parent about enrollment"
        blocks.append(text(next_steps))
        
        return ChatResponse(
            response=f"✅ {result.student_name} enrolled successfully!",
            intent="single_enrollment_successful",
            data={
                "student_id": result.student_id,
                "student_name": result.student_name,
                "admission_no": result.admission_no,
                "class_name": result.class_name,
                "term_title": result.term_title,
                "enrollment_id": result.enrollment_id,
                "was_just_assigned": result.was_just_assigned,
                "context": {}  # Clear context - enrollment complete
            },
            blocks=blocks,
            suggestions=[
                f"Generate invoice for student {result.admission_no or result.student_name}",
                "Show enrollment status",
                "Enroll more students"
            ]
        )
    
    def bulk_enrollment_success(self, result: BulkEnrollmentResult):
        """Bulk enrollment success"""
        blocks = []
        
        # Success header
        success_rate = (result.successful_count / (result.successful_count + result.failed_count)) * 100
        blocks.append(text(f"**Bulk Enrollment Complete - {result.term_title}**\n\n{result.successful_count} students enrolled successfully ({success_rate:.0f}% success rate)."))
        
        # Summary KPIs
        kpi_items = [
            count_kpi("Successful", result.successful_count, "success"),
            count_kpi("Failed", result.failed_count, "warning" if result.failed_count > 0 else "success"),
            count_kpi("Success Rate", f"{success_rate:.0f}%", "info")
        ]
        blocks.append(kpis(kpi_items))
        
        # Success details grouped by class
        if result.successful_enrollments:
            by_class = {}
            for enrollment in result.successful_enrollments:
                class_name = enrollment['class']
                if class_name not in by_class:
                    by_class[class_name] = []
                by_class[class_name].append(enrollment['name'])
            
            success_text = "**Successfully Enrolled:**\n\n"
            for class_name, students in by_class.items():
                success_text += f"**{class_name}**: {len(students)} students\n"
                for student_name in students[:5]:  # Show first 5
                    success_text += f"  ✓ {student_name}\n"
                if len(students) > 5:
                    success_text += f"  ... and {len(students) - 5} more\n"
                success_text += "\n"
            
            blocks.append(text(success_text))
        
        # Failure details if any
        if result.failed_enrollments:
            failure_text = f"**Failed Enrollments ({len(result.failed_enrollments)}):**\n\n"
            for failure in result.failed_enrollments[:3]:
                failure_text += f"  ✗ {failure}\n"
            if len(result.failed_enrollments) > 3:
                failure_text += f"  ... and {len(result.failed_enrollments) - 3} more failures\n"
            
            blocks.append(text(failure_text))
        
        # Next steps
        next_steps = "**Next Steps:**\n• Generate invoices for enrolled students\n• Notify parents about enrollment"
        blocks.append(text(next_steps))
        
        return ChatResponse(
            response=f"Bulk enrollment complete - {result.successful_count} students enrolled",
            intent="bulk_enrollment_successful",
            data={
                "term_title": result.term_title,
                "successful_count": result.successful_count,
                "failed_count": result.failed_count,
                "successful_enrollments": result.successful_enrollments,
                "failed_enrollments": result.failed_enrollments,
                "context": {}  # Clear context - enrollment complete
            },
            blocks=blocks,
            suggestions=[
                "Generate invoices for all students",
                "Show enrollment status",
                "Show class enrollments"
            ]
        )
    
    def enrollment_statistics(self, stats):
        """Show enrollment statistics"""
        blocks = []
        
        # Header
        school_name = self.get_school_name()
        blocks.append(text(f"**Enrollment Statistics - {school_name}**\n\nCurrent enrollment status across your school."))
        
        # Main KPIs
        kpi_items = [
            count_kpi("Total Students", stats['total_students'], "primary"),
            count_kpi("Assigned to Classes", stats['assigned_students'], "success"),
            count_kpi("Enrolled Current Term", stats['enrolled_current_term'], "info"),
            count_kpi("Ready for Enrollment", stats['ready_for_enrollment'], "warning" if stats['ready_for_enrollment'] > 0 else "success")
        ]
        blocks.append(kpis(kpi_items))
        
        # Calculate rates
        if stats['total_students'] > 0:
            assignment_rate = (stats['assigned_students'] / stats['total_students']) * 100
            enrollment_rate = (stats['enrolled_current_term'] / stats['total_students']) * 100
            
            rates_text = f"**Enrollment Rates:**\n• Assignment Rate: {assignment_rate:.1f}%\n• Enrollment Rate: {enrollment_rate:.1f}%"
            blocks.append(text(rates_text))
        
        # Action recommendations
        if stats['ready_for_enrollment'] > 0:
            blocks.append(text(f"**Action Required:**\n{stats['ready_for_enrollment']} students are ready for enrollment in the current term."))
        elif stats['assigned_students'] < stats['total_students']:
            unassigned = stats['total_students'] - stats['assigned_students']
            blocks.append(text(f"**Next Steps:**\n{unassigned} students need class assignments before they can be enrolled."))
        else:
            blocks.append(text("**Status:**\nAll students are enrolled! Your enrollment process is up to date."))
        
        suggestions = ["Show enrollment status"]
        if stats['ready_for_enrollment'] > 0:
            suggestions.insert(0, "Enroll all ready students")
        if stats['assigned_students'] < stats['total_students']:
            suggestions.append("Show unassigned students")
        
        return ChatResponse(
            response=f"Enrollment statistics - {stats['enrolled_current_term']}/{stats['total_students']} students enrolled",
            intent="enrollment_statistics",
            data=stats,
            blocks=blocks,
            suggestions=suggestions
        )
    
    def error(self, operation, error_msg):
        """Error response"""
        return ChatResponse(
            response=f"Error {operation}: {error_msg}",
            intent="error",
            blocks=[error_block(f"Error {operation.title()}", error_msg)]
        )
    
    def invalid_selection(self, context, max_options):
        """Invalid selection response"""
        return ChatResponse(
            response=f"Please select a valid option (1-{max_options}) or say 'cancel'.",
            intent="invalid_selection",
            data={"context": context},
            suggestions=[f"Select {i}" for i in range(1, min(max_options + 1, 4))] + ["Cancel"]
        )
    
    def flow_cancelled(self):
        """Flow cancellation response"""
        return ChatResponse(
            response="Enrollment cancelled.",
            intent="enrollment_cancelled",
            data={"context": {}},
            blocks=[
                text("**Enrollment Cancelled**\n\nThe enrollment process has been cancelled. You can start again anytime.")
            ],
            suggestions=[
                "Show enrollment status", 
                "Enroll students",
                "List students"
            ]
        )