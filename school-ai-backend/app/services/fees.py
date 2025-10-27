# app/services/fees.py
"""
Enhanced Fees Service for Enrollment-Based System

This service ensures fee invoicing is always based on active enrollments,
not the legacy students.class_id field. It integrates seamlessly with the
enhanced enrollment system.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from datetime import date, timedelta
from typing import List, Dict, Optional

from app.models.fee import FeeStructure, FeeItem
from app.models.student import Student
from app.models.class_model import Class
from app.models.academic import Enrollment, AcademicTerm, AcademicYear
from app.models.payment import Invoice, InvoiceLine


class FeesService:
    """Handles fee operations using enrollment-based student tracking"""
    
    def __init__(self, db: Session, school_id: str):
        self.db = db
        self.school_id = school_id
    
    def generate_invoices_for_term(
        self,
        term_id: str,
        include_optional: Dict[str, bool] = None,
        due_date: Optional[date] = None,
        class_ids: Optional[List[str]] = None,
        student_ids: Optional[List[str]] = None
    ) -> List[Invoice]:
        """
        Generate invoices based on active enrollments for a term.
        This replaces the legacy fee generation logic.
        """
        include_optional = include_optional or {}
        
        # Get term and year details
        term_data = self.db.execute(
            select(AcademicTerm, AcademicYear).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    AcademicTerm.id == term_id,
                    AcademicTerm.school_id == self.school_id
                )
            )
        ).first()
        
        if not term_data:
            raise ValueError(f"Term {term_id} not found in school {self.school_id}")
        
        term_obj, year_obj = term_data
        
        # Build enrollment query - only ENROLLED students
        enrollment_query = select(Enrollment, Student, Class).join(
            Student, Student.id == Enrollment.student_id
        ).join(
            Class, Class.id == Enrollment.class_id
        ).where(
            and_(
                Enrollment.school_id == self.school_id,
                Enrollment.term_id == term_id,
                Enrollment.status == "ENROLLED"
            )
        )
        
        # Apply filters
        if class_ids:
            enrollment_query = enrollment_query.where(Enrollment.class_id.in_(class_ids))
        
        if student_ids:
            enrollment_query = enrollment_query.where(Enrollment.student_id.in_(student_ids))
        
        enrollments = self.db.execute(enrollment_query).all()
        
        created_invoices = []
        
        for enrollment, student, class_obj in enrollments:
            try:
                # Check if invoice already exists
                existing_invoice = self.db.execute(
                    select(Invoice).where(
                        and_(
                            Invoice.school_id == self.school_id,
                            Invoice.student_id == student.id,
                            Invoice.term == term_obj.term,
                            Invoice.year == year_obj.year
                        )
                    )
                ).scalar_one_or_none()
                
                if existing_invoice:
                    continue
                
                # Get appropriate fee structure for this student's class
                fee_structure = self._get_fee_structure_for_enrollment(
                    enrollment, class_obj, term_obj.term, year_obj.year
                )
                
                if not fee_structure:
                    continue
                
                # Create invoice
                invoice = self._create_invoice_for_enrollment(
                    enrollment=enrollment,
                    student=student,
                    class_obj=class_obj,
                    fee_structure=fee_structure,
                    term=term_obj.term,
                    year=year_obj.year,
                    include_optional=include_optional,
                    due_date=due_date
                )
                
                if invoice:
                    created_invoices.append(invoice)
                    
            except Exception as e:
                # Log error but continue with other students
                print(f"Error creating invoice for student {student.id}: {e}")
                continue
        
        return created_invoices
    
    def get_billable_students_for_term(
        self,
        term_id: str,
        class_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get students who can be billed for a specific term based on enrollments.
        """
        
        # Get term details
        term_data = self.db.execute(
            select(AcademicTerm, AcademicYear).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    AcademicTerm.id == term_id,
                    AcademicTerm.school_id == self.school_id
                )
            )
        ).first()
        
        if not term_data:
            return []
        
        term_obj, year_obj = term_data
        
        # Get enrolled students
        query = select(Enrollment, Student, Class).join(
            Student, Student.id == Enrollment.student_id
        ).join(
            Class, Class.id == Enrollment.class_id
        ).where(
            and_(
                Enrollment.school_id == self.school_id,
                Enrollment.term_id == term_id,
                Enrollment.status == "ENROLLED"
            )
        )
        
        if class_id:
            query = query.where(Enrollment.class_id == class_id)
        
        enrollments = self.db.execute(query).all()
        
        billable_students = []
        
        for enrollment, student, class_obj in enrollments:
            # Check if student already has invoice
            existing_invoice = self.db.execute(
                select(Invoice).where(
                    and_(
                        Invoice.school_id == self.school_id,
                        Invoice.student_id == student.id,
                        Invoice.term == term_obj.term,
                        Invoice.year == year_obj.year
                    )
                )
            ).scalar_one_or_none()
            
            if not existing_invoice:
                billable_students.append({
                    "student_id": student.id,
                    "student_name": f"{student.first_name} {student.last_name}",
                    "admission_no": student.admission_no,
                    "enrollment_id": enrollment.id,
                    "class_id": enrollment.class_id,
                    "class_name": class_obj.name,
                    "class_level": class_obj.level,
                    "joined_on": enrollment.joined_on,
                    "enrollment_status": enrollment.status
                })
        
        return billable_students
    
    def generate_invoice_for_new_enrollment(
        self,
        enrollment_id: str,
        include_optional: Dict[str, bool] = None,
        due_date: Optional[date] = None
    ) -> Optional[Invoice]:
        """
        Generate invoice immediately when a student is enrolled.
        This is called from the enrollment service for seamless integration.
        """
        include_optional = include_optional or {}
        
        # Get enrollment details
        enrollment_data = self.db.execute(
            select(Enrollment, Student, Class, AcademicTerm, AcademicYear).join(
                Student, Student.id == Enrollment.student_id
            ).join(
                Class, Class.id == Enrollment.class_id
            ).join(
                AcademicTerm, AcademicTerm.id == Enrollment.term_id
            ).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    Enrollment.id == enrollment_id,
                    Enrollment.school_id == self.school_id
                )
            )
        ).first()
        
        if not enrollment_data:
            return None
        
        enrollment, student, class_obj, term_obj, year_obj = enrollment_data
        
        # Check if invoice already exists
        existing_invoice = self.db.execute(
            select(Invoice).where(
                and_(
                    Invoice.school_id == self.school_id,
                    Invoice.student_id == student.id,
                    Invoice.term == term_obj.term,
                    Invoice.year == year_obj.year
                )
            )
        ).scalar_one_or_none()
        
        if existing_invoice:
            return existing_invoice
        
        # Get fee structure
        fee_structure = self._get_fee_structure_for_enrollment(
            enrollment, class_obj, term_obj.term, year_obj.year
        )
        
        if not fee_structure:
            return None
        
        # Create invoice
        return self._create_invoice_for_enrollment(
            enrollment=enrollment,
            student=student,
            class_obj=class_obj,
            fee_structure=fee_structure,
            term=term_obj.term,
            year=year_obj.year,
            include_optional=include_optional,
            due_date=due_date
        )
    
    def _get_fee_structure_for_enrollment(
        self,
        enrollment: Enrollment,
        class_obj: Class,
        term: int,
        year: int
    ) -> Optional[FeeStructure]:
        """
        Find the most appropriate fee structure for an enrollment.
        Priority: class level -> "ALL" level
        """
        
        # Try class-specific level first
        for search_level in [class_obj.level, "ALL"]:
            fee_structure = self.db.execute(
                select(FeeStructure).where(
                    and_(
                        FeeStructure.school_id == self.school_id,
                        FeeStructure.level == search_level,
                        FeeStructure.term == term,
                        FeeStructure.year == year,
                        FeeStructure.is_published == True
                    )
                )
            ).scalar_one_or_none()
            
            if fee_structure:
                return fee_structure
        
        return None
    
    def _create_invoice_for_enrollment(
        self,
        enrollment: Enrollment,
        student: Student,
        class_obj: Class,
        fee_structure: FeeStructure,
        term: int,
        year: int,
        include_optional: Dict[str, bool],
        due_date: Optional[date]
    ) -> Optional[Invoice]:
        """
        Create invoice for a specific enrollment with proper fee item filtering.
        """
        
        # Get applicable fee items
        fee_items_query = select(FeeItem).where(
            and_(
                FeeItem.school_id == self.school_id,
                FeeItem.fee_structure_id == fee_structure.id,
                FeeItem.amount.isnot(None)  # Only priced items
            )
        )
        
        fee_items = self.db.execute(fee_items_query).scalars().all()
        
        if not fee_items:
            return None
        
        # Create invoice
        invoice = Invoice(
            school_id=self.school_id,
            student_id=student.id,
            term=term,
            year=year,
            total=0,
            status="ISSUED",
            due_date=due_date or (date.today() + timedelta(days=30))
        )
        self.db.add(invoice)
        self.db.flush()  # Get invoice ID
        
        total_amount = 0
        
        for item in fee_items:
            # Skip optional items not explicitly included
            if item.is_optional and not include_optional.get(item.item_name, False):
                continue
            
            # Skip items for different classes (if class-specific)
            if item.class_id and item.class_id != enrollment.class_id:
                continue
            
            # Check billing cycle
            if not self._should_include_fee_item(item, term):
                continue
            
            # Create invoice line
            line = InvoiceLine(
                school_id=self.school_id,
                invoice_id=invoice.id,
                item_name=item.item_name,
                amount=item.amount
            )
            self.db.add(line)
            total_amount += float(item.amount)
        
        invoice.total = total_amount
        
        # If no lines were added, don't create the invoice
        if total_amount == 0:
            self.db.expunge(invoice)
            return None
        
        return invoice
    
    def _should_include_fee_item(self, fee_item: FeeItem, current_term: int) -> bool:
        """Determine if a fee item should be included based on billing cycle"""
        
        if fee_item.billing_cycle == "TERM":
            return True
        elif fee_item.billing_cycle == "ANNUAL":
            return current_term == 1  # Only charge annual fees in first term
        elif fee_item.billing_cycle == "ONE_OFF":
            return True
        
        return False
    
    def get_student_invoice_summary(self, student_id: str) -> Dict:
        """
        Get comprehensive invoice summary for a student based on their enrollments.
        """
        
        # Get all invoices for the student
        invoices = self.db.execute(
            select(Invoice).where(
                and_(
                    Invoice.school_id == self.school_id,
                    Invoice.student_id == student_id
                )
            ).order_by(Invoice.year.desc(), Invoice.term.desc())
        ).scalars().all()
        
        # Calculate totals
        total_invoiced = sum(float(inv.total) for inv in invoices)
        
        # Get payments
        from app.models.payment import Payment
        total_paid = self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                and_(
                    Payment.school_id == self.school_id,
                    Payment.invoice_id.in_([inv.id for inv in invoices])
                )
            )
        ).scalar() or 0
        
        total_paid = float(total_paid)
        balance = total_invoiced - total_paid
        
        return {
            "student_id": student_id,
            "total_invoices": len(invoices),
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "balance": balance,
            "invoices": [
                {
                    "id": inv.id,
                    "term": inv.term,
                    "year": inv.year,
                    "total": float(inv.total),
                    "status": inv.status,
                    "due_date": inv.due_date
                }
                for inv in invoices
            ]
        }
    
    def get_class_fee_summary(self, class_id: str, term_id: str) -> Dict:
        """
        Get fee collection summary for a specific class in a term.
        """
        
        # Get term details
        term_data = self.db.execute(
            select(AcademicTerm, AcademicYear).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    AcademicTerm.id == term_id,
                    AcademicTerm.school_id == self.school_id
                )
            )
        ).first()
        
        if not term_data:
            return {"error": "Term not found"}
        
        term_obj, year_obj = term_data
        
        # Get enrolled students in this class for this term
        enrolled_students = self.db.execute(
            select(Enrollment.student_id).where(
                and_(
                    Enrollment.school_id == self.school_id,
                    Enrollment.class_id == class_id,
                    Enrollment.term_id == term_id,
                    Enrollment.status == "ENROLLED"
                )
            )
        ).scalars().all()
        
        if not enrolled_students:
            return {
                "class_id": class_id,
                "term_id": term_id,
                "enrolled_count": 0,
                "invoiced_count": 0,
                "total_invoiced": 0,
                "total_collected": 0
            }
        
        # Get invoices for these students in this term
        invoices = self.db.execute(
            select(Invoice).where(
                and_(
                    Invoice.school_id == self.school_id,
                    Invoice.student_id.in_(enrolled_students),
                    Invoice.term == term_obj.term,
                    Invoice.year == year_obj.year
                )
            )
        ).scalars().all()
        
        total_invoiced = sum(float(inv.total) for inv in invoices)
        
        # Get payments
        if invoices:
            from app.models.payment import Payment
            total_collected = self.db.execute(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    and_(
                        Payment.school_id == self.school_id,
                        Payment.invoice_id.in_([inv.id for inv in invoices])
                    )
                )
            ).scalar() or 0
        else:
            total_collected = 0
        
        return {
            "class_id": class_id,
            "term_id": term_id,
            "enrolled_count": len(enrolled_students),
            "invoiced_count": len(invoices),
            "total_invoiced": total_invoiced,
            "total_collected": float(total_collected),
            "collection_rate": (float(total_collected) / total_invoiced * 100) if total_invoiced > 0 else 0
        }


