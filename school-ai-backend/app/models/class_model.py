# app/models/class_model.py - Fixed with UUID types
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Class(Base):
    __tablename__ = "classes"

    # Fixed: Use proper UUID type instead of String(36)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[str] = mapped_column(String(64), nullable=False)
    academic_year: Mapped[int] = mapped_column(Integer, nullable=False)  # Changed to int for consistency
    stream: Mapped[str | None] = mapped_column(String(16))
    
    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="class_")
