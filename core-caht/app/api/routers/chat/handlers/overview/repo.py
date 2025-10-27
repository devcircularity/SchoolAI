# handlers/overview/repo.py
from ...base import db_execute_safe

class OverviewRepo:
    """Pure data access layer for overview operations"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
    
    def get_student_statistics(self):
        """Get comprehensive student statistics"""
        return db_execute_safe(self.db,
            """SELECT 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE status = 'ACTIVE') as active,
                   COUNT(*) FILTER (WHERE class_id IS NULL AND status = 'ACTIVE') as unassigned
               FROM students 
               WHERE school_id = :school_id""",
            {"school_id": self.school_id}
        )[0]
    
    def get_class_statistics(self):
        """Get class statistics"""
        return db_execute_safe(self.db,
            """SELECT 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE EXISTS(
                       SELECT 1 FROM students s 
                       WHERE s.class_id = c.id AND s.status = 'ACTIVE'
                   )) as with_students
               FROM classes c
               WHERE school_id = :school_id""",
            {"school_id": self.school_id}
        )[0]
    
    def get_academic_statistics(self):
        """Get academic year and term statistics"""
        return db_execute_safe(self.db,
            """SELECT 
                   (SELECT COUNT(*) FROM academic_years WHERE school_id = :school_id) as years,
                   (SELECT COUNT(*) FROM academic_terms WHERE school_id = :school_id) as terms,
                   (SELECT COUNT(*) FROM academic_terms WHERE school_id = :school_id AND state = 'ACTIVE') as active_terms
            """,
            {"school_id": self.school_id}
        )[0]
    
    def get_current_term_enrollment(self):
        """Get current term enrollment count"""
        result = db_execute_safe(self.db,
            """SELECT COUNT(DISTINCT e.student_id)
               FROM enrollments e
               JOIN academic_terms t ON e.term_id = t.id
               WHERE e.school_id = :school_id AND t.state = 'ACTIVE'""",
            {"school_id": self.school_id}
        )
        return result[0][0] if result else 0
    
    def get_current_term_info(self):
        """Get current active term information"""
        return db_execute_safe(self.db,
            """SELECT t.id, t.title, t.state, y.year, y.title as year_title
               FROM academic_terms t
               JOIN academic_years y ON t.year_id = y.id
               WHERE t.school_id = :school_id AND t.state = 'ACTIVE'
               LIMIT 1""",
            {"school_id": self.school_id}
        )
    
    def get_class_breakdown(self):
        """Get class breakdown with student counts"""
        return db_execute_safe(self.db,
            """SELECT c.name, c.level, COUNT(s.id) as student_count
               FROM classes c
               LEFT JOIN students s ON c.id = s.class_id AND s.status = 'ACTIVE'
               WHERE c.school_id = :school_id
               GROUP BY c.id, c.name, c.level
               ORDER BY c.level, c.name""",
            {"school_id": self.school_id}
        )
    
    def get_recent_enrollments(self, days=7):
        """Get recent enrollment activity"""
        return db_execute_safe(self.db,
            """SELECT COUNT(*), MAX(created_at)
               FROM enrollments e
               WHERE e.school_id = :school_id 
               AND e.created_at >= NOW() - INTERVAL '%s days'""" % days,
            {"school_id": self.school_id}
        )
    
    def get_recent_classes(self, days=7):
        """Get recent class creation activity"""
        return db_execute_safe(self.db,
            """SELECT COUNT(*), MAX(created_at)
               FROM classes c
               WHERE c.school_id = :school_id 
               AND c.created_at >= NOW() - INTERVAL '%s days'""" % days,
            {"school_id": self.school_id}
        )
    
    def get_fee_statistics(self):
        """Get fee and payment statistics"""
        try:
            return db_execute_safe(self.db,
                """SELECT 
                       COUNT(DISTINCT fs.id) as fee_structures,
                       COUNT(DISTINCT i.id) as total_invoices,
                       COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'PENDING') as pending_invoices,
                       COALESCE(SUM(p.amount), 0) as total_payments
                   FROM fee_structures fs
                   LEFT JOIN invoices i ON fs.school_id = i.school_id
                   LEFT JOIN payments p ON i.id = p.invoice_id
                   WHERE fs.school_id = :school_id""",
                {"school_id": self.school_id}
            )
        except Exception:
            # Return zeros if fee tables don't exist or have issues
            return [(0, 0, 0, 0)]