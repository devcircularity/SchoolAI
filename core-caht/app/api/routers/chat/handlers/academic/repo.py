# handlers/academic/repo.py
from ...base import db_execute_safe, db_execute_non_select

class AcademicRepo:
    """Pure data access layer for academic operations"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
    
    def get_current_term(self):
        """Get currently active academic term"""
        return db_execute_safe(self.db,
            """SELECT t.id, t.title, t.state, t.start_date, t.end_date,
                      y.year, y.title as year_title
               FROM academic_terms t
               JOIN academic_years y ON t.year_id = y.id
               WHERE t.school_id = :school_id AND t.state = 'ACTIVE'
               ORDER BY y.year DESC, t.term ASC
               LIMIT 1""",
            {"school_id": self.school_id}
        )
    
    def get_enrollment_stats(self, term_id):
        """Get enrollment statistics for a term"""
        return db_execute_safe(self.db,
            """SELECT COUNT(*) as total_enrollments,
                      COUNT(DISTINCT student_id) as unique_students,
                      COUNT(DISTINCT c.id) as enrolled_classes
               FROM enrollments e
               LEFT JOIN students s ON e.student_id = s.id
               LEFT JOIN classes c ON s.class_id = c.id
               WHERE e.school_id = :school_id AND e.term_id = :term_id""",
            {"school_id": self.school_id, "term_id": term_id}
        )
    
    def get_active_terms(self):
        """Get all currently active terms"""
        return db_execute_safe(self.db,
            """SELECT t.id, t.title, y.year
               FROM academic_terms t
               JOIN academic_years y ON t.year_id = y.id
               WHERE t.school_id = :school_id AND t.state = 'ACTIVE'""",
            {"school_id": self.school_id}
        )
    
    def get_available_terms(self):
        """Get terms available for activation (PLANNED state)"""
        return db_execute_safe(self.db,
            """SELECT t.id, t.title, t.state, y.year, t.start_date, t.end_date, t.term
               FROM academic_terms t
               JOIN academic_years y ON t.year_id = y.id
               WHERE t.school_id = :school_id AND t.state = 'PLANNED'
               ORDER BY y.year DESC, t.term ASC""",
            {"school_id": self.school_id}
        )
    
    def get_academic_calendar(self):
        """Get complete academic calendar"""
        return db_execute_safe(self.db,
            """SELECT y.year, y.title as year_title, y.state as year_state,
                      t.term, t.title as term_title, t.state as term_state,
                      t.start_date, t.end_date, t.id as term_id
               FROM academic_years y
               LEFT JOIN academic_terms t ON y.id = t.year_id
               WHERE y.school_id = :school_id
               ORDER BY y.year DESC, t.term ASC""",
            {"school_id": self.school_id}
        )
    
    def get_setup_stats(self):
        """Get academic setup statistics"""
        year_count = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM academic_years WHERE school_id = :school_id",
            {"school_id": self.school_id}
        )[0][0]
        
        term_count = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM academic_terms WHERE school_id = :school_id",
            {"school_id": self.school_id}
        )[0][0]
        
        active_terms = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM academic_terms WHERE school_id = :school_id AND state = 'ACTIVE'",
            {"school_id": self.school_id}
        )[0][0]
        
        return {
            "year_count": year_count,
            "term_count": term_count,
            "active_terms": active_terms
        }
    
    def deactivate_all_terms(self):
        """Deactivate all currently active terms"""
        return db_execute_non_select(self.db,
            "UPDATE academic_terms SET state = 'CLOSED' WHERE school_id = :school_id AND state = 'ACTIVE'",
            {"school_id": self.school_id}
        )
    
    def activate_term(self, term_id):
        """Activate a specific term"""
        return db_execute_non_select(self.db,
            "UPDATE academic_terms SET state = 'ACTIVE' WHERE id = :term_id AND school_id = :school_id",
            {"term_id": term_id, "school_id": self.school_id}
        )
    
    def get_term_by_id(self, term_id):
        """Get term details by ID"""
        return db_execute_safe(self.db,
            """SELECT t.id, t.title, t.state, t.start_date, t.end_date,
                      y.year, y.title as year_title
               FROM academic_terms t
               JOIN academic_years y ON t.year_id = y.id
               WHERE t.id = :term_id AND t.school_id = :school_id""",
            {"term_id": term_id, "school_id": self.school_id}
        )