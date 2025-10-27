# handlers/student/views.py
from ...blocks import (
    text, kpis, count_kpi, table, status_column, action_row, 
    chart_xy, empty_state, error_block
)
from ...base import ChatResponse
from .dataclasses import StudentRow

class StudentViews:
    """Pure presentation layer for student responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def not_found_by_admission(self, admission_no):
        """Student not found by admission number"""
        return ChatResponse(
            response=f"No student found with admission number {admission_no}.",
            intent="student_not_found",
            data={"searched_admission": admission_no},
            blocks=[
                text(f"**Student Not Found**\n\nNo student with admission number {admission_no} was found in your school.")
            ],
            suggestions=["List all students", "Create new student", "Search by name"]
        )
    
    def not_found_by_name(self, name):
        """Student not found by name"""
        return ChatResponse(
            response=f"No student found matching '{name}'.",
            intent="student_not_found",
            data={"searched_name": name},
            blocks=[
                text(f"**Student Not Found**\n\nNo student matching '{name}' was found in your school.")
            ],
            suggestions=["List all students", "Create new student", "Search by admission number"]
        )
    
    def details(self, student_row: StudentRow):
        """Format detailed student information"""
        full_name = f"{student_row.first_name} {student_row.last_name}"
        guardian_name = f"{student_row.guardian_first} {student_row.guardian_last}" if student_row.guardian_first else "No guardian assigned"
        
        response_text = f"Student Details:\n\n"
        response_text += f"Name: {full_name}\n"
        response_text += f"Admission Number: {student_row.admission_no or 'Not assigned'}\n"
        response_text += f"Status: {student_row.status}\n"
        
        if student_row.class_name:
            response_text += f"Class: {student_row.class_name} ({student_row.level})\n"
        else:
            response_text += f"Class: Not assigned\n"
        
        response_text += f"\nGuardian Information:\n"
        response_text += f"Name: {guardian_name}\n"
        if student_row.guardian_phone:
            response_text += f"Phone: {student_row.guardian_phone}\n"
        if student_row.guardian_email:
            response_text += f"Email: {student_row.guardian_email}\n"
        if student_row.relationship:
            response_text += f"Relationship: {student_row.relationship}\n"
        
        suggestions = []
        if not student_row.class_name:
            suggestions.append("Assign to class")
        if not student_row.guardian_first:
            suggestions.append("Add guardian information")
        
        suggestions.extend(["List all students", "Show student count", "Create new student"])
        
        return ChatResponse(
            response=response_text,
            intent="student_details",
            data={
                "student": {
                    "id": str(student_row.id),
                    "name": full_name,
                    "admission_no": student_row.admission_no,
                    "status": student_row.status,
                    "class": student_row.class_name,
                    "level": student_row.level,
                    "guardian_name": guardian_name,
                    "guardian_phone": student_row.guardian_phone,
                    "guardian_email": student_row.guardian_email,
                    "has_class": bool(student_row.class_name),
                    "has_guardian": bool(student_row.guardian_first)
                }
            },
            suggestions=suggestions
        )
    
    def multiple_results(self, students, search_term):
        """Show multiple search results"""
        response_text = f"Found {len(students)} students matching '{search_term}':\n\n"
        for student in students[:10]:  # Limit to 10 results
            full_name = f"{student[1]} {student[2]}"
            admission = student[3] or "No admission #"
            class_info = f" - {student[5]}" if student[5] else " - No class"
            response_text += f"• {full_name} (#{admission}){class_info}\n"
        
        if len(students) > 10:
            response_text += f"\n*Showing first 10 of {len(students)} results*"
        
        return ChatResponse(
            response=response_text,
            intent="multiple_students_found",
            data={
                "students": [
                    {
                        "id": str(s[0]),
                        "name": f"{s[1]} {s[2]}",
                        "admission_no": s[3],
                        "class": s[5]
                    } for s in students
                ]
            },
            suggestions=[
                f"Show student {students[0][3]}" if students[0][3] else "Show student details",
                "List all students"
            ]
        )
    
    def list_table(self, students):
        """Rich table display for student list"""
        if not students:
            return ChatResponse(
                response="No students found in your school.",
                intent="no_students",
                blocks=[
                    text("**No Students Found**\n\nYour school doesn't have any students registered yet."),
                    text("Get started by creating your first student with their guardian information.")
                ],
                suggestions=["Create new student", "Import students", "Student registration guide"]
            )
        
        blocks = []
        school_name = self.get_school_name()
        
        # Header
        blocks.append(text(f"**Students in {school_name}**\n\nComplete list of registered students with their class assignments and guardian information."))
        
        # Statistics
        assigned_count = sum(1 for s in students if s[4])  # has class_name
        unassigned_count = len(students) - assigned_count
        with_guardians = sum(1 for s in students if s[7])  # has guardian_first
        
        kpi_items = [
            count_kpi("Total Students", len(students), "primary"),
            count_kpi("Assigned to Classes", assigned_count, "success"),
            count_kpi("With Guardians", with_guardians, "primary")
        ]
        
        if unassigned_count > 0:
            kpi_items.append(
                count_kpi("Unassigned", unassigned_count, "warning",
                        action={"type": "query", "payload": {"message": "show unassigned students"}})
            )
        
        blocks.append(kpis(kpi_items))
        
        # Table
        columns = [
            {"key": "student_name", "label": "Student Name", "sortable": True},
            {"key": "admission_no", "label": "Admission #", "sortable": True, "width": 120},
            {"key": "class_assignment", "label": "Class", "sortable": True},
            {"key": "guardian_name", "label": "Guardian", "sortable": True},
            {"key": "contact", "label": "Contact"},
            status_column("status", "Status", {
                "ACTIVE": "success",
                "INACTIVE": "warning", 
                "GRADUATED": "info"
            })
        ]
        
        rows = []
        for student in students:
            student_name = f"{student[1]} {student[2]}"
            admission_no = student[3] or "Not assigned"
            class_info = f"{student[4]} ({student[5]})" if student[4] else "Not assigned"
            guardian_name = f"{student[7]} {student[8]}" if student[7] else "No guardian"
            guardian_phone = student[9] or "No phone"
            status = student[6]
            
            row_data = {
                "student_name": student_name,
                "admission_no": admission_no,
                "class_assignment": class_info,
                "guardian_name": guardian_name,
                "contact": guardian_phone,
                "status": status
            }
            
            rows.append(action_row(row_data, "query", {"message": f"show student {admission_no} details"}))
        
        table_actions = [
            {"label": "Create New Student", "type": "query", "payload": {"message": "create new student"}},
            {"label": "Show Unassigned", "type": "query", "payload": {"message": "show unassigned students"}},
        ]
        
        blocks.append(table("Student Directory", columns, rows, 
                          pagination={"mode": "client", "page": 1, "pageSize": 25, "total": len(rows)},
                          actions=table_actions))
        
        # Class distribution chart
        if len(students) > 5 and assigned_count > 0:
            class_distribution = {}
            for student in students:
                if student[4]:  # has class
                    class_name = student[4]
                    class_distribution[class_name] = class_distribution.get(class_name, 0) + 1
            
            if len(class_distribution) > 1:
                chart_data = [
                    {"class": class_name, "students": count}
                    for class_name, count in sorted(class_distribution.items(), key=lambda x: x[1], reverse=True)
                ]
                
                blocks.append(chart_xy("Students by Class", "bar", "class", "students",
                                     [{"name": "Students", "data": chart_data}],
                                     {"height": 200, "yAxisFormat": "integer"}))
        
        suggestions = ["Create new student", "Show student details"]
        if unassigned_count > 0:
            suggestions.insert(0, "Show unassigned students")
        
        return ChatResponse(
            response=f"Found {len(students)} students ({assigned_count} assigned to classes)",
            intent="student_list",
            data={
                "total_students": len(students),
                "assigned_count": assigned_count,
                "unassigned_count": unassigned_count,
                "with_guardians": with_guardians
            },
            blocks=blocks,
            suggestions=suggestions
        )
    
    def count_summary(self, stats):
        """Student count with breakdown"""
        school_name = self.get_school_name()
        
        blocks = []
        blocks.append(text(f"**Student Statistics - {school_name}**\n\nDetailed breakdown of student information and assignments."))
        
        kpi_items = [
            count_kpi("Total Students", stats["total"], "primary"),
            count_kpi("Active Students", stats["active"], "success"),
            count_kpi("With Guardians", stats["with_guardians"], "primary"),
            count_kpi("Assigned to Classes", stats["assigned"], "success"),
            count_kpi("Enrolled Current Term", stats["enrolled"], "primary")
        ]
        
        blocks.append(kpis(kpi_items))
        
        response_text = f"Student Statistics for {school_name}:\n\n"
        response_text += f"Total Students: {stats['total']}\n"
        response_text += f"Active Students: {stats['active']}\n"
        response_text += f"With Guardians: {stats['with_guardians']}\n"
        response_text += f"Assigned to Classes: {stats['assigned']}\n"
        response_text += f"Enrolled Current Term: {stats['enrolled']}\n"
        
        if stats["total"] > 0:
            guardian_rate = (stats["with_guardians"] / stats["total"]) * 100
            assignment_rate = (stats["assigned"] / stats["total"]) * 100
            enrollment_rate = (stats["enrolled"] / stats["total"]) * 100 if stats["active"] > 0 else 0
            response_text += f"\nGuardian Info Rate: {guardian_rate:.1f}%\n"
            response_text += f"Assignment Rate: {assignment_rate:.1f}%\n"
            response_text += f"Enrollment Rate: {enrollment_rate:.1f}%"
        
        suggestions = ["List all students"]
        if stats["with_guardians"] < stats["total"]:
            suggestions.append("Show students without guardians")
        if stats["assigned"] < stats["total"]:
            suggestions.append("Show unassigned students")
        if stats["enrolled"] < stats["assigned"]:
            suggestions.append("Enroll students")
        
        return ChatResponse(
            response=response_text,
            intent="student_count",
            data=stats,
            blocks=blocks,
            suggestions=suggestions
        )
    
    def unassigned_list(self, unassigned):
        """Show unassigned students"""
        if not unassigned:
            return ChatResponse(
                response="All students are assigned to classes.",
                intent="all_students_assigned",
                blocks=[text("**All Students Assigned**\n\nGreat! All your students are currently assigned to classes.")],
                suggestions=["List all students", "Show class enrollments", "Enroll students in terms"]
            )
        
        response_text = f"Students without class assignments ({len(unassigned)}):\n\n"
        
        student_list = []
        for student in unassigned:
            student_id = str(student[0])
            full_name = f"{student[1]} {student[2]}"
            admission_no = student[3]
            status = student[4]
            guardian_name = f"{student[5]} {student[6]}" if student[5] else "No guardian"
            guardian_phone = student[7] or "No phone"
            
            status_icon = "✓" if status == "ACTIVE" else "✗"
            admission_info = f" (#{admission_no})" if admission_no else ""
            
            response_text += f"{status_icon} {full_name}{admission_info}\n"
            response_text += f"   Guardian: {guardian_name} ({guardian_phone})\n\n"
            
            student_list.append({
                "id": student_id,
                "name": full_name,
                "admission_no": admission_no,
                "status": status,
                "guardian": guardian_name,
                "guardian_phone": guardian_phone
            })
        
        response_text += f"These students need class assignments before they can be enrolled in terms."
        
        return ChatResponse(
            response=response_text,
            intent="unassigned_students",
            data={"unassigned_students": student_list, "count": len(unassigned)},
            suggestions=["Show available classes", "Assign students to classes", "Create new class"]
        )
    
    def overview(self):
        """General student overview"""
        return ChatResponse(
            response="I can help you with student information and management. What would you like to know about your students?",
            intent="student_general",
            blocks=[text("**Student Management**\n\nI can help you with student information, registration, and management tasks.")],
            suggestions=["Create new student", "List all students", "Show student count", "Find student by admission number"]
        )
    
    def error(self, operation, error_msg):
        """Error response"""
        return ChatResponse(
            response=f"Error {operation}: {error_msg}",
            intent="error",
            blocks=[error_block(f"Error {operation.title()}", error_msg)]
        )