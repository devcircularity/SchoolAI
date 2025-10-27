# app/models/enrollment.py - New proper enrollment model
from __future__ import annotations
import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Enrollment(Base):
    """
    Enrollment links students to classes for specific terms.
    This is where invoicing should be triggered.
    """
    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False, index=True)
    term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Enrollment status
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ENROLLED")
    enrolled_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    withdrawn_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Invoice generation flag
    invoice_generated: Mapped[bool] = mapped_column(nullable=False, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Ensure one enrollment per student per term
        Index("uq_enrollment_student_term", "school_id", "student_id", "term_id", unique=True),
        CheckConstraint("status IN ('ENROLLED','TRANSFERRED_OUT','SUSPENDED','DROPPED','GRADUATED')", name="ck_enrollment_status"),
    )
