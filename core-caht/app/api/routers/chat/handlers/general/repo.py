# handlers/general/repo.py
from ...base import db_execute_safe

class GeneralRepo:
    """Pure data access layer for general system information"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
    
    def get_school_name(self):
        """Get school name"""
        try:
            result = db_execute_safe(self.db,
                "SELECT name FROM schools WHERE id = :school_id",
                {"school_id": self.school_id}
            )
            return result[0][0] if result else "Your School"
        except:
            return "Your School"
    
    def get_system_status(self):
        """Get comprehensive system setup status"""
        try:
            # Academic setup
            academic_years = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM academic_years WHERE school_id = :school_id",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            active_terms = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM academic_terms WHERE school_id = :school_id AND state = 'ACTIVE'",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            # Structure setup
            grades = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM cbc_level WHERE school_id = :school_id",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            classes = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM classes WHERE school_id = :school_id",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            # Student data
            students = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM students WHERE school_id = :school_id AND status = 'ACTIVE'",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            unassigned_students = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM students WHERE school_id = :school_id AND class_id IS NULL AND status = 'ACTIVE'",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            # Current term enrollment and invoice data
            unenrolled_students = students  
            students_without_invoices = students  
            
            if active_terms > 0:
                enrolled_students = db_execute_safe(self.db,
                    """SELECT COUNT(DISTINCT e.student_id)
                       FROM enrollments e
                       JOIN academic_terms t ON e.term_id = t.id
                       WHERE e.school_id = :school_id AND t.state = 'ACTIVE' AND e.status = 'ENROLLED'""",
                    {"school_id": self.school_id}
                )[0][0] or 0
                
                unenrolled_students = max(0, students - enrolled_students)
                
                # Students with invoices in current term
                with_invoices = db_execute_safe(self.db,
                    """SELECT COUNT(DISTINCT i.student_id)
                       FROM invoices i
                       JOIN academic_terms t ON i.term = t.term 
                       JOIN academic_years y ON i.year = y.year AND t.year_id = y.id
                       WHERE i.school_id = :school_id AND t.state = 'ACTIVE'""",
                    {"school_id": self.school_id}
                )[0][0] or 0
                
                students_without_invoices = max(0, enrolled_students - with_invoices)
            
            return {
                "academic_years": academic_years,
                "active_terms": active_terms,
                "grades": grades,
                "classes": classes,
                "students": students,
                "unassigned_students": unassigned_students,
                "unenrolled_students": unenrolled_students,
                "students_without_invoices": students_without_invoices
            }
            
        except Exception as e:
            # Return minimal status if database queries fail
            return {
                "academic_years": 0,
                "active_terms": 0,
                "grades": 0,
                "classes": 0,
                "students": 0,
                "unassigned_students": 0,
                "unenrolled_students": 0,
                "students_without_invoices": 0
            }
    
    def get_system_usage_stats(self):
        """Get system usage statistics"""
        try:
            students = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM students WHERE school_id = :school_id",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            classes = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM classes WHERE school_id = :school_id",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            invoices = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM invoices WHERE school_id = :school_id",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            payments = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM payments WHERE school_id = :school_id",
                {"school_id": self.school_id}
            )[0][0] or 0
            
            return {
                "students": students,
                "classes": classes,
                "invoices": invoices,
                "payments": payments
            }
        except:
            return {"students": 0, "classes": 0, "invoices": 0, "payments": 0}