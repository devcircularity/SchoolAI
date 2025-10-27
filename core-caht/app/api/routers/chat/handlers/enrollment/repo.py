# handlers/enrollment/repo.py
from ...base import db_execute_safe, db_execute_non_select
import uuid
from datetime import datetime

class EnrollmentRepo:
    """Pure data access layer for enrollment operations"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
    
    def find_student_by_admission(self, admission_no):
        """Find student by admission number"""
        query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id, 
                   c.name as class_name, c.level
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE s.school_id = :school_id AND s.admission_no = :admission_no 
            AND s.status = 'ACTIVE'
            LIMIT 1
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_id, 
            "admission_no": admission_no
        })
    
    def find_students_by_name(self, name):
        """Find students by name (fuzzy matching)"""
        name_parts = name.split()
        
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
            
            query = """
                SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id,
                       c.name as class_name, c.level
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.id
                WHERE s.school_id = :school_id AND s.status = 'ACTIVE'
                AND (LOWER(s.first_name) LIKE :first_pattern 
                     OR LOWER(s.last_name) LIKE :last_pattern
                     OR LOWER(s.first_name || ' ' || s.last_name) LIKE :full_pattern)
                ORDER BY s.first_name, s.last_name
                LIMIT 10
            """
            params = {
                "school_id": self.school_id,
                "first_pattern": f"%{first_name.lower()}%",
                "last_pattern": f"%{last_name.lower()}%", 
                "full_pattern": f"%{name.lower()}%"
            }
        else:
            query = """
                SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id,
                       c.name as class_name, c.level
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.id
                WHERE s.school_id = :school_id AND s.status = 'ACTIVE'
                AND (LOWER(s.first_name) LIKE :pattern OR LOWER(s.last_name) LIKE :pattern)
                ORDER BY s.first_name, s.last_name
                LIMIT 10
            """
            params = {
                "school_id": self.school_id,
                "pattern": f"%{name.lower()}%"
            }
        
        return db_execute_safe(self.db, query, params)
    
    def get_active_term(self):
        """Get active academic term"""
        query = """
            SELECT t.id, t.title, y.year
            FROM academic_terms t
            JOIN academic_years y ON t.year_id = y.id
            WHERE t.school_id = :school_id AND t.state = 'ACTIVE'
            LIMIT 1
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def get_students_ready_for_enrollment(self, term_id):
        """Get students ready for enrollment (assigned to classes but not enrolled in term)"""
        query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id,
                   c.name as class_name, c.level
            FROM students s
            JOIN classes c ON s.class_id = c.id
            WHERE s.school_id = :school_id 
            AND s.status = 'ACTIVE'
            AND NOT EXISTS (
                SELECT 1 FROM enrollments e 
                WHERE e.student_id = s.id AND e.term_id = :term_id
            )
            ORDER BY c.name, s.first_name, s.last_name
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_id, 
            "term_id": term_id
        })
    
    def get_available_classes_for_assignment(self):
        """Get all available classes for student assignment"""
        query = """
            SELECT c.id, c.name, c.level, c.academic_year, c.stream,
                   COUNT(s.id) as current_students
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'ACTIVE'
            WHERE c.school_id = :school_id
            GROUP BY c.id, c.name, c.level, c.academic_year, c.stream
            ORDER BY c.academic_year DESC, c.level, c.name
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def suggest_class_for_student(self, student_data):
        """Suggest appropriate class for student based on available info"""
        query = """
            SELECT c.id, c.name, c.level, c.academic_year, c.stream,
                   COUNT(s.id) as current_students
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'ACTIVE'
            WHERE c.school_id = :school_id
            GROUP BY c.id, c.name, c.level, c.academic_year, c.stream
            HAVING COUNT(s.id) < 40
            ORDER BY c.academic_year DESC, c.level, c.name
            LIMIT 5
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def is_already_enrolled(self, student_id, term_id):
        """Check if student is already enrolled in the term"""
        query = """
            SELECT id FROM enrollments 
            WHERE school_id = :school_id 
            AND student_id = :student_id 
            AND term_id = :term_id
            LIMIT 1
        """
        result = db_execute_safe(self.db, query, {
            "school_id": self.school_id,
            "student_id": student_id,
            "term_id": term_id
        })
        return bool(result)
    
    def assign_student_to_class(self, student_id, class_id):
        """Assign student to a class"""
        query = """
            UPDATE students 
            SET class_id = :class_id, updated_at = CURRENT_TIMESTAMP
            WHERE id = :student_id AND school_id = :school_id
        """
        return db_execute_non_select(self.db, query, {
            "class_id": class_id,
            "student_id": student_id,
            "school_id": self.school_id
        })
    
    def create_enrollment(self, student_id, class_id, term_id):
        """Create single enrollment record"""
        enrollment_id = str(uuid.uuid4())
        query = """
            INSERT INTO enrollments (id, school_id, student_id, class_id, term_id, status, created_at, updated_at)
            VALUES (:id, :school_id, :student_id, :class_id, :term_id, 'ENROLLED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        affected_rows = db_execute_non_select(self.db, query, {
            "id": enrollment_id,
            "school_id": self.school_id,
            "student_id": student_id,
            "class_id": class_id,
            "term_id": term_id
        })
        
        return {"enrollment_id": enrollment_id, "affected_rows": affected_rows}
    
    def create_bulk_enrollments(self, students, term_id):
        """Create multiple enrollment records"""
        successful = []
        failed = []
        
        for student in students:
            try:
                result = self.create_enrollment(
                    student['id'], 
                    student['class_id'], 
                    term_id
                )
                
                if result['affected_rows'] > 0:
                    successful.append({
                        "student_id": student['id'],
                        "name": f"{student['first_name']} {student['last_name']}",
                        "admission_no": student['admission_no'],
                        "class": student.get('class_name', 'Unknown'),
                        "enrollment_id": result['enrollment_id']
                    })
                else:
                    failed.append(f"{student['first_name']} {student['last_name']} - No rows affected")
                    
            except Exception as e:
                failed.append(f"{student['first_name']} {student['last_name']} - {str(e)}")
                continue
        
        return {"successful": successful, "failed": failed}
    
    def get_enrollment_statistics(self):
        """Get enrollment statistics for the school"""
        stats = {}
        
        # Total students
        result = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM students WHERE school_id = :school_id AND status = 'ACTIVE'",
            {"school_id": self.school_id}
        )
        stats['total_students'] = result[0][0] if result else 0
        
        # Students with class assignments
        result = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM students WHERE school_id = :school_id AND status = 'ACTIVE' AND class_id IS NOT NULL",
            {"school_id": self.school_id}
        )
        stats['assigned_students'] = result[0][0] if result else 0
        
        # Enrolled in current term
        result = db_execute_safe(self.db,
            """SELECT COUNT(DISTINCT e.student_id)
               FROM enrollments e
               JOIN academic_terms t ON e.term_id = t.id
               WHERE e.school_id = :school_id AND t.state = 'ACTIVE'""",
            {"school_id": self.school_id}
        )
        stats['enrolled_current_term'] = result[0][0] if result else 0
        
        # Ready for enrollment
        active_term = self.get_active_term()
        if active_term:
            ready_students = self.get_students_ready_for_enrollment(active_term[0][0])
            stats['ready_for_enrollment'] = len(ready_students)
        else:
            stats['ready_for_enrollment'] = 0
        
        return stats