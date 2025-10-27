# app/models/accounting.py
from sqlalchemy import String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
import uuid

class GLAccount(Base):
    __tablename__ = "gl_accounts"  # <<< ADD THIS LINE
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # ASSET/LIABILITY/EQUITY/INCOME/EXPENSE

class JournalEntry(Base):
    # defaults are fine; our migration created 'journalentry'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    memo: Mapped[str] = mapped_column(String(255), nullable=True)

class JournalLine(Base):
    # defaults are fine; our migration created 'journalline'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    journal_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    debit: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    credit: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)