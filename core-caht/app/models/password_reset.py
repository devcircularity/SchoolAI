# app/models/password_reset.py
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Token and metadata
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Optional: track IP address for security
    created_ip: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv6 support
    used_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationship to user
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")
    
    def is_valid(self) -> bool:
        """Check if token is still valid (not used and not expired)"""
        return (
            not self.used and 
            self.expires_at > datetime.utcnow()
        )
    
    def mark_used(self, ip_address: str = None) -> None:
        """Mark token as used"""
        self.used = True
        self.used_at = datetime.utcnow()
        if ip_address:
            self.used_ip = ip_address
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.used}, expires_at={self.expires_at})>"