# app/api/routes/students_unified.py
"""
Updated Students API using Enhanced Enrollment System

This replaces the existing students route to use enrollment-first approach.
All student-class assignments go through proper enrollment tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, text
from typing import Optional, List
from datetime import date

from app.core.db import get_db
from app.api.deps.tenancy import require_school
from app.api.deps.auth import get_current_user
from app.services.enrollment import get_enrollment_service
from app.models.student import Student
from app.models.class_model import Class
from app.models.academic import AcademicTerm, AcademicYear

router = APIRouter(prefix="/students", tags=["Students"])


# Unified schemas for the new approach
from pydantic import BaseModel, Field

class StudentCreateWithEnrollment(BaseModel):
    """Schema for creating student with immediate enrollment"""
    admission_no: str = Field(..., description="Unique admission number")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    gender: Optional[str] = None
    dob: Optional[date] = None
    
    # Class assignment (required)
    class_id: str = Field(..., description="Class to enroll student in")
    term_id: str = Field(..., description="Academic term for enrollment")
    
    # Optional guardian data
    guardian_first_name: Optional[str] = None
    guardian_last_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None
    guardian_relationship: Optional[str] = "Parent"

class StudentEnrollment(BaseModel):
    """Schema for enrolling existing student"""
    student_id: str
    class_id: str
    term_id: str
    joined_on: Optional[date] = None

class StudentTransfer(BaseModel):
    """Schema for transferring student between classes"""
    from_class_id: str
    to_class_id: str
    term_id: str
    reason: Optional[str] = None

class StudentEnrollmentOut(BaseModel):
    """Response schema for enrollment operations"""
    enrollment_id: str
    student_id: str
    class_id: str
    term_id: str
    status: str
    joined_on: Optional[date]
    invoice_generated: bool
    message: str


@router.post("/create-with-enrollment", response_model=StudentEnrollmentOut)
def create_student_with_enrollment(
    payload: StudentCreateWithEnrollment,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Create a new student and immediately enroll them in a class.
    This is the recommended way to add students.
    """
    
    service = get_enrollment_service(db, school_id)
    
    try:
        # Prepare guardian data if provided
        guardian_data = None
        if payload.guardian_first_name and payload.guardian_last_name and payload.guardian_phone:
            guardian_data = {
                "first_name": payload.guardian_first_name,
                "last_name": payload.guardian_last_name,
                "phone": payload.guardian_phone,
                "email": payload.guardian_email,
                "relationship": payload.guardian_relationship
            }
        
        result = service.create_student_with_enrollment(
            admission_no=payload.admission_no,
            first_name=payload.first_name,
            last_name=payload.last_name,
            class_id=payload.class_id,
            term_id=payload.term_id,
            gender=payload.gender,
            dob=payload.dob,
            guardian_data=guardian_data
        )
        
        db.commit()
        
        enrollment = result["enrollment"]
        return StudentEnrollmentOut(
            enrollment_id=enrollment["enrollment_id"],
            student_id=enrollment["student_id"],
            class_id=enrollment["class_id"],
            term_id=enrollment["term_id"],
            status=enrollment["status"],
            joined_on=enrollment["joined_on"],
            invoice_generated=enrollment["invoice_generated"],
            message=result["message"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create student: {str(e)}")


@router.post("/enroll", response_model=StudentEnrollmentOut)
def enroll_existing_student(
    payload: StudentEnrollment,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Enroll an existing student in a class for a specific term.
    """
    
    service = get_enrollment_service(db, school_id)
    
    try:
        result = service.enroll_student(
            student_id=payload.student_id,
            class_id=payload.class_id,
            term_id=payload.term_id,
            joined_on=payload.joined_on,
            auto_generate_invoice=True
        )
        
        db.commit()
        
        return StudentEnrollmentOut(
            enrollment_id=result["enrollment_id"],
            student_id=result["student_id"],
            class_id=result["class_id"],
            term_id=result["term_id"],
            status=result["status"],
            joined_on=result["joined_on"],
            invoice_generated=result["invoice_generated"],
            message=result["message"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to enroll student: {str(e)}")


@router.post("/transfer", response_model=dict)
def transfer_student(
    student_id: str,
    payload: StudentTransfer,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Transfer a student between classes within the same term.
    """
    
    service = get_enrollment_service(db, school_id)
    
    try:
        result = service.transfer_student(
            student_id=student_id,
            from_class_id=payload.from_class_id,
            to_class_id=payload.to_class_id,
            term_id=payload.term_id,
            reason=payload.reason
        )
        
        db.commit()
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to transfer student: {str(e)}")


@router.get("/{student_id}/current-class")
def get_student_current_class(
    student_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    term_id: Optional[str] = Query(None, description="Specific term ID, or current active term")
):
    """
    Get student's current class assignment based on active enrollment.
    """
    
    service = get_enrollment_service(db, school_id)
    
    try:
        current_class_id = service.get_student_current_class(student_id, term_id)
        
        if not current_class_id:
            return {
                "student_id": student_id,
                "current_class_id": None,
                "message": "Student not currently enrolled in any class"
            }
        
        # Get class details
        class_obj = db.get(Class, current_class_id)
        
        return {
            "student_id": student_id,
            "current_class_id": current_class_id,
            "class_name": class_obj.name if class_obj else "Unknown",
            "class_level": class_obj.level if class_obj else "Unknown"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current class: {str(e)}")


@router.get("/{student_id}/enrollment-history")
def get_student_enrollment_history(
    student_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get complete enrollment history for a student across all terms.
    """
    
    service = get_enrollment_service(db, school_id)
    
    try:
        history = service.get_enrollment_history(student_id)
        return {
            "student_id": student_id,
            "enrollment_history": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enrollment history: {str(e)}")


@router.get("/class/{class_id}/roster")
def get_class_roster(
    class_id: str,
    term_id: str = Query(..., description="Academic term ID"),
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get all students enrolled in a specific class for a term.
    This replaces the simple class_id lookup with proper enrollment tracking.
    """
    
    service = get_enrollment_service(db, school_id)
    
    try:
        roster = service.get_class_roster(class_id, term_id)
        
        # Get class details
        class_obj = db.get(Class, class_id)
        term_obj = db.get(AcademicTerm, term_id)
        
        return {
            "class_id": class_id,
            "class_name": class_obj.name if class_obj else "Unknown",
            "term_id": term_id,
            "term_title": term_obj.title if term_obj else "Unknown",
            "student_count": len(roster),
            "students": roster
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get class roster: {str(e)}")


@router.get("", response_model=List[dict])
def list_all_students(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    include_class_info: bool = Query(True, description="Include current class information"),
    active_only: bool = Query(True, description="Only return active students")
):
    """
    List all students with their current enrollment information.
    This provides a comprehensive view using the unified system.
    """
    
    query = select(Student).where(Student.school_id == school_id)
    
    if active_only:
        query = query.where(Student.status == "ACTIVE")
    
    students = db.execute(query.order_by(Student.last_name, Student.first_name)).scalars().all()
    
    result = []
    service = get_enrollment_service(db, school_id) if include_class_info else None
    
    for student in students:
        student_data = {
            "id": student.id,
            "admission_no": student.admission_no,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "full_name": f"{student.first_name} {student.last_name}",
            "gender": student.gender,
            "dob": student.dob,
            "status": student.status,
            "legacy_class_id": student.class_id  # Keep for reference
        }
        
        if include_class_info and service:
            # Get current enrollment-based class
            current_class_id = service.get_student_current_class(student.id)
            if current_class_id:
                class_obj = db.get(Class, current_class_id)
                student_data.update({
                    "current_class_id": current_class_id,
                    "current_class_name": class_obj.name if class_obj else "Unknown",
                    "current_class_level": class_obj.level if class_obj else "Unknown"
                })
            else:
                student_data.update({
                    "current_class_id": None,
                    "current_class_name": None,
                    "current_class_level": None
                })
        
        result.append(student_data)
    
    return result


@router.get("/active-terms")
def get_active_terms_for_enrollment(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get currently active academic terms for enrollment purposes.
    """
    
    active_terms = db.execute(
        select(AcademicTerm, AcademicYear.year)
        .join(AcademicYear, AcademicYear.id == AcademicTerm.year_id)
        .where(
            and_(
                AcademicTerm.school_id == school_id,
                AcademicTerm.state.in_(["PLANNED", "ACTIVE"])
            )
        )
        .order_by(AcademicYear.year.desc(), AcademicTerm.term.desc())
    ).all()
    
    return [
        {
            "term_id": term.id,
            "term_number": term.term,
            "term_title": term.title,
            "year": year,
            "state": term.state,
            "start_date": term.start_date,
            "end_date": term.end_date
        }
        for term, year in active_terms
    ]


# Migration helper endpoint (can be removed after migration)
@router.post("/migrate-legacy-assignments")
def migrate_legacy_class_assignments(
    term_id: str = Query(..., description="Target term for migration"),
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    ctx = Depends(get_current_user)
):
    """
    ONE-TIME MIGRATION: Convert existing students.class_id assignments to proper enrollments.
    This helps transition from the old system to the unified enrollment system.
    """
    
    # Only allow OWNER/ADMIN to run migration
    if ctx.get("role") not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only owners/admins can run migrations")
    
    service = get_unified_enrollment_service(db, school_id)
    
    try:
        # Find students with class_id but no enrollment in target term
        students_to_migrate = db.execute(
            text("""
                SELECT s.id, s.admission_no, s.first_name, s.last_name, s.class_id
                FROM students s
                WHERE s.school_id = :school_id 
                  AND s.class_id IS NOT NULL
                  AND s.status = 'ACTIVE'
                  AND NOT EXISTS (
                      SELECT 1 FROM enrollments e 
                      WHERE e.student_id = s.id 
                        AND e.term_id = :term_id
                        AND e.school_id = :school_id
                  )
            """),
            {"school_id": school_id, "term_id": term_id}
        ).fetchall()
        
        migrated_count = 0
        errors = []
        
        for student_row in students_to_migrate:
            try:
                result = service.enroll_student(
                    student_id=student_row.id,
                    class_id=student_row.class_id,
                    term_id=term_id,
                    auto_generate_invoice=False  # Don't auto-generate during migration
                )
                migrated_count += 1
                
            except Exception as e:
                errors.append({
                    "student_id": student_row.id,
                    "admission_no": student_row.admission_no,
                    "error": str(e)
                })
        
        db.commit()
        
        return {
            "migration_completed": True,
            "students_migrated": migrated_count,
            "total_candidates": len(students_to_migrate),
            "errors": errors,
            "message": f"Successfully migrated {migrated_count} students to enrollment system"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")