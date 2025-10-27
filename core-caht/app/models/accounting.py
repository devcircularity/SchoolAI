# app/models/accounting.py - Fixed to use correct Base import
from sqlalchemy import String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base  # 🔧 FIXED: Import from models.base
import uuid

class GLAccount(Base):
    __tablename__ = "gl_accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # ASSET/LIABILITY/EQUITY/INCOME/EXPENSE

class JournalEntry(Base):
    __tablename__ = "journalentry"  # Keep existing table name
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    memo: Mapped[str] = mapped_column(String(255), nullable=True)

class JournalLine(Base):
    __tablename__ = "journalline"  # Keep existing table name
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    journal_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    debit: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    credit: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)