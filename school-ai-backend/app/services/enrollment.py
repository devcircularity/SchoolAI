# app/services/enrollment.py
"""
Enhanced Student-Class Enrollment Service

This service implements an enrollment-first approach where:
1. All student-class relationships go through the enrollment system
2. students.class_id is automatically synced as a convenience field
3. Fee invoicing is always based on active enrollments
4. Academic progression is properly tracked
"""

from datetime import date
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.student import Student
from app.models.class_model import Class
from app.models.academic import Enrollment, EnrollmentStatusEvent, AcademicTerm, AcademicYear
from app.models.fee import FeeStructure


class EnrollmentService:
    """Handles all student enrollment operations with automatic sync"""
    
    def __init__(self, db: Session, school_id: str):
        self.db = db
        self.school_id = school_id
    
    def enroll_student(
        self,
        student_id: str,
        class_id: str,
        term_id: str,
        joined_on: Optional[date] = None,
        auto_generate_invoice: bool = True
    ) -> Dict:
        """
        Enroll student in a class for a specific term.
        This is the primary method for student-class assignment.
        """
        joined_on = joined_on or date.today()
        
        # 1. Verify student exists and belongs to school
        student = self.db.get(Student, student_id)
        if not student or student.school_id != self.school_id:
            raise ValueError(f"Student {student_id} not found in school {self.school_id}")
        
        # 2. Verify class exists
        class_obj = self.db.get(Class, class_id)
        if not class_obj or class_obj.school_id != self.school_id:
            raise ValueError(f"Class {class_id} not found in school {self.school_id}")
        
        # 3. Verify term exists and is active
        term = self.db.get(AcademicTerm, term_id)
        if not term or term.school_id != self.school_id:
            raise ValueError(f"Term {term_id} not found in school {self.school_id}")
        
        # 4. Check for existing enrollment in this term
        existing_enrollment = self.db.execute(
            select(Enrollment).where(
                and_(
                    Enrollment.school_id == self.school_id,
                    Enrollment.student_id == student_id,
                    Enrollment.term_id == term_id
                )
            )
        ).scalar_one_or_none()
        
        if existing_enrollment:
            # Update existing enrollment (class transfer within term)
            old_class_id = existing_enrollment.class_id
            existing_enrollment.class_id = class_id
            existing_enrollment.status = "ENROLLED"
            existing_enrollment.joined_on = joined_on
            
            # Log the change
            self.db.add(EnrollmentStatusEvent(
                school_id=self.school_id,
                enrollment_id=existing_enrollment.id,
                prev_status="ENROLLED",
                new_status="ENROLLED",
                reason=f"Transferred from class {old_class_id} to {class_id}",
                event_date=joined_on
            ))
            
            enrollment = existing_enrollment
        else:
            # Create new enrollment
            enrollment = Enrollment(
                school_id=self.school_id,
                student_id=student_id,
                class_id=class_id,
                term_id=term_id,
                status="ENROLLED",
                joined_on=joined_on
            )
            self.db.add(enrollment)
            self.db.flush()
            
            # Log enrollment event
            self.db.add(EnrollmentStatusEvent(
                school_id=self.school_id,
                enrollment_id=enrollment.id,
                prev_status=None,
                new_status="ENROLLED",
                reason="New enrollment",
                event_date=joined_on
            ))
        
        # 5. Sync students.class_id with current active enrollment
        self._sync_student_class_assignment(student_id)
        
        self.db.flush()
        
        # 6. Auto-generate invoice if requested and fee structure exists
        invoice_generated = False
        if auto_generate_invoice:
            try:
                # Get academic year for this term
                year_obj = self.db.execute(
                    select(AcademicYear).where(AcademicYear.id == term.year_id)
                ).scalar_one()
                
                # Check if invoice already exists for this student/term/year
                from app.models.payment import Invoice
                existing_invoice = self.db.execute(
                    select(Invoice).where(
                        and_(
                            Invoice.school_id == self.school_id,
                            Invoice.student_id == student_id,
                            Invoice.term == term.term,
                            Invoice.year == year_obj.year
                        )
                    )
                ).scalar_one_or_none()
                
                if not existing_invoice:
                    from app.services.fees import generate_invoices_for_term
                    invoices = generate_invoices_for_term(
                        db=self.db,
                        school_id=self.school_id,
                        term_id=term_id,
                        class_ids=[class_id],
                        include_optional={}
                    )
                    invoice_generated = len(invoices) > 0
                    
            except Exception as e:
                # Log warning but don't fail enrollment
                print(f"Warning: Could not generate invoice for enrollment: {e}")
        
        return {
            "enrollment_id": enrollment.id,
            "student_id": student_id,
            "class_id": class_id,
            "term_id": term_id,
            "status": enrollment.status,
            "joined_on": enrollment.joined_on,
            "invoice_generated": invoice_generated,
            "message": "Student enrolled successfully"
        }
    
    def create_student_with_enrollment(
        self,
        admission_no: str,
        first_name: str,
        last_name: str,
        class_id: str,
        term_id: str,
        gender: Optional[str] = None,
        dob: Optional[date] = None,
        guardian_data: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new student and immediately enroll them in a class.
        This is the recommended way to add new students.
        """
        
        # 1. Check admission number uniqueness
        existing = self.db.execute(
            select(Student).where(
                and_(
                    Student.school_id == self.school_id,
                    Student.admission_no == admission_no
                )
            )
        ).scalar_one_or_none()
        
        if existing:
            raise ValueError(f"Admission number {admission_no} already exists")
        
        # 2. Create guardian if provided
        primary_guardian_id = None
        if guardian_data:
            from app.models.guardian import Guardian
            guardian = Guardian(
                school_id=self.school_id,
                first_name=guardian_data["first_name"],
                last_name=guardian_data["last_name"],
                phone=guardian_data["phone"],
                email=guardian_data.get("email"),
                relationship=guardian_data.get("relationship", "Parent")
            )
            self.db.add(guardian)
            self.db.flush()
            primary_guardian_id = guardian.id
        
        # 3. Create student (without class_id - will be set by enrollment)
        student = Student(
            school_id=self.school_id,
            admission_no=admission_no,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            dob=dob,
            class_id=None,  # Will be set by enrollment sync
            primary_guardian_id=primary_guardian_id,
            status="ACTIVE"
        )
        self.db.add(student)
        self.db.flush()
        
        # 4. Link guardian if created
        if primary_guardian_id:
            from app.models.student_guardian import StudentGuardian
            self.db.add(StudentGuardian(
                school_id=self.school_id,
                student_id=student.id,
                guardian_id=primary_guardian_id
            ))
        
        # 5. Enroll in class
        enrollment_result = self.enroll_student(
            student_id=student.id,
            class_id=class_id,
            term_id=term_id,
            auto_generate_invoice=True
        )
        
        return {
            "student_id": student.id,
            "admission_no": student.admission_no,
            "name": f"{student.first_name} {student.last_name}",
            "guardian_id": primary_guardian_id,
            "enrollment": enrollment_result,
            "message": f"Student {admission_no} created and enrolled successfully"
        }
    
    def transfer_student(
        self,
        student_id: str,
        from_class_id: str,
        to_class_id: str,
        term_id: str,
        reason: Optional[str] = None
    ) -> Dict:
        """Transfer student between classes within the same term"""
        
        # Find current enrollment
        enrollment = self.db.execute(
            select(Enrollment).where(
                and_(
                    Enrollment.school_id == self.school_id,
                    Enrollment.student_id == student_id,
                    Enrollment.class_id == from_class_id,
                    Enrollment.term_id == term_id,
                    Enrollment.status == "ENROLLED"
                )
            )
        ).scalar_one_or_none()
        
        if not enrollment:
            raise ValueError(f"No active enrollment found for student in class {from_class_id}")
        
        # Update enrollment
        enrollment.class_id = to_class_id
        
        # Log transfer event
        self.db.add(EnrollmentStatusEvent(
            school_id=self.school_id,
            enrollment_id=enrollment.id,
            prev_status="ENROLLED",
            new_status="ENROLLED",
            reason=reason or f"Transferred from {from_class_id} to {to_class_id}",
            event_date=date.today()
        ))
        
        # Sync student class assignment
        self._sync_student_class_assignment(student_id)
        
        return {
            "student_id": student_id,
            "from_class": from_class_id,
            "to_class": to_class_id,
            "term_id": term_id,
            "message": "Student transferred successfully"
        }
    
    def get_student_current_class(self, student_id: str, term_id: Optional[str] = None) -> Optional[str]:
        """Get student's current class based on active enrollment"""
        
        query = select(Enrollment.class_id).where(
            and_(
                Enrollment.school_id == self.school_id,
                Enrollment.student_id == student_id,
                Enrollment.status == "ENROLLED"
            )
        )
        
        if term_id:
            query = query.where(Enrollment.term_id == term_id)
        else:
            # Get most recent active enrollment
            query = query.order_by(Enrollment.created_at.desc())
        
        result = self.db.execute(query).scalar_one_or_none()
        return result
    
    def get_class_roster(self, class_id: str, term_id: str) -> List[Dict]:
        """Get all students enrolled in a class for a specific term"""
        
        enrollments = self.db.execute(
            select(Enrollment, Student).join(
                Student, Student.id == Enrollment.student_id
            ).where(
                and_(
                    Enrollment.school_id == self.school_id,
                    Enrollment.class_id == class_id,
                    Enrollment.term_id == term_id,
                    Enrollment.status == "ENROLLED"
                )
            ).order_by(Student.last_name, Student.first_name)
        ).all()
        
        return [
            {
                "student_id": student.id,
                "admission_no": student.admission_no,
                "name": f"{student.first_name} {student.last_name}",
                "enrollment_id": enrollment.id,
                "joined_on": enrollment.joined_on,
                "status": enrollment.status
            }
            for enrollment, student in enrollments
        ]
    
    def _sync_student_class_assignment(self, student_id: str):
        """
        Private method to sync students.class_id with current active enrollment.
        This keeps the convenience field updated.
        """
        
        # Get current active enrollment (most recent)
        current_class = self.db.execute(
            select(Enrollment.class_id).where(
                and_(
                    Enrollment.school_id == self.school_id,
                    Enrollment.student_id == student_id,
                    Enrollment.status == "ENROLLED"
                )
            ).order_by(Enrollment.created_at.desc())
        ).scalar_one_or_none()
        
        # Update student record
        student = self.db.get(Student, student_id)
        if student:
            student.class_id = current_class
    
    def get_enrollment_history(self, student_id: str) -> List[Dict]:
        """Get complete enrollment history for a student"""
        
        history = self.db.execute(
            select(
                Enrollment,
                Class.name.label("class_name"),
                AcademicTerm.title.label("term_title"),
                AcademicYear.year
            ).join(
                Class, Class.id == Enrollment.class_id
            ).join(
                AcademicTerm, AcademicTerm.id == Enrollment.term_id
            ).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    Enrollment.school_id == self.school_id,
                    Enrollment.student_id == student_id
                )
            ).order_by(AcademicYear.year.desc(), AcademicTerm.term.desc())
        ).all()
        
        return [
            {
                "enrollment_id": enrollment.id,
                "class_name": class_name,
                "term_title": term_title,
                "year": year,
                "status": enrollment.status,
                "joined_on": enrollment.joined_on,
                "left_on": enrollment.left_on
            }
            for enrollment, class_name, term_title, year in history
        ]


