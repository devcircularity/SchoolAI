from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
import uuid

class CbcLevel(Base):
    __tablename__ = "cbc_level"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    group_name: Mapped[str | None] = mapped_column(String(64), nullable=True)  # NEW