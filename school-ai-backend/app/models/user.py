# app/models/user.py - Single User model with UUID
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Enum as SAEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum

class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    ACCOUNTANT = "ACCOUNTANT"
    PARENT = "PARENT"

class User(Base):
    __tablename__ = "users"
    
    # Use proper UUID type
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    roles_csv: Mapped[str] = mapped_column(String(255), default="PARENT")
    
    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (add after all models are converted)
    # school_memberships: Mapped[list["SchoolMember"]] = relationship("SchoolMember", back_populates="user")
    # created_schools: Mapped[list["School"]] = relationship("School", back_populates="creator")
    
    # Convenience property
    @property
    def roles(self) -> list[str]:
        return [r for r in self.roles_csv.split(",") if r]

    def set_roles(self, roles: list[str]) -> None:
        self.roles_csv = ",".join(sorted(set(roles)))