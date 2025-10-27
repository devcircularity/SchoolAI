# handlers/class/repo.py
from ...base import db_execute_safe

class ClassRepo:
    """Pure data access layer for class operations"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
    
    def list_all_classes(self):
        """Get all classes with student counts"""
        query = """
            SELECT c.id, c.name, c.level, c.academic_year, c.stream,
                   COUNT(s.id) as student_count,
                   COUNT(CASE WHEN s.status = 'ACTIVE' THEN 1 END) as active_students
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id
            WHERE c.school_id = :school_id
            GROUP BY c.id, c.name, c.level, c.academic_year, c.stream
            ORDER BY c.level, c.name
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def get_class_by_name(self, class_name):
        """Get class details by name (case-insensitive search)"""
        query = """
            SELECT c.id, c.name, c.level, c.academic_year, c.stream, c.created_at,
                   COUNT(s.id) as total_students,
                   COUNT(CASE WHEN s.status = 'ACTIVE' THEN 1 END) as active_students,
                   COUNT(CASE WHEN s.gender = 'MALE' AND s.status = 'ACTIVE' THEN 1 END) as male_students,
                   COUNT(CASE WHEN s.gender = 'FEMALE' AND s.status = 'ACTIVE' THEN 1 END) as female_students
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id
            WHERE c.school_id = :school_id 
            AND (LOWER(c.name) LIKE LOWER(:class_name) OR LOWER(CONCAT(c.name, ' ', COALESCE(c.stream, ''))) LIKE LOWER(:class_name))
            GROUP BY c.id, c.name, c.level, c.academic_year, c.stream, c.created_at
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_id, 
            "class_name": f"%{class_name}%"
        })
    
    def get_empty_classes(self):
        """Get classes without any active students"""
        query = """
            SELECT c.id, c.name, c.level, c.academic_year, c.stream
            FROM classes c
            WHERE c.school_id = :school_id
            AND NOT EXISTS (
                SELECT 1 FROM students s 
                WHERE s.class_id = c.id AND s.status = 'ACTIVE'
            )
            ORDER BY c.level, c.name
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def get_class_students(self, class_id):
        """Get students in a specific class"""
        query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no, s.gender, s.status
            FROM students s
            WHERE s.class_id = :class_id AND s.status = 'ACTIVE'
            ORDER BY s.last_name, s.first_name
        """
        return db_execute_safe(self.db, query, {"class_id": class_id})
    
    def get_available_grades(self):
        """Get all available grades with educational ordering"""
        query = """
            SELECT id, label, group_name 
            FROM cbc_level 
            WHERE school_id = :school_id 
            ORDER BY 
                CASE group_name
                    WHEN 'Early Years Education (EYE)' THEN 1
                    WHEN 'Lower Primary' THEN 2
                    WHEN 'Upper Primary' THEN 3
                    WHEN 'Junior Secondary (JSS)' THEN 4
                    WHEN 'Senior Secondary' THEN 5
                    ELSE 6
                END,
                CASE 
                    WHEN label = 'PP1' THEN 1
                    WHEN label = 'PP2' THEN 2
                    WHEN label LIKE 'Grade %' THEN CAST(SUBSTRING(label FROM 7) AS INTEGER)
                    ELSE 999
                END
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def get_class_counts(self):
        """Get class statistics"""
        # Total classes
        total = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM classes WHERE school_id = :school_id",
            {"school_id": self.school_id}
        )[0][0]
        
        # Empty classes
        empty = db_execute_safe(self.db,
            """SELECT COUNT(*)
               FROM classes c
               WHERE c.school_id = :school_id
               AND NOT EXISTS (
                   SELECT 1 FROM students s 
                   WHERE s.class_id = c.id AND s.status = 'ACTIVE'
               )""",
            {"school_id": self.school_id}
        )[0][0] or 0
        
        # Classes by level
        classes_by_level = db_execute_safe(self.db,
            """SELECT c.level, COUNT(*) as class_count,
                      SUM(CASE WHEN EXISTS(
                          SELECT 1 FROM students s WHERE s.class_id = c.id AND s.status = 'ACTIVE'
                      ) THEN 1 ELSE 0 END) as classes_with_students
               FROM classes c
               WHERE c.school_id = :school_id
               GROUP BY c.level
               ORDER BY c.level""",
            {"school_id": self.school_id}
        )
        
        return {
            "total": total,
            "empty": empty,
            "active": total - empty,
            "by_level": [
                {"level": row[0], "count": row[1], "with_students": row[2]}
                for row in classes_by_level
            ]
        }
    
    def get_grade_class_counts(self, grades):
        """Get count of classes for each grade"""
        grade_class_counts = {}
        
        for grade in grades:
            count = db_execute_safe(self.db,
                "SELECT COUNT(*) FROM classes WHERE school_id = :school_id AND level = :level",
                {"school_id": self.school_id, "level": grade['label']}
            )[0][0]
            grade_class_counts[grade['label']] = count
        
        return grade_class_counts
    
    def check_class_exists(self, class_name, level=None):
        """Check if a class name already exists"""
        if level:
            query = "SELECT id FROM classes WHERE school_id = :school_id AND name = :name AND level = :level"
            params = {"school_id": self.school_id, "name": class_name, "level": level}
        else:
            query = "SELECT id FROM classes WHERE school_id = :school_id AND name = :name"
            params = {"school_id": self.school_id, "name": class_name}
        
        result = db_execute_safe(self.db, query, params)
        return len(result) > 0
    
    def check_grade_exists(self, grade_label):
        """Check if a grade already exists"""
        result = db_execute_safe(self.db,
            "SELECT id FROM cbc_level WHERE school_id = :school_id AND label = :label",
            {"school_id": self.school_id, "label": grade_label}
        )
        return len(result) > 0
    
    def check_fee_structures_exist(self, grade_label):
        """Check if fee structures already exist for this grade"""
        result = db_execute_safe(self.db,
            "SELECT COUNT(*) FROM fee_structures WHERE school_id = :school_id AND level = :level",
            {"school_id": self.school_id, "level": grade_label}
        )
        return result[0][0] > 0 if result else False
    
    def get_current_academic_year(self):
        """Get the current academic year"""
        result = db_execute_safe(self.db,
            "SELECT year FROM academic_years WHERE school_id = :school_id ORDER BY year DESC LIMIT 1",
            {"school_id": self.school_id}
        )
        return result[0][0] if result else None