def get_fees_service(db: Session, school_id: str) -> FeesService:
    """Factory function to get fees service instance"""
    return FeesService(db, school_id)


# ========================================================================
# LEGACY FUNCTIONS (Updated to use enrollment-based logic)
# ========================================================================

def generate_invoices_for_term(
    db: Session,
    school_id: str,
    term_id: str,
    include_optional: Dict[str, bool] | None = None,
    due_date: date | None = None,
    class_ids: List[str] | None = None
) -> List[Invoice]:
    """
    Generate invoices for all enrolled students in a term.
    Updated to use enrollment-based logic while maintaining API compatibility.
    """
    fees_service = get_fees_service(db, school_id)
    return fees_service.generate_invoices_for_term(
        term_id=term_id,
        include_optional=include_optional or {},
        due_date=due_date,
        class_ids=class_ids
    )


def get_billable_students_for_term(
    db: Session,
    school_id: str,
    term_id: str,
    class_id: str | None = None
) -> List[Dict]:
    """Get students who can be billed for a specific term"""
    fees_service = get_fees_service(db, school_id)
    return fees_service.get_billable_students_for_term(term_id, class_id)


def generate_invoices_for_students(
    db: Session,
    school_id: str,
    student_ids: List[str],
    term: int,
    year: int,
    include_optional: Dict[str, bool] | None = None,
    due_date: date | None = None,
) -> List[Invoice]:
    """
    Legacy function for backward compatibility.
    Tries to use new enrollment-based logic, falls back to old logic if needed.
    """
    
    # Try to find the academic term
    term_record = db.execute(
        select(AcademicTerm).join(
            AcademicYear, AcademicYear.id == AcademicTerm.year_id
        ).where(
            AcademicTerm.school_id == school_id,
            AcademicTerm.term == term,
            AcademicYear.year == year
        )
    ).scalar_one_or_none()
    
    if term_record:
        # Use new enrollment-based logic
        fees_service = get_fees_service(db, school_id)
        all_invoices = fees_service.generate_invoices_for_term(
            term_id=term_record.id,
            include_optional=include_optional or {},
            due_date=due_date,
            student_ids=student_ids
        )
        return all_invoices
    else:
        # Fall back to legacy logic for schools without academic terms
        return _legacy_generate_invoices_for_students(
            db, school_id, student_ids, term, year, include_optional, due_date
        )


