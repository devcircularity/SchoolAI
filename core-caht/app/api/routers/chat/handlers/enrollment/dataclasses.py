# handlers/enrollment/dataclasses.py
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class StudentEnrollmentData:
    """Student data for enrollment operations"""
    id: str
    first_name: str
    last_name: str
    admission_no: Optional[str]
    class_id: Optional[str]
    class_name: Optional[str]
    class_level: Optional[str]

@dataclass
class TermData:
    """Academic term data"""
    id: str
    title: str
    year: int

@dataclass
class ClassData:
    """Class data for assignment operations"""
    id: str
    name: str
    level: str
    academic_year: int
    stream: Optional[str]
    current_students: int

@dataclass
class EnrollmentResult:
    """Result of enrollment operation"""
    student_id: str
    student_name: str
    admission_no: Optional[str]
    class_name: str
    term_title: str
    enrollment_id: str
    was_just_assigned: bool = False

@dataclass
class BulkEnrollmentResult:
    """Result of bulk enrollment operation"""
    successful_count: int
    failed_count: int
    successful_enrollments: List[dict]
    failed_enrollments: List[str]
    term_title: str

def row_to_student_enrollment(row) -> StudentEnrollmentData:
    """Convert database row to StudentEnrollmentData"""
    return StudentEnrollmentData(
        id=str(row[0]),
        first_name=row[1],
        last_name=row[2],
        admission_no=row[3],
        class_id=str(row[4]) if row[4] else None,
        class_name=row[5],
        class_level=row[6]
    )

def row_to_term(row) -> TermData:
    """Convert database row to TermData"""
    return TermData(
        id=str(row[0]),
        title=row[1],
        year=row[2]
    )

def row_to_class(row) -> ClassData:
    """Convert database row to ClassData"""
    return ClassData(
        id=str(row[0]),
        name=row[1],
        level=row[2],
        academic_year=row[3],
        stream=row[4],
        current_students=row[5]
    )

def student_to_dict(student: StudentEnrollmentData) -> dict:
    """Convert StudentEnrollmentData to dict for context storage"""
    return {
        'id': student.id,
        'first_name': student.first_name,
        'last_name': student.last_name,
        'admission_no': student.admission_no,
        'class_id': student.class_id,
        'class_name': student.class_name,
        'class_level': student.class_level
    }

def format_student_name(student: StudentEnrollmentData) -> str:
    """Format student full name"""
    return f"{student.first_name} {student.last_name}"

def format_student_identifier(student: StudentEnrollmentData) -> str:
    """Format student identifier with admission number"""
    admission = student.admission_no or "No admission #"
    return f"{format_student_name(student)} (#{admission})"

def group_students_by_class(students: List[StudentEnrollmentData]) -> dict:
    """Group students by their class for display purposes"""
    by_class = {}
    for student in students:
        class_name = student.class_name or 'Unassigned'
        if class_name not in by_class:
            by_class[class_name] = []
        by_class[class_name].append(student)
    return by_class