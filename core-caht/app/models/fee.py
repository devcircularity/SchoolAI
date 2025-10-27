# app/models/fee.py - Updated with UUID types and proper constraints
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal, Optional
from datetime import datetime

from sqlalchemy import (
    String, Integer, Boolean, Numeric, ForeignKey, DateTime,
    CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# String "enums" keep migrations simple
Category = Literal["TUITION", "COCURRICULAR", "OTHER"]
BillingCycle = Literal["TERM", "ANNUAL", "ONE_OFF"]


class FeeStructure(Base):
    __tablename__ = "fee_structures"

    # Fixed: Use proper UUID type instead of String(36)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False)  # 'ALL' or a CBC grade label
    term: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items: Mapped[list["FeeItem"]] = relationship(
        "FeeItem",
        back_populates="structure",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_fee_structures_school_term_year", "school_id", "term", "year"),
    )

    def __repr__(self) -> str:
        return f"<FeeStructure id={self.id} {self.level} T{self.term} {self.year} default={self.is_default}>"


class FeeItem(Base):
    __tablename__ = "fee_items"

    # Fixed: Use proper UUID type instead of String(36)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fee_structures.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Per-class override (NULL ⇒ applies to all classes for that structure)
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    item_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Fixed: Make amount required with default value to avoid NULL violations
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal('0.00'))

    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Categorization & billing rules
    category: Mapped[Category] = mapped_column(String(24), default="OTHER", nullable=False)
    billing_cycle: Mapped[BillingCycle] = mapped_column(String(16), default="TERM", nullable=False)

    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    structure: Mapped["FeeStructure"] = relationship("FeeStructure", back_populates="items")
    # Optionally, add a relationship to Class if you want ORM access:
    # klass: Mapped[Optional["Class"]] = relationship("Class", back_populates="fee_items")

    __table_args__ = (
        CheckConstraint("billing_cycle IN ('TERM','ANNUAL','ONE_OFF')", name="ck_fee_items_billing_cycle"),
        CheckConstraint("category IN ('TUITION','COCURRICULAR','OTHER')", name="ck_fee_items_category"),
        CheckConstraint("amount >= 0", name="ck_fee_items_amount_positive"),
        Index("ix_fee_items_school_structure_class", "school_id", "fee_structure_id", "class_id"),
        # Helpful safeguard to avoid duplicate names within the same structure+class override
        # Index("uq_feeitem_struct_class_name", "fee_structure_id", "class_id", "item_name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<FeeItem id={self.id} name={self.item_name} cat={self.category} cycle={self.billing_cycle} amt={self.amount}>"