def _legacy_generate_invoices_for_students(
    db: Session,
    school_id: str,
    student_ids: List[str],
    term: int,
    year: int,
    include_optional: Dict[str, bool] | None = None,
    due_date: date | None = None,
) -> List[Invoice]:
    """Original logic for schools not yet using academic terms"""
    
    created: List[Invoice] = []
    include_optional = include_optional or {}

    for sid in student_ids:
        student = db.get(Student, sid)
        if not student or student.school_id != school_id:
            continue

        level = "ALL"
        if student.class_id:
            from app.models.class_model import Class
            klass = db.get(Class, student.class_id)
            if klass and klass.school_id == school_id:
                level = klass.level

        fs = _select_fee_structure_legacy(db, school_id, level, term, year)
        if not fs:
            continue

        inv = Invoice(
            school_id=school_id,
            student_id=student.id,
            term=term,
            year=year,
            total=0,
            status="ISSUED",
            due_date=due_date or (date.today() + timedelta(days=30)),
        )
        db.add(inv)
        db.flush()

        total = 0
        items = db.execute(
            select(FeeItem).where(
                FeeItem.school_id == school_id,
                FeeItem.fee_structure_id == fs.id,
            )
        ).scalars().all()

        for item in items:
            if item.is_optional and not include_optional.get(item.item_name, False):
                continue
            
            line = InvoiceLine(
                school_id=school_id,
                invoice_id=inv.id,
                item_name=item.item_name,
                amount=item.amount,
            )
            db.add(line)
            total += float(item.amount) if item.amount else 0

        inv.total = total
        created.append(inv)

    return created


def _select_fee_structure_legacy(db: Session, school_id: str, level: str, term: int, year: int):
    """Legacy fee structure selection"""
    
    fs = db.execute(
        select(FeeStructure).where(
            FeeStructure.school_id == school_id,
            FeeStructure.term == term,
            FeeStructure.year == year,
            FeeStructure.level.in_([level, "ALL"]),
        ).order_by(FeeStructure.level.desc(), FeeStructure.is_default.desc())
    ).scalars().first()
    return fs