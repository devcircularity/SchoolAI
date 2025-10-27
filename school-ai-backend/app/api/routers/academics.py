# app/api/routes/academics.py
"""
Enhanced Academic Management API

Integrates academic calendar management with enrollment system.
Provides unified workflows for academic progression and enrollment management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import List, Optional, Dict
from datetime import date

from app.core.db import get_db
from app.api.deps.tenancy import require_school
from app.api.deps.auth import get_current_user
from app.services.academics import get_academic_service
from app.services.enrollment import get_enrollment_service

router = APIRouter(prefix="/academics", tags=["Academic Management"])

# Enhanced Schemas
from pydantic import BaseModel, Field

class AcademicYearCreate(BaseModel):
    """Create academic year with integrated term structure"""
    year: int = Field(..., description="Academic year (e.g., 2025)")
    start_date: date = Field(..., description="Year start date")
    end_date: date = Field(..., description="Year end date")
    auto_create_terms: bool = Field(default=True, description="Auto-create 3 standard terms")
    custom_terms: Optional[List[Dict]] = Field(None, description="Custom term structure")

class AcademicYearResponse(BaseModel):
    """Academic year creation response"""
    academic_year: Dict
    terms: List[Dict]
    message: str

class TermAdvanceResponse(BaseModel):
    """Term advancement response"""
    success: bool
    previous_term: Optional[Dict]
    current_term: Optional[Dict]
    enrollment_transitions: Dict
    message: str
    warnings: Optional[List[str]] = None

class EnrollmentSummaryResponse(BaseModel):
    """Comprehensive enrollment and academic summary"""
    current_context: Dict
    enrollment_summary: Dict
    academic_calendar: Dict
    enrollment_ready: bool
    recommendations: List[str]

class BulkEnrollmentRequest(BaseModel):
    """Bulk enrollment request"""
    term_id: str = Field(..., description="Target academic term")
    student_class_mappings: List[Dict] = Field(..., description="Student to class assignments")
    auto_generate_invoices: bool = Field(default=True, description="Generate invoices automatically")


@router.post("/years", response_model=AcademicYearResponse)
def create_academic_year_with_terms(
    data: AcademicYearCreate,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Create academic year with integrated term structure.
    This replaces the old separate year/term creation process.
    """
    
    academic_service = get_academic_service(db, school_id)
    
    try:
        # Prepare term structure
        term_structure = None
        if not data.auto_create_terms and data.custom_terms:
            term_structure = data.custom_terms
        
        result = academic_service.create_academic_year_with_terms(
            year=data.year,
            start_date=data.start_date,
            end_date=data.end_date,
            term_structure=term_structure
        )
        
        db.commit()
        
        return AcademicYearResponse(
            academic_year=result["academic_year"],
            terms=result["terms"],
            message=result["message"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create academic year: {str(e)}")


@router.post("/years/{year_id}/activate")
def activate_academic_year(
    year_id: str,
    auto_activate_first_term: bool = Query(default=True, description="Auto-activate Term 1"),
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Activate academic year and optionally its first term.
    This makes the year ready for student enrollments.
    """
    
    academic_service = get_academic_service(db, school_id)
    
    try:
        result = academic_service.activate_academic_year(
            year_id=year_id,
            auto_activate_first_term=auto_activate_first_term
        )
        
        db.commit()
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to activate academic year: {str(e)}")


@router.post("/advance-term", response_model=TermAdvanceResponse)
def advance_to_next_term(
    force: bool = Query(default=False, description="Force advancement despite warnings"),
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Advance from current term to next term with enrollment transitions.
    Handles automatic student progression and term closure.
    """
    
    academic_service = get_academic_service(db, school_id)
    
    try:
        result = academic_service.advance_to_next_term(force=force)
        
        if result.get("success", True):
            db.commit()
        
        return TermAdvanceResponse(
            success=result.get("success", True),
            previous_term=result.get("previous_term"),
            current_term=result.get("current_term"),
            enrollment_transitions=result.get("enrollment_transitions", {}),
            message=result["message"],
            warnings=result.get("warnings")
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to advance term: {str(e)}")


@router.get("/overview", response_model=EnrollmentSummaryResponse)
def get_academic_enrollment_overview(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive overview of academic calendar and enrollment readiness.
    This is the main dashboard endpoint for academic management.
    """
    
    academic_service = get_academic_service(db, school_id)
    
    try:
        summary = academic_service.get_enrollment_ready_summary()
        
        return EnrollmentSummaryResponse(
            current_context=summary["current_context"],
            enrollment_summary=summary["enrollment_summary"],
            academic_calendar=summary["academic_calendar"],
            enrollment_ready=summary["enrollment_ready"],
            recommendations=summary["recommendations"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.post("/bulk-enroll")
def bulk_enroll_students_for_term(
    data: BulkEnrollmentRequest,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Bulk enroll students for a specific term with class assignments.
    Perfect for beginning-of-term enrollment or migration.
    """
    
    academic_service = get_academic_service(db, school_id)
    
    try:
        result = academic_service.bulk_enroll_students_for_term(
            term_id=data.term_id,
            enrollment_mappings=data.student_class_mappings,
            auto_generate_invoices=data.auto_generate_invoices
        )
        
        db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to bulk enroll: {str(e)}")


@router.get("/migration-helper")
def get_migration_helper_data(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get data needed for migrating from legacy system to enrollment-based system.
    Shows students who need enrollment and suggests class assignments.
    """
    
    try:
        # Get students who need enrollment
        from app.models.student import Student
        from app.models.academic import Enrollment
        
        students_needing_enrollment = db.execute(
            select(Student).where(
                and_(
                    Student.school_id == school_id,
                    Student.status == "ACTIVE",
                    ~Student.id.in_(
                        select(Enrollment.student_id).where(
                            and_(
                                Enrollment.school_id == school_id,
                                Enrollment.status == "ENROLLED"
                            )
                        )
                    )
                )
            ).order_by(Student.last_name, Student.first_name)
        ).scalars().all()
        
        # Get available classes
        from app.models.class_model import Class
        available_classes = db.execute(
            select(Class).where(Class.school_id == school_id)
            .order_by(Class.level, Class.name)
        ).scalars().all()
        
        # Get current active term
        from app.models.academic import AcademicTerm, AcademicYear
        current_term = db.execute(
            select(AcademicTerm, AcademicYear).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    AcademicTerm.school_id == school_id,
                    AcademicTerm.state == "ACTIVE"
                )
            )
        ).first()
        
        # Prepare migration suggestions
        migration_suggestions = []
        for student in students_needing_enrollment:
            suggestion = {
                "student_id": student.id,
                "student_name": f"{student.first_name} {student.last_name}",
                "admission_no": student.admission_no,
                "current_class_id": student.class_id,
                "suggested_class_id": student.class_id,  # Use current assignment as suggestion
                "suggested_class_name": None
            }
            
            # Find class name if class_id exists
            if student.class_id:
                suggested_class = next(
                    (c for c in available_classes if c.id == student.class_id), 
                    None
                )
                if suggested_class:
                    suggestion["suggested_class_name"] = suggested_class.name
            
            migration_suggestions.append(suggestion)
        
        return {
            "students_needing_enrollment": len(students_needing_enrollment),
            "available_classes": [
                {
                    "id": cls.id,
                    "name": cls.name,
                    "level": cls.level,
                    "stream": cls.stream
                }
                for cls in available_classes
            ],
            "current_term": {
                "id": current_term[0].id,
                "title": current_term[0].title,
                "year": current_term[1].year,
                "state": current_term[0].state
            } if current_term else None,
            "migration_suggestions": migration_suggestions,
            "ready_for_migration": current_term is not None and len(students_needing_enrollment) > 0,
            "bulk_enrollment_payload": {
                "term_id": current_term[0].id if current_term else None,
                "student_class_mappings": [
                    {
                        "student_id": suggestion["student_id"],
                        "class_id": suggestion["suggested_class_id"]
                    }
                    for suggestion in migration_suggestions
                    if suggestion["suggested_class_id"]
                ],
                "auto_generate_invoices": True
            } if current_term else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get migration data: {str(e)}")


@router.post("/quick-setup")
def quick_academic_setup(
    year: int = Query(..., description="Academic year to set up"),
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Quick setup for schools starting fresh.
    Creates academic year, activates it, and prepares for enrollment.
    """
    
    academic_service = get_academic_service(db, school_id)
    
    try:
        # Create academic year with terms
        year_result = academic_service.create_academic_year_with_terms(
            year=year,
            start_date=date(year, 1, 1),
            end_date=date(year, 12, 31)
        )
        
        # Activate the year and first term
        activation_result = academic_service.activate_academic_year(
            year_id=year_result["academic_year"]["id"],
            auto_activate_first_term=True
        )
        
        # Get overview to show what's ready
        overview = academic_service.get_enrollment_ready_summary()
        
        db.commit()
        
        return {
            "setup_completed": True,
            "academic_year": year_result["academic_year"],
            "active_term": activation_result["activated_term"],
            "enrollment_ready": overview["enrollment_ready"],
            "next_steps": overview["recommendations"],
            "message": f"Academic year {year} is ready for student enrollments!"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Quick setup failed: {str(e)}")


# Legacy compatibility endpoints (updated to use new service)
@router.post("/years/{year_id}/terms", deprecated=True)
def create_academic_term_legacy(
    year_id: str,
    term_data: Dict,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Legacy endpoint for creating individual terms.
    Recommend using the integrated year creation instead.
    """
    
    from app.models.academic import AcademicTerm, AcademicYear
    
    # Verify year exists
    year = db.execute(
        select(AcademicYear).where(
            and_(
                AcademicYear.id == year_id,
                AcademicYear.school_id == school_id
            )
        )
    ).scalar_one_or_none()
    
    if not year:
        raise HTTPException(status_code=404, detail="Academic year not found")
    
    # Create term
    term = AcademicTerm(
        school_id=school_id,
        year_id=year_id,
        term=term_data["term"],
        title=term_data["title"],
        start_date=term_data.get("start_date"),
        end_date=term_data.get("end_date"),
        state="PLANNED"
    )
    
    db.add(term)
    db.commit()
    
    return {
        "id": term.id,
        "term": term.term,
        "title": term.title,
        "state": term.state,
        "year_id": term.year_id,
        "message": "Term created. Consider using integrated year creation for better workflow."
    }


@router.get("/years", deprecated=False)
def list_academic_years(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """List all academic years with their terms"""
    
    from app.models.academic import AcademicYear, AcademicTerm
    
    years_with_terms = db.execute(
        select(AcademicYear, AcademicTerm).join(
            AcademicTerm, AcademicTerm.year_id == AcademicYear.id
        ).where(
            AcademicYear.school_id == school_id
        ).order_by(AcademicYear.year.desc(), AcademicTerm.term.asc())
    ).all()
    
    # Group by year
    years_dict = {}
    for year, term in years_with_terms:
        if year.id not in years_dict:
            years_dict[year.id] = {
                "id": year.id,
                "year": year.year,
                "title": year.title,
                "state": year.state,
                "start_date": year.start_date,
                "end_date": year.end_date,
                "terms": []
            }
        
        years_dict[year.id]["terms"].append({
            "id": term.id,
            "term_number": term.term,
            "title": term.title,
            "state": term.state,
            "start_date": term.start_date,
            "end_date": term.end_date
        })
    
    return list(years_dict.values())


@router.get("/current")
def get_current_academic_context(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """Get current active academic year and term"""
    
    from app.models.academic import AcademicYear, AcademicTerm
    
    current_context = db.execute(
        select(AcademicYear, AcademicTerm).join(
            AcademicTerm, AcademicTerm.year_id == AcademicYear.id
        ).where(
            and_(
                AcademicYear.school_id == school_id,
                AcademicYear.state == "ACTIVE",
                AcademicTerm.state == "ACTIVE"
            )
        )
    ).first()
    
    if not current_context:
        return {
            "current_year": None,
            "current_term": None,
            "enrollment_ready": False,
            "message": "No active academic term found"
        }
    
    year, term = current_context
    
    return {
        "current_year": {
            "id": year.id,
            "year": year.year,
            "title": year.title,
            "state": year.state
        },
        "current_term": {
            "id": term.id,
            "term_number": term.term,
            "title": term.title,
            "state": term.state
        },
        "enrollment_ready": True,
        "message": f"Currently in {term.title} of {year.year}"
    }