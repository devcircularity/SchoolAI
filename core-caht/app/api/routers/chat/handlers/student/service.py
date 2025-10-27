# handlers/student/service.py
from ...base import ChatResponse
from .repo import StudentRepo
from .views import StudentViews
from .dataclasses import row_to_student

class StudentService:
    """Business logic layer for student operations"""
    
    def __init__(self, db, school_id, get_school_name):
        self.repo = StudentRepo(db, school_id)
        self.views = StudentViews(get_school_name)
    
    def search_by_admission(self, admission_no):
        """Search student by admission number"""
        try:
            rows = self.repo.get_by_admission(admission_no)
            if not rows:
                return self.views.not_found_by_admission(admission_no)
            
            student_row = row_to_student(rows[0])
            return self.views.details(student_row)
        except Exception as e:
            return self.views.error("searching for student", str(e))
    
    def search_by_name(self, name):
        """Search student by name"""
        try:
            rows = self.repo.search_by_name(name)
            if not rows:
                return self.views.not_found_by_name(name)
            
            if len(rows) == 1:
                student_row = row_to_student(rows[0])
                return self.views.details(student_row)
            else:
                return self.views.multiple_results(rows, name)
        except Exception as e:
            return self.views.error("searching for student", str(e))
    
    def list_students(self):
        """List all students"""
        try:
            rows = self.repo.list_50()
            return self.views.list_table(rows)
        except Exception as e:
            return self.views.error("listing students", str(e))
    
    def show_unassigned(self):
        """Show unassigned students"""
        try:
            rows = self.repo.get_unassigned()
            return self.views.unassigned_list(rows)
        except Exception as e:
            return self.views.error("getting unassigned students", str(e))
    
    def show_count(self):
        """Show student statistics"""
        try:
            stats = self.repo.get_counts()
            return self.views.count_summary(stats)
        except Exception as e:
            return self.views.error("getting student count", str(e))
    
    def show_overview(self):
        """Show general overview"""
        return self.views.overview()