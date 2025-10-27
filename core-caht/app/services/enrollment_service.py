# app/services/enrollment_service.py - Enrollment business logic
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.enrollment import Enrollment
from app.schemas.enrollment import EnrollmentCreate
from typing import Dict, Any
import uuid

class EnrollmentService:
    def __init__(self, db: Session, school_id: str):
        self.db = db
        self.school_id = school_id
    
    def enroll_student(self, enrollment_data: EnrollmentCreate) -> Dict[str, Any]:
        """
        Enroll a student in a class for a specific term.
        This should trigger invoice generation.
        """
        try:
            # Check if student is already enrolled for this term
            existing = self.db.execute(
                text("""
                    SELECT id FROM enrollments 
                    WHERE school_id = :school_id 
                    AND student_id = :student_id 
                    AND term_id = :term_id
                """),
                {
                    "school_id": self.school_id,
                    "student_id": str(enrollment_data.student_id),
                    "term_id": str(enrollment_data.term_id)
                }
            ).first()
            
            if existing:
                return {"success": False, "message": "Student already enrolled for this term"}
            
            # Create enrollment
            enrollment_id = str(uuid.uuid4())
            self.db.execute(
                text("""
                    INSERT INTO enrollments (id, school_id, student_id, class_id, term_id, enrolled_date, status, invoice_generated)
                    VALUES (:id, :school_id, :student_id, :class_id, :term_id, :enrolled_date, 'ENROLLED', false)
                """),
                {
                    "id": enrollment_id,
                    "school_id": self.school_id,
                    "student_id": str(enrollment_data.student_id),
                    "class_id": str(enrollment_data.class_id),
                    "term_id": str(enrollment_data.term_id),
                    "enrolled_date": enrollment_data.enrolled_date or date.today()
                }
            )
            
            # Update student's current class
            self.db.execute(
                text("""
                    UPDATE students 
                    SET class_id = :class_id, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :student_id AND school_id = :school_id
                """),
                {
                    "class_id": str(enrollment_data.class_id),
                    "student_id": str(enrollment_data.student_id),
                    "school_id": self.school_id
                }
            )
            
            self.db.commit()
            
            # TODO: Trigger invoice generation here
            # self.generate_invoice_for_enrollment(enrollment_id)
            
            return {
                "success": True, 
                "message": "Student enrolled successfully",
                "enrollment_id": enrollment_id
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Enrollment failed: {str(e)}"}
    
    def get_student_enrollments(self, student_id: uuid.UUID) -> list:
        """Get all enrollments for a student"""
        return self.db.execute(
            text("""
                SELECT e.id, e.status, e.enrolled_date, e.withdrawn_date, e.invoice_generated,
                       c.name as class_name, c.level,
                       t.title as term_title, t.start_date, t.end_date
                FROM enrollments e
                JOIN classes c ON e.class_id = c.id
                JOIN academic_terms t ON e.term_id = t.id
                WHERE e.school_id = :school_id AND e.student_id = :student_id
                ORDER BY e.enrolled_date DESC
            """),
            {"school_id": self.school_id, "student_id": str(student_id)}
        ).fetchall()
    
    def get_class_enrollments(self, class_id: uuid.UUID, term_id: uuid.UUID) -> list:
        """Get all students enrolled in a class for a specific term"""
        return self.db.execute(
            text("""
                SELECT s.id, s.first_name, s.last_name, s.admission_no,
                       e.status, e.enrolled_date, e.invoice_generated
                FROM enrollments e
                JOIN students s ON e.student_id = s.id
                WHERE e.school_id = :school_id 
                AND e.class_id = :class_id 
                AND e.term_id = :term_id
                ORDER BY s.first_name, s.last_name
            """),
            {
                "school_id": self.school_id, 
                "class_id": str(class_id),
                "term_id": str(term_id)
            }
        ).fetchall()