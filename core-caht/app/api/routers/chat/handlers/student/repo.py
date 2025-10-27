# handlers/student/repo.py
from ...base import db_execute_safe

class StudentRepo:
    """Pure data access layer for student operations"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
    
    def get_by_admission(self, admission_no):
        """Get student by admission number with full details"""
        query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no, s.status,
                   c.name as class_name, c.level,
                   g.first_name as guardian_first, g.last_name as guardian_last,
                   g.phone as guardian_phone, g.email as guardian_email, g.relationship
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN guardians g ON s.primary_guardian_id = g.id
            WHERE s.school_id = :school_id AND s.admission_no = :admission_no
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_id, 
            "admission_no": admission_no
        })
    
    def search_by_name(self, name):
        """Search students by name pattern"""
        query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no, s.status,
                   c.name as class_name, c.level,
                   g.first_name as guardian_first, g.last_name as guardian_last,
                   g.phone as guardian_phone, g.email as guardian_email, g.relationship
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN guardians g ON s.primary_guardian_id = g.id
            WHERE s.school_id = :school_id 
            AND (LOWER(s.first_name) LIKE :name_pattern 
                 OR LOWER(s.last_name) LIKE :name_pattern
                 OR LOWER(s.first_name || ' ' || s.last_name) LIKE :full_name_pattern)
            ORDER BY s.first_name, s.last_name
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_id,
            "name_pattern": f"%{name.lower()}%",
            "full_name_pattern": f"%{name.lower()}%"
        })
    
    def list_50(self):
        """Get recent 50 students with full details"""
        query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no, 
                   c.name as class_name, c.level, s.status,
                   g.first_name as guardian_first, g.last_name as guardian_last,
                   g.phone as guardian_phone, g.email as guardian_email
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN guardians g ON s.primary_guardian_id = g.id
            WHERE s.school_id = :school_id
            ORDER BY s.admission_no DESC, s.first_name, s.last_name
            LIMIT 50
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def get_unassigned(self):
        """Get students without class assignments"""
        query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no, s.status,
                   g.first_name as guardian_first, g.last_name as guardian_last,
                   g.phone as guardian_phone
            FROM students s
            LEFT JOIN guardians g ON s.primary_guardian_id = g.id
            WHERE s.school_id = :school_id AND s.class_id IS NULL
            ORDER BY s.admission_no DESC, s.first_name, s.last_name
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def get_counts(self):
        """Get student statistics"""
        # Total students
        total = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM students WHERE school_id = :school_id",
            {"school_id": self.school_id}
        )[0][0]
        
        # Active students
        active = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM students WHERE school_id = :school_id AND status = 'ACTIVE'",
            {"school_id": self.school_id}
        )[0][0]
        
        # With class assignments
        assigned = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM students WHERE school_id = :school_id AND class_id IS NOT NULL",
            {"school_id": self.school_id}
        )[0][0]
        
        # With guardians
        with_guardians = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM students WHERE school_id = :school_id AND primary_guardian_id IS NOT NULL",
            {"school_id": self.school_id}
        )[0][0]
        
        # Enrolled in current term
        enrolled = db_execute_safe(self.db,
            """SELECT COUNT(DISTINCT e.student_id)
               FROM enrollments e
               JOIN academic_terms t ON e.term_id = t.id
               WHERE e.school_id = :school_id AND t.state = 'ACTIVE'""",
            {"school_id": self.school_id}
        )[0][0] or 0
        
        return {
            "total": total,
            "active": active,
            "assigned": assigned,
            "with_guardians": with_guardians,
            "enrolled": enrolled
        }