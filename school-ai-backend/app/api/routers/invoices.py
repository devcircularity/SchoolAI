# app/api/routes/invoices_unified.py
"""
Updated Invoices API using Enhanced Enrollment System

This replaces the existing invoices route to use enrollment-based billing.
All invoice generation is based on active enrollments, not legacy class assignments.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import List, Dict, Optional
from datetime import date, timedelta

from app.core.db import get_db
from app.api.deps.tenancy import require_school
from app.api.deps.auth import get_current_user
from app.services.fees import get_fees_service
from app.models.payment import Invoice, InvoiceLine
from app.models.student import Student
from app.models.academic import AcademicTerm, AcademicYear

router = APIRouter(prefix="/invoices", tags=["Invoices"])


from pydantic import BaseModel, Field

class InvoiceGenerateForTerm(BaseModel):
    """Schema for generating invoices for a term"""
    term_id: str = Field(..., description="Academic term ID")
    include_optional: Dict[str, bool] = Field(default_factory=dict, description="Optional fees to include")
    due_days: int = Field(default=30, description="Days from today for due date")
    class_ids: Optional[List[str]] = Field(None, description="Specific classes (all if not provided)")
    student_ids: Optional[List[str]] = Field(None, description="Specific students (all enrolled if not provided)")

class InvoiceGenerateResponse(BaseModel):
    """Response for invoice generation"""
    success: bool
    message: str
    term_id: str
    invoices_created: int
    invoice_ids: List[str]
    billable_students_found: int
    errors: List[str] = Field(default_factory=list)

class InvoiceSummary(BaseModel):
    """Summary of invoice details"""
    id: str
    student_id: str
    student_name: str
    admission_no: str
    term: int
    year: int
    total: float
    status: str
    due_date: Optional[date]
    created_at: str
    class_name: Optional[str] = None


@router.post("/generate-for-term", response_model=InvoiceGenerateResponse)
def generate_invoices_for_term(
    payload: InvoiceGenerateForTerm,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Generate invoices for all enrolled students in a term.
    Uses enrollment-based logic for accurate billing.
    """
    
    fees_service = get_fees_service(db, school_id)
    
    try:
        # Calculate due date
        due_date = date.today() + timedelta(days=payload.due_days)
        
        # Get billable students first (for reporting)
        billable_students = fees_service.get_billable_students_for_term(
            term_id=payload.term_id,
            class_id=payload.class_ids[0] if payload.class_ids and len(payload.class_ids) == 1 else None
        )
        
        # Generate invoices
        invoices = fees_service.generate_invoices_for_term(
            term_id=payload.term_id,
            include_optional=payload.include_optional,
            due_date=due_date,
            class_ids=payload.class_ids,
            student_ids=payload.student_ids
        )
        
        db.commit()
        
        return InvoiceGenerateResponse(
            success=True,
            message=f"Generated {len(invoices)} invoices for term",
            term_id=payload.term_id,
            invoices_created=len(invoices),
            invoice_ids=[inv.id for inv in invoices],
            billable_students_found=len(billable_students)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate invoices: {str(e)}")


@router.get("/billable-students/{term_id}")
def get_billable_students(
    term_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    class_id: Optional[str] = Query(None, description="Filter by specific class")
):
    """
    Get students who can be billed for a specific term based on enrollments.
    This shows students who are enrolled but don't have invoices yet.
    """
    
    fees_service = get_fees_service(db, school_id)
    
    try:
        students = fees_service.get_billable_students_for_term(
            term_id=term_id,
            class_id=class_id
        )
        
        # Get term details for context
        term = db.get(AcademicTerm, term_id)
        
        return {
            "term_id": term_id,
            "term_title": term.title if term else "Unknown",
            "billable_count": len(students),
            "students": students
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[InvoiceSummary])
def list_invoices(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    student_id: Optional[str] = Query(None, description="Filter by student"),
    term: Optional[int] = Query(None, description="Filter by term number"),
    year: Optional[int] = Query(None, description="Filter by academic year"),
    status: Optional[str] = Query(None, description="Filter by invoice status"),
    class_id: Optional[str] = Query(None, description="Filter by class (via enrollments)"),
    limit: int = Query(100, description="Maximum number of invoices to return")
):
    """
    List invoices with optional filtering.
    When filtering by class_id, this uses enrollment data for accuracy.
    """
    
    # Build base query
    query = select(Invoice, Student).join(
        Student, Student.id == Invoice.student_id
    ).where(Invoice.school_id == school_id)
    
    # Apply filters
    if student_id:
        query = query.where(Invoice.student_id == student_id)
    if term:
        query = query.where(Invoice.term == term)
    if year:
        query = query.where(Invoice.year == year)
    if status:
        query = query.where(Invoice.status == status)
    
    # Class filter requires enrollment lookup
    if class_id:
        # Get student IDs enrolled in this class
        from app.models.academic import Enrollment
        enrolled_student_ids = db.execute(
            select(Enrollment.student_id).where(
                and_(
                    Enrollment.school_id == school_id,
                    Enrollment.class_id == class_id,
                    Enrollment.status == "ENROLLED"
                )
            ).distinct()
        ).scalars().all()
        
        if enrolled_student_ids:
            query = query.where(Invoice.student_id.in_(enrolled_student_ids))
        else:
            # No enrolled students in this class
            return []
    
    query = query.order_by(Invoice.created_at.desc()).limit(limit)
    
    results = db.execute(query).all()
    
    # Build response with class information
    invoices = []
    for invoice, student in results:
        # Get class name for this student (current enrollment)
        class_name = None
        if class_id:
            from app.models.class_model import Class
            class_obj = db.get(Class, class_id)
            class_name = class_obj.name if class_obj else None
        else:
            # Find current class via enrollment
            from app.services.enrollment import get_enrollment_service
            enrollment_service = get_enrollment_service(db, school_id)
            current_class_id = enrollment_service.get_student_current_class(student.id)
            if current_class_id:
                from app.models.class_model import Class
                class_obj = db.get(Class, current_class_id)
                class_name = class_obj.name if class_obj else None
        
        invoices.append(InvoiceSummary(
            id=invoice.id,
            student_id=invoice.student_id,
            student_name=f"{student.first_name} {student.last_name}",
            admission_no=student.admission_no,
            term=invoice.term,
            year=invoice.year,
            total=float(invoice.total),
            status=invoice.status,
            due_date=invoice.due_date,
            created_at=invoice.created_at.isoformat(),
            class_name=class_name
        ))
    
    return invoices


@router.get("/{invoice_id}")
def get_invoice_details(
    invoice_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get detailed invoice information including line items and enrollment context.
    """
    
    # Get invoice with student details
    invoice_data = db.execute(
        select(Invoice, Student).join(
            Student, Student.id == Invoice.student_id
        ).where(
            and_(
                Invoice.id == invoice_id,
                Invoice.school_id == school_id
            )
        )
    ).first()
    
    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice, student = invoice_data
    
    # Get invoice lines
    lines = db.execute(
        select(InvoiceLine).where(InvoiceLine.invoice_id == invoice_id)
    ).scalars().all()
    
    # Get enrollment context for this invoice
    from app.models.academic import Enrollment, AcademicTerm
    enrollment_context = db.execute(
        select(Enrollment, AcademicTerm).join(
            AcademicTerm, AcademicTerm.id == Enrollment.term_id
        ).where(
            and_(
                Enrollment.school_id == school_id,
                Enrollment.student_id == student.id,
                AcademicTerm.term == invoice.term,
                AcademicTerm.school_id == school_id
            )
        ).order_by(Enrollment.created_at.desc())
    ).first()
    
    # Get class information
    class_info = None
    if enrollment_context:
        enrollment, term = enrollment_context
        from app.models.class_model import Class
        class_obj = db.get(Class, enrollment.class_id)
        if class_obj:
            class_info = {
                "id": class_obj.id,
                "name": class_obj.name,
                "level": class_obj.level,
                "enrollment_status": enrollment.status,
                "joined_on": enrollment.joined_on
            }
    
    return {
        "id": invoice.id,
        "student": {
            "id": student.id,
            "name": f"{student.first_name} {student.last_name}",
            "admission_no": student.admission_no
        },
        "class": class_info,
        "term": invoice.term,
        "year": invoice.year,
        "total": float(invoice.total),
        "status": invoice.status,
        "due_date": invoice.due_date,
        "created_at": invoice.created_at,
        "line_items": [
            {
                "item_name": line.item_name,
                "amount": float(line.amount)
            }
            for line in lines
        ]
    }


@router.get("/student/{student_id}/summary")
def get_student_invoice_summary(
    student_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive invoice and payment summary for a student.
    """
    
    fees_service = get_fees_service(db, school_id)
    
    try:
        summary = fees_service.get_student_invoice_summary(student_id)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get invoice summary: {str(e)}")


@router.get("/class/{class_id}/fee-summary")
def get_class_fee_summary(
    class_id: str,
    term_id: str = Query(..., description="Academic term ID"),
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get fee collection summary for a specific class in a term.
    Shows enrollment-based billing metrics.
    """
    
    fees_service = get_fees_service(db, school_id)
    
    try:
        summary = fees_service.get_class_fee_summary(class_id, term_id)
        
        # Get class details
        from app.models.class_model import Class
        class_obj = db.get(Class, class_id)
        
        # Get term details
        term_obj = db.get(AcademicTerm, term_id)
        
        return {
            **summary,
            "class_name": class_obj.name if class_obj else "Unknown",
            "class_level": class_obj.level if class_obj else "Unknown",
            "term_title": term_obj.title if term_obj else "Unknown"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get class fee summary: {str(e)}")


@router.post("/generate-for-enrollment/{enrollment_id}")
def generate_invoice_for_enrollment(
    enrollment_id: str,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
    include_optional: Dict[str, bool] = {},
    due_days: int = 30
):
    """
    Generate invoice for a specific enrollment.
    Useful when enrolling students mid-term or for manual invoice generation.
    """
    
    fees_service = get_fees_service(db, school_id)
    
    try:
        due_date = date.today() + timedelta(days=due_days)
        
        invoice = fees_service.generate_invoice_for_new_enrollment(
            enrollment_id=enrollment_id,
            include_optional=include_optional,
            due_date=due_date
        )
        
        if not invoice:
            raise HTTPException(
                status_code=400, 
                detail="Could not generate invoice - check enrollment status and fee structure"
            )
        
        db.commit()
        
        return {
            "success": True,
            "message": "Invoice generated successfully",
            "invoice_id": invoice.id,
            "enrollment_id": enrollment_id,
            "total": float(invoice.total),
            "due_date": invoice.due_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate invoice: {str(e)}")


# Legacy compatibility endpoint
@router.post("/generate-for-students")
def generate_invoices_for_students_legacy(
    student_ids: List[str],
    term: int,
    year: int,
    include_optional: Dict[str, bool] = {},
    due_days: int = 30,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Legacy endpoint for backward compatibility.
    Converts term/year to academic term and uses enrollment-based logic.
    """
    
    try:
        # Find the academic term for this term/year
        term_record = db.execute(
            select(AcademicTerm).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    AcademicTerm.school_id == school_id,
                    AcademicTerm.term == term,
                    AcademicYear.year == year
                )
            )
        ).scalar_one_or_none()
        
        if not term_record:
            raise HTTPException(
                status_code=404, 
                detail=f"Academic term {term} for year {year} not found"
            )
        
        # Use the enhanced fees service
        fees_service = get_fees_service(db, school_id)
        due_date = date.today() + timedelta(days=due_days)
        
        invoices = fees_service.generate_invoices_for_term(
            term_id=term_record.id,
            include_optional=include_optional,
            due_date=due_date,
            student_ids=student_ids
        )
        
        db.commit()
        
        return {
            "message": f"Generated {len(invoices)} invoices",
            "invoices_created": len(invoices),
            "invoice_ids": [inv.id for inv in invoices],
            "term_id": term_record.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate invoices: {str(e)}")


@router.get("/analytics/term-performance")
def get_term_fee_performance(
    term_id: str = Query(..., description="Academic term ID"),
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive fee performance analytics for a term.
    Shows enrollment vs billing vs collection metrics.
    """
    
    try:
        # Get term details
        term_data = db.execute(
            select(AcademicTerm, AcademicYear).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    AcademicTerm.id == term_id,
                    AcademicTerm.school_id == school_id
                )
            )
        ).first()
        
        if not term_data:
            raise HTTPException(status_code=404, detail="Term not found")
        
        term_obj, year_obj = term_data
        
        # Get enrollment statistics
        from app.models.academic import Enrollment
        enrollment_stats = db.execute(
            select(
                Enrollment.status,
                db.func.count().label('count')
            ).where(
                and_(
                    Enrollment.school_id == school_id,
                    Enrollment.term_id == term_id
                )
            ).group_by(Enrollment.status)
        ).all()
        
        # Get invoice statistics
        invoice_stats = db.execute(
            select(
                Invoice.status,
                db.func.count().label('count'),
                db.func.sum(Invoice.total).label('total_amount')
            ).where(
                and_(
                    Invoice.school_id == school_id,
                    Invoice.term == term_obj.term,
                    Invoice.year == year_obj.year
                )
            ).group_by(Invoice.status)
        ).all()
        
        # Get payment statistics
        from app.models.payment import Payment
        payment_total = db.execute(
            select(db.func.coalesce(db.func.sum(Payment.amount), 0)).where(
                and_(
                    Payment.school_id == school_id,
                    Payment.invoice_id.in_(
                        select(Invoice.id).where(
                            and_(
                                Invoice.school_id == school_id,
                                Invoice.term == term_obj.term,
                                Invoice.year == year_obj.year
                            )
                        )
                    )
                )
            )
        ).scalar() or 0
        
        return {
            "term": {
                "id": term_obj.id,
                "title": term_obj.title,
                "term_number": term_obj.term,
                "year": year_obj.year,
                "state": term_obj.state
            },
            "enrollment_stats": {
                status: count for status, count in enrollment_stats
            },
            "invoice_stats": {
                status: {"count": count, "total_amount": float(total_amount or 0)}
                for status, count, total_amount in invoice_stats
            },
            "total_collected": float(payment_total),
            "summary": {
                "total_enrolled": sum(count for _, count in enrollment_stats),
                "total_invoiced": sum(
                    float(total_amount or 0) 
                    for _, _, total_amount in invoice_stats
                ),
                "collection_rate": (
                    float(payment_total) / sum(float(total_amount or 0) for _, _, total_amount in invoice_stats) * 100
                    if sum(float(total_amount or 0) for _, _, total_amount in invoice_stats) > 0 else 0
                )
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")