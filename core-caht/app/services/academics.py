# app/services/academics.py
"""
Enhanced Academic Management Service

Integrates academic year/term management with enrollment system.
Provides unified workflows for academic progression and enrollment management.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, or_

from app.models.academic import AcademicYear, AcademicTerm, Enrollment, EnrollmentStatusEvent
from app.models.student import Student
from app.models.class_model import Class


class AcademicManagementService:
    """Unified academic and enrollment management"""
    
    def __init__(self, db: Session, school_id: str):
        self.db = db
        self.school_id = school_id
    
    def create_academic_year_with_terms(
        self,
        year: int,
        start_date: date,
        end_date: date,
        term_structure: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Create academic year with standard term structure.
        
        Args:
            year: Academic year (e.g., 2025)
            start_date: Year start date
            end_date: Year end date
            term_structure: Custom term definitions, or None for standard 3-term structure
        """
        
        # Check if year already exists
        existing_year = self.db.execute(
            select(AcademicYear).where(
                and_(
                    AcademicYear.school_id == self.school_id,
                    AcademicYear.year == year
                )
            )
        ).scalar_one_or_none()
        
        if existing_year:
            raise ValueError(f"Academic year {year} already exists")
        
        # Create academic year
        academic_year = AcademicYear(
            school_id=self.school_id,
            year=year,
            title=f"Academic Year {year}",
            state="DRAFT",
            start_date=start_date,
            end_date=end_date
        )
        self.db.add(academic_year)
        self.db.flush()
        
        # Default 3-term structure if not provided
        if not term_structure:
            term_structure = self._get_default_term_structure(start_date, end_date)
        
        # Create terms
        created_terms = []
        for term_config in term_structure:
            term = AcademicTerm(
                school_id=self.school_id,
                year_id=academic_year.id,
                term=term_config["term_number"],
                title=term_config["title"],
                state="PLANNED",
                start_date=term_config["start_date"],
                end_date=term_config["end_date"]
            )
            self.db.add(term)
            created_terms.append(term)
        
        self.db.flush()
        
        return {
            "academic_year": {
                "id": academic_year.id,
                "year": academic_year.year,
                "title": academic_year.title,
                "state": academic_year.state,
                "start_date": academic_year.start_date,
                "end_date": academic_year.end_date
            },
            "terms": [
                {
                    "id": term.id,
                    "term_number": term.term,
                    "title": term.title,
                    "state": term.state,
                    "start_date": term.start_date,
                    "end_date": term.end_date
                }
                for term in created_terms
            ],
            "message": f"Created academic year {year} with {len(created_terms)} terms"
        }
    
    def activate_academic_year(self, year_id: str, auto_activate_first_term: bool = True) -> Dict:
        """
        Activate an academic year and optionally activate its first term.
        Closes any currently active year.
        """
        
        year = self.db.execute(
            select(AcademicYear).where(
                and_(
                    AcademicYear.id == year_id,
                    AcademicYear.school_id == self.school_id
                )
            )
        ).scalar_one_or_none()
        
        if not year:
            raise ValueError(f"Academic year {year_id} not found")
        
        # Close any currently active year
        active_years = self.db.execute(
            select(AcademicYear).where(
                and_(
                    AcademicYear.school_id == self.school_id,
                    AcademicYear.state == "ACTIVE"
                )
            )
        ).scalars().all()
        
        for active_year in active_years:
            active_year.state = "CLOSED"
            # Close all terms in the year
            self.db.execute(
                select(AcademicTerm).where(
                    AcademicTerm.year_id == active_year.id
                )
            ).scalars().all()
            
            for term in self.db.execute(
                select(AcademicTerm).where(AcademicTerm.year_id == active_year.id)
            ).scalars():
                if term.state == "ACTIVE":
                    term.state = "CLOSED"
        
        # Activate the new year
        year.state = "ACTIVE"
        
        activated_term = None
        if auto_activate_first_term:
            # Activate first term
            first_term = self.db.execute(
                select(AcademicTerm).where(
                    and_(
                        AcademicTerm.year_id == year.id,
                        AcademicTerm.term == 1
                    )
                )
            ).scalar_one_or_none()
            
            if first_term:
                first_term.state = "ACTIVE"
                activated_term = first_term
        
        self.db.flush()
        
        return {
            "academic_year": {
                "id": year.id,
                "year": year.year,
                "title": year.title,
                "state": year.state
            },
            "activated_term": {
                "id": activated_term.id,
                "title": activated_term.title,
                "term_number": activated_term.term
            } if activated_term else None,
            "message": f"Activated academic year {year.year}" + 
                      (f" and {activated_term.title}" if activated_term else "")
        }
    
    def advance_to_next_term(self, force: bool = False) -> Dict:
        """
        Advance from current active term to the next term.
        Handles enrollment status updates and term transitions.
        """
        
        # Get current active term
        current_term = self.db.execute(
            select(AcademicTerm, AcademicYear).join(
                AcademicYear, AcademicYear.id == AcademicTerm.year_id
            ).where(
                and_(
                    AcademicTerm.school_id == self.school_id,
                    AcademicTerm.state == "ACTIVE",
                    AcademicYear.state == "ACTIVE"
                )
            )
        ).first()
        
        if not current_term:
            raise ValueError("No active term found")
        
        current_term_obj, current_year = current_term
        
        # Check for unfinished enrollment business
        if not force:
            warnings = self._check_term_readiness_for_closure(current_term_obj.id)
            if warnings:
                return {
                    "success": False,
                    "warnings": warnings,
                    "message": "Term has unfinished business. Use force=True to override.",
                    "current_term": current_term_obj.title
                }
        
        # Find next term
        next_term = self.db.execute(
            select(AcademicTerm).where(
                and_(
                    AcademicTerm.year_id == current_year.id,
                    AcademicTerm.term == current_term_obj.term + 1
                )
            )
        ).scalar_one_or_none()
        
        if not next_term:
            # End of year - need to check for next year
            next_year = self.db.execute(
                select(AcademicYear).where(
                    and_(
                        AcademicYear.school_id == self.school_id,
                        AcademicYear.year == current_year.year + 1
                    )
                )
            ).scalar_one_or_none()
            
            if next_year:
                next_term = self.db.execute(
                    select(AcademicTerm).where(
                        and_(
                            AcademicTerm.year_id == next_year.id,
                            AcademicTerm.term == 1
                        )
                    )
                ).scalar_one_or_none()
        
        if not next_term:
            raise ValueError("No next term available. Create next academic year first.")
        
        # Close current term
        current_term_obj.state = "CLOSED"
        
        # Activate next term
        next_term.state = "ACTIVE"
        
        # Handle enrollment transitions
        enrollment_transitions = self._handle_term_transition_enrollments(
            current_term_obj.id, 
            next_term.id
        )
        
        self.db.flush()
        
        return {
            "success": True,
            "previous_term": {
                "id": current_term_obj.id,
                "title": current_term_obj.title,
                "state": "CLOSED"
            },
            "current_term": {
                "id": next_term.id,
                "title": next_term.title,
                "state": "ACTIVE",
                "year": next_term.year_id
            },
            "enrollment_transitions": enrollment_transitions,
            "message": f"Advanced from {current_term_obj.title} to {next_term.title}"
        }
    
    def get_enrollment_ready_summary(self) -> Dict:
        """
        Get comprehensive overview of academic calendar and enrollment readiness.
        """
        
        # Get current academic year and term
        current_context = self.db.execute(
            select(AcademicYear, AcademicTerm).join(
                AcademicTerm, AcademicTerm.year_id == AcademicYear.id
            ).where(
                and_(
                    AcademicYear.school_id == self.school_id,
                    AcademicYear.state == "ACTIVE",
                    AcademicTerm.state == "ACTIVE"
                )
            )
        ).first()
        
        # Get all years and terms
        all_academic_data = self.db.execute(
            select(AcademicYear, AcademicTerm).join(
                AcademicTerm, AcademicTerm.year_id == AcademicYear.id
            ).where(
                AcademicYear.school_id == self.school_id
            ).order_by(AcademicYear.year.desc(), AcademicTerm.term.asc())
        ).all()
        
        # Get enrollment statistics
        total_students = self.db.execute(
            select(func.count(Student.id)).where(
                and_(
                    Student.school_id == self.school_id,
                    Student.status == "ACTIVE"
                )
            )
        ).scalar() or 0
        
        enrolled_students = 0
        current_term_id = None
        
        if current_context:
            current_year, current_term = current_context
            current_term_id = current_term.id
            
            enrolled_students = self.db.execute(
                select(func.count(Enrollment.id)).where(
                    and_(
                        Enrollment.school_id == self.school_id,
                        Enrollment.term_id == current_term.id,
                        Enrollment.status == "ENROLLED"
                    )
                )
            ).scalar() or 0
        
        # Get available classes
        total_classes = self.db.execute(
            select(func.count(Class.id)).where(Class.school_id == self.school_id)
        ).scalar() or 0
        
        # Organize academic calendar
        calendar = {}
        for year, term in all_academic_data:
            if year.year not in calendar:
                calendar[year.year] = {
                    "year_info": {
                        "id": year.id,
                        "title": year.title,
                        "state": year.state,
                        "start_date": year.start_date,
                        "end_date": year.end_date
                    },
                    "terms": []
                }
            
            calendar[year.year]["terms"].append({
                "id": term.id,
                "term_number": term.term,
                "title": term.title,
                "state": term.state,
                "start_date": term.start_date,
                "end_date": term.end_date,
                "is_current": term.id == current_term_id if current_term_id else False
            })
        
        return {
            "current_context": {
                "year": current_context[0].year if current_context else None,
                "year_title": current_context[0].title if current_context else None,
                "term": current_context[1].term if current_context else None,
                "term_title": current_context[1].title if current_context else None,
                "term_id": current_term_id
            },
            "enrollment_summary": {
                "total_students": total_students,
                "enrolled_students": enrolled_students,
                "students_needing_enrollment": total_students - enrolled_students,
                "total_classes": total_classes,
                "enrollment_rate": (enrolled_students / total_students * 100) if total_students > 0 else 0
            },
            "academic_calendar": calendar,
            "enrollment_ready": total_students > 0 and current_term_id is not None,
            "recommendations": self._get_setup_recommendations(
                total_students, enrolled_students, current_term_id, total_classes
            )
        }
    
    def bulk_enroll_students_for_term(
        self,
        term_id: str,
        enrollment_mappings: List[Dict],
        auto_generate_invoices: bool = True
    ) -> Dict:
        """
        Bulk enroll students with class assignments for a term.
        
        Args:
            term_id: Target academic term
            enrollment_mappings: List of {"student_id": "...", "class_id": "..."}
            auto_generate_invoices: Whether to generate invoices automatically
        """
        
        from app.services.enrollment import get_enrollment_service
        enrollment_service = get_enrollment_service(self.db, self.school_id)
        
        successful_enrollments = []
        failed_enrollments = []
        
        for mapping in enrollment_mappings:
            try:
                result = enrollment_service.enroll_student(
                    student_id=mapping["student_id"],
                    class_id=mapping["class_id"],
                    term_id=term_id,
                    auto_generate_invoice=auto_generate_invoices
                )
                successful_enrollments.append(result)
                
            except Exception as e:
                failed_enrollments.append({
                    "student_id": mapping["student_id"],
                    "class_id": mapping["class_id"],
                    "error": str(e)
                })
        
        self.db.flush()
        
        return {
            "term_id": term_id,
            "successful_enrollments": len(successful_enrollments),
            "failed_enrollments": len(failed_enrollments),
            "success_details": successful_enrollments,
            "failure_details": failed_enrollments,
            "invoices_generated": auto_generate_invoices,
            "message": f"Enrolled {len(successful_enrollments)} students successfully"
        }
    
    def _get_default_term_structure(self, start_date: date, end_date: date) -> List[Dict]:
        """Generate default 3-term structure"""
        
        total_days = (end_date - start_date).days
        term_days = total_days // 3
        
        return [
            {
                "term_number": 1,
                "title": "Term 1",
                "start_date": start_date,
                "end_date": start_date + timedelta(days=term_days)
            },
            {
                "term_number": 2,
                "title": "Term 2", 
                "start_date": start_date + timedelta(days=term_days + 1),
                "end_date": start_date + timedelta(days=term_days * 2)
            },
            {
                "term_number": 3,
                "title": "Term 3",
                "start_date": start_date + timedelta(days=term_days * 2 + 1),
                "end_date": end_date
            }
        ]
    
    def _check_term_readiness_for_closure(self, term_id: str) -> List[str]:
        """Check if term is ready to be closed"""
        
        warnings = []
        
        # Check for unpaid invoices
        from app.models.payment import Invoice
        unpaid_invoices = self.db.execute(
            select(func.count(Invoice.id)).where(
                and_(
                    Invoice.school_id == self.school_id,
                    Invoice.status.in_(["ISSUED", "PARTIAL"])
                )
            )
        ).scalar() or 0
        
        if unpaid_invoices > 0:
            warnings.append(f"{unpaid_invoices} unpaid invoices")
        
        # Check for students without enrollment status events
        enrollments_without_events = self.db.execute(
            select(func.count(Enrollment.id)).where(
                and_(
                    Enrollment.school_id == self.school_id,
                    Enrollment.term_id == term_id,
                    ~Enrollment.id.in_(
                        select(EnrollmentStatusEvent.enrollment_id).where(
                            EnrollmentStatusEvent.school_id == self.school_id
                        )
                    )
                )
            )
        ).scalar() or 0
        
        if enrollments_without_events > 0:
            warnings.append(f"{enrollments_without_events} enrollments without status tracking")
        
        return warnings
    
    def _handle_term_transition_enrollments(self, from_term_id: str, to_term_id: str) -> Dict:
        """Handle enrollment transitions between terms"""
        
        # Get students enrolled in previous term
        previous_enrollments = self.db.execute(
            select(Enrollment, Student, Class).join(
                Student, Student.id == Enrollment.student_id
            ).join(
                Class, Class.id == Enrollment.class_id
            ).where(
                and_(
                    Enrollment.school_id == self.school_id,
                    Enrollment.term_id == from_term_id,
                    Enrollment.status == "ENROLLED"
                )
            )
        ).all()
        
        transitioned = 0
        
        # Auto-enroll students in next term (same class by default)
        for enrollment, student, class_obj in previous_enrollments:
            try:
                new_enrollment = Enrollment(
                    school_id=self.school_id,
                    student_id=student.id,
                    class_id=class_obj.id,  # Same class by default
                    term_id=to_term_id,
                    status="ENROLLED",
                    joined_on=date.today()
                )
                self.db.add(new_enrollment)
                
                # Create transition event
                self.db.add(EnrollmentStatusEvent(
                    school_id=self.school_id,
                    enrollment_id=new_enrollment.id,
                    prev_status=None,
                    new_status="ENROLLED",
                    reason=f"Auto-enrolled from previous term",
                    event_date=date.today()
                ))
                
                transitioned += 1
                
            except Exception as e:
                print(f"Failed to transition student {student.id}: {e}")
        
        return {
            "students_transitioned": transitioned,
            "total_previous_enrollments": len(previous_enrollments)
        }
    
    def _get_setup_recommendations(
        self, 
        total_students: int, 
        enrolled_students: int, 
        current_term_id: Optional[str],
        total_classes: int
    ) -> List[str]:
        """Generate setup recommendations"""
        
        recommendations = []
        
        if not current_term_id:
            recommendations.append("Activate an academic term to enable enrollments")
        
        if total_students > 0 and enrolled_students == 0:
            recommendations.append("Run student enrollment migration to enroll existing students")
        
        if total_students > enrolled_students and current_term_id:
            recommendations.append(f"{total_students - enrolled_students} students need enrollment")
        
        if total_classes == 0:
            recommendations.append("Create classes before enrolling students")
        
        if total_students == 0:
            recommendations.append("Add students to begin enrollment management")
        
        return recommendations


def get_academic_service(db: Session, school_id: str) -> AcademicManagementService:
    """Factory function to get academic management service"""
    return AcademicManagementService(db, school_id)