# app/models/payment.py - Updated with UUID types and consistent structure
from __future__ import annotations
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    # Fixed: Use proper UUID type instead of String(36)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    term: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal('0.00'))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")  # DRAFT|ISSUED|PAID|PARTIAL
    due_date: Mapped[date | None] = mapped_column(Date)
    
    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','ISSUED','PAID','PARTIAL')", name="ck_invoice_status"),
        CheckConstraint("total >= 0", name="ck_invoice_total_positive"),
        Index("ix_invoices_school_student_term", "school_id", "student_id", "term", "year"),
    )


class Payment(Base):
    __tablename__ = "payments"

    # Fixed: Use proper UUID type instead of String(36)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)  # CASH|BANK|MPESA
    txn_ref: Mapped[str | None] = mapped_column(String(64))
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")
    
    __table_args__ = (
        CheckConstraint("method IN ('CASH','BANK','MPESA')", name="ck_payment_method"),
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        Index("ix_payments_school_invoice", "school_id", "invoice_id"),
    )


class InvoiceLine(Base):
    __tablename__ = "invoiceline"

    # Fixed: Use proper UUID type instead of String(36)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Add required timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="invoice_lines")
    
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_invoiceline_amount_positive"),
        Index("ix_invoiceline_school_invoice", "school_id", "invoice_id"),
    )