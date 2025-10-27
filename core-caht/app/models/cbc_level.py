# app/models/cbc_level.py - Fixed to use proper UUID types
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
import uuid

class CbcLevel(Base):
    __tablename__ = "cbc_level"

    # 🔧 FIXED: Use proper UUID type instead of String(36)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    group_name: Mapped[str | None] = mapped_column(String(64), nullable=True)