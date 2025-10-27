# handlers/academic/dataclasses.py
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class TermRow:
    """Explicit structure for academic term data"""
    id: str
    title: str
    state: str
    start_date: Optional[date]
    end_date: Optional[date]
    year: int
    year_title: str

@dataclass
class EnrollmentStats:
    """Enrollment statistics for a term"""
    total_enrollments: int
    unique_students: int
    enrolled_classes: int

@dataclass
class SetupStatus:
    """Academic setup status information"""
    year_count: int
    term_count: int
    active_terms: int
    setup_complete: bool

def row_to_term(row) -> TermRow:
    """Convert database row to TermRow dataclass"""
    return TermRow(
        id=str(row[0]),
        title=row[1],
        state=row[2],
        start_date=row[3] if len(row) > 3 else None,
        end_date=row[4] if len(row) > 4 else None,
        year=row[5] if len(row) > 5 else 0,
        year_title=row[6] if len(row) > 6 else ""
    )

def serialize_date(date_obj) -> Optional[str]:
    """Convert date object to string for JSON serialization"""
    if date_obj is None:
        return None
    if isinstance(date_obj, (date, datetime)):
        return date_obj.isoformat()
    return str(date_obj)