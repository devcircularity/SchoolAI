# app/models/school.py - Fixed to use Date field for academic_year_start
from __future__ import annotations
import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class School(Base):
    __tablename__ = "schools"

    # Use proper UUID type
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    address: Mapped[str | None] = mapped_column(String(256))
    contact: Mapped[str | None] = mapped_column(String(128))
    short_code: Mapped[str | None] = mapped_column(String(16), unique=True)
    email: Mapped[str | None] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(8), default="KES")
    
    # FIXED: Academic year start as proper Date field
    academic_year_start: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Foreign key to users table
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (add after all models are converted)
    # members: Mapped[list["SchoolMember"]] = relationship("SchoolMember", back_populates="school")
    # creator: Mapped["User"] = relationship("User", back_populates="created_schools")


class SchoolMember(Base):
    __tablename__ = "schoolmember"

    # Use proper UUID type
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # OWNER|ADMIN|TEACHER|ACCOUNTANT|PARENT
    
    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (add after all models are converted)
    # school: Mapped["School"] = relationship("School", back_populates="members")
    # user: Mapped["User"] = relationship("User", back_populates="school_memberships")
    
    __table_args__ = (
        CheckConstraint("role IN ('OWNER','ADMIN','TEACHER','ACCOUNTANT','PARENT')", name="ck_schoolmember_role"),
    )