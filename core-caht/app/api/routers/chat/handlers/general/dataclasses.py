# handlers/general/dataclasses.py
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class SystemStatus:
    """System setup status structure"""
    academic_years: int
    active_terms: int
    grades: int
    classes: int
    students: int
    unassigned_students: int
    unenrolled_students: int
    students_without_invoices: int

@dataclass
class NextStepAction:
    """Next step action structure"""
    title: str
    description: str
    action: str
    message: str
    impact: str
    estimated_time: str

@dataclass
class UsageStats:
    """System usage statistics"""
    students: int
    classes: int
    invoices: int
    payments: int

def system_status_from_dict(data: Dict) -> SystemStatus:
    """Convert dictionary to SystemStatus dataclass"""
    return SystemStatus(
        academic_years=data.get('academic_years', 0),
        active_terms=data.get('active_terms', 0),
        grades=data.get('grades', 0),
        classes=data.get('classes', 0),
        students=data.get('students', 0),
        unassigned_students=data.get('unassigned_students', 0),
        unenrolled_students=data.get('unenrolled_students', 0),
        students_without_invoices=data.get('students_without_invoices', 0)
    )

def usage_stats_from_dict(data: Dict) -> UsageStats:
    """Convert dictionary to UsageStats dataclass"""
    return UsageStats(
        students=data.get('students', 0),
        classes=data.get('classes', 0),
        invoices=data.get('invoices', 0),
        payments=data.get('payments', 0)
    )