def get_enrollment_service(db: Session, school_id: str) -> EnrollmentService:
    """Factory function to get enrollment service instance"""
    return EnrollmentService(db, school_id)


# ========================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# ========================================================================
# These functions maintain compatibility with existing imports

def upsert_enrollment(
    *, 
    db: Session, 
    school_id: str, 
    student_id: str, 
    class_id: str, 
    term_id: str, 
    joined_on: date | None = None
) -> Enrollment:
    """
    Legacy function wrapper for backward compatibility.
    Creates or updates enrollment for a student in a term.
    """
    service = get_enrollment_service(db, school_id)
    result = service.enroll_student(
        student_id=student_id,
        class_id=class_id,
        term_id=term_id,
        joined_on=joined_on,
        auto_generate_invoice=False  # Don't auto-generate for legacy calls
    )
    
    # Return the enrollment object for compatibility
    enrollment = db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.id == result["enrollment_id"],
                Enrollment.school_id == school_id
            )
        )
    ).scalar_one()
    
    return enrollment


def change_enrollment_status(
    *,
    db: Session,
    school_id: str,
    enrollment_id: str,
    new_status: str,
    reason: str | None = None,
    event_date: date | None = None
) -> Enrollment:
    """
    Legacy function wrapper for backward compatibility.
    Updates enrollment status and creates audit event.
    """
    enrollment = db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.id == enrollment_id,
                Enrollment.school_id == school_id
            )
        )
    ).scalar_one_or_none()
    
    if not enrollment:
        raise ValueError(f"Enrollment {enrollment_id} not found")
    
    prev_status = enrollment.status
    enrollment.status = new_status
    
    if new_status in ["TRANSFERRED_OUT", "SUSPENDED", "DROPPED", "GRADUATED"]:
        enrollment.left_on = event_date or date.today()
    
    # Create status event
    db.add(EnrollmentStatusEvent(
        school_id=school_id,
        enrollment_id=enrollment.id,
        prev_status=prev_status,
        new_status=new_status,
        reason=reason,
        event_date=event_date or date.today()
    ))
    
    # Sync student class_id
    service = get_enrollment_service(db, school_id)
    service._sync_student_class_assignment(enrollment.student_id)
    
    return enrollment