# handlers/overview/dataclasses.py
from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime

@dataclass
class StudentStats:
    """Student statistics data"""
    total: int
    active: int
    unassigned: int
    enrolled_current_term: int

@dataclass
class ClassStats:
    """Class statistics data"""
    total: int
    with_students: int

@dataclass
class AcademicStats:
    """Academic statistics data"""
    years: int
    terms: int
    active_terms: int

@dataclass
class FeeStats:
    """Fee and payment statistics data"""
    fee_structures: int
    total_invoices: int
    pending_invoices: int
    total_payments: float

@dataclass
class CurrentTerm:
    """Current active term information"""
    id: str
    title: str
    state: str
    year: int
    year_title: str

@dataclass
class ClassBreakdown:
    """Individual class breakdown data"""
    class_name: str
    level: str
    student_count: int
    status: str

@dataclass
class ActivityItem:
    """Recent activity timeline item"""
    time: str
    icon: str
    title: str
    subtitle: str

@dataclass
class OverviewData:
    """Complete overview data structure"""
    school_name: str
    student_stats: StudentStats
    class_stats: ClassStats
    academic_stats: AcademicStats
    fee_stats: Optional[FeeStats]
    current_term: Optional[CurrentTerm]
    class_breakdown: List[ClassBreakdown]
    recent_activity: List[ActivityItem]

def create_student_stats(row) -> StudentStats:
    """Create StudentStats from database row"""
    return StudentStats(
        total=row[0] or 0,
        active=row[1] or 0,
        unassigned=row[2] or 0,
        enrolled_current_term=0  # Set separately
    )

def create_class_stats(row) -> ClassStats:
    """Create ClassStats from database row"""
    return ClassStats(
        total=row[0] or 0,
        with_students=row[1] or 0
    )

def create_academic_stats(row) -> AcademicStats:
    """Create AcademicStats from database row"""
    return AcademicStats(
        years=row[0] or 0,
        terms=row[1] or 0,
        active_terms=row[2] or 0
    )

def create_fee_stats(row) -> FeeStats:
    """Create FeeStats from database row"""
    return FeeStats(
        fee_structures=row[0] or 0,
        total_invoices=row[1] or 0,
        pending_invoices=row[2] or 0,
        total_payments=float(row[3] or 0)
    )

def create_current_term(row) -> Optional[CurrentTerm]:
    """Create CurrentTerm from database row"""
    if not row:
        return None
    
    term = row[0]
    return CurrentTerm(
        id=str(term[0]),
        title=term[1],
        state=term[2],
        year=term[3],
        year_title=term[4]
    )

def create_class_breakdown(rows) -> List[ClassBreakdown]:
    """Create ClassBreakdown list from database rows"""
    return [
        ClassBreakdown(
            class_name=row[0],
            level=row[1],
            student_count=row[2],
            status="Active" if row[2] > 0 else "Empty"
        )
        for row in rows
    ]

def create_activity_item(time: str, icon: str, title: str, subtitle: str) -> ActivityItem:
    """Create ActivityItem"""
    return ActivityItem(
        time=time,
        icon=icon,
        title=title,
        subtitle=subtitle
    )