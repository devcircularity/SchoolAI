# handlers/class/dataclasses.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class ClassRow:
    """Explicit structure for class data rows"""
    id: str
    name: str
    level: str
    academic_year: int
    stream: Optional[str]
    student_count: int
    active_students: int

@dataclass
class ClassDetailRow:
    """Extended class row with detailed information"""
    id: str
    name: str
    level: str
    academic_year: int
    stream: Optional[str]
    created_at: Optional[datetime]
    total_students: int
    active_students: int
    male_students: int
    female_students: int

@dataclass
class GradeRow:
    """Structure for grade data rows"""
    id: str
    label: str
    group_name: str

@dataclass
class StudentRow:
    """Structure for student data in class context"""
    id: str
    first_name: str
    last_name: str
    admission_no: Optional[str]
    gender: str
    status: str

def row_to_class(row) -> ClassRow:
    """Convert database row to ClassRow dataclass"""
    return ClassRow(
        id=str(row[0]),
        name=row[1],
        level=row[2],
        academic_year=row[3],
        stream=row[4],
        student_count=row[5],
        active_students=row[6]
    )

def row_to_class_detail(row) -> ClassDetailRow:
    """Convert database row to ClassDetailRow dataclass"""
    return ClassDetailRow(
        id=str(row[0]),
        name=row[1],
        level=row[2],
        academic_year=row[3],
        stream=row[4],
        created_at=row[5],
        total_students=row[6],
        active_students=row[7],
        male_students=row[8],
        female_students=row[9]
    )

def row_to_grade(row) -> GradeRow:
    """Convert database row to GradeRow dataclass"""
    return GradeRow(
        id=str(row[0]),
        label=row[1],
        group_name=row[2]
    )

def row_to_student(row) -> StudentRow:
    """Convert database row to StudentRow dataclass"""
    return StudentRow(
        id=str(row[0]),
        first_name=row[1],
        last_name=row[2],
        admission_no=row[3],
        gender=row[4],
        status=row[5]
    )

def determine_grade_group(level: str) -> str:
    """Determine grade group from level name"""
    level_lower = level.lower()
    
    if any(term in level_lower for term in ['pp', 'baby', 'nursery', 'pre']):
        return "Pre-Primary"
    elif any(term in level_lower for term in ['grade', 'standard', 'class']) and any(str(i) in level_lower for i in range(1, 9)):
        return "Primary"
    elif any(term in level_lower for term in ['form']) and any(str(i) in level_lower for i in range(1, 5)):
        return "Secondary"
    elif any(term in level_lower for term in ['year']) and any(str(i) in level_lower for i in range(7, 13)):
        return "Secondary"
    else:
        return "Other"

def format_class_display_name(class_name: str, stream: Optional[str] = None) -> str:
    """Format class name for display"""
    if stream:
        return f"{class_name} ({stream})"
    return class_name