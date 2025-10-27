# app/models/notification.py - Fixed to use correct Base import
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.models.base import Base  # 🔧 FIXED: Import from models.base
import uuid

class Notification(Base):
    __tablename__ = "notification"  # Keep existing table name if it exists
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # IN_APP / EMAIL
    subject: Mapped[str] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(String(2000), nullable=False)
    to_guardian_id: Mapped[str | None] = mapped_column(String(36), index=True)
    to_user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(16), default="QUEUED")  # QUEUED/SENT/FAILED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))