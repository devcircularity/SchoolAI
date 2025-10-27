# handlers/student/dataclasses.py
from dataclasses import dataclass
from typing import Optional

@dataclass 
class StudentRow:
    """Explicit structure for student data rows"""
    id: str
    first_name: str
    last_name: str
    admission_no: Optional[str]
    status: str
    class_name: Optional[str]
    level: Optional[str]
    guardian_first: Optional[str]
    guardian_last: Optional[str]
    guardian_phone: Optional[str]
    guardian_email: Optional[str]
    relationship: Optional[str]

def row_to_student(row) -> StudentRow:
    """Convert database row to StudentRow dataclass"""
    return StudentRow(
        id=str(row[0]),
        first_name=row[1],
        last_name=row[2], 
        admission_no=row[3],
        status=row[4],
        class_name=row[5] if len(row) > 5 else None,
        level=row[6] if len(row) > 6 else None,
        guardian_first=row[7] if len(row) > 7 else None,
        guardian_last=row[8] if len(row) > 8 else None,
        guardian_phone=row[9] if len(row) > 9 else None,
        guardian_email=row[10] if len(row) > 10 else None,
        relationship=row[11] if len(row) > 11 else None
    )