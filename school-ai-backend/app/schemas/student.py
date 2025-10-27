from pydantic import BaseModel
from datetime import date
from app.schemas.guardian import GuardianCreate

class StudentCreate(BaseModel):
    admission_no: str
    first_name: str
    last_name: str
    gender: str | None = None
    dob: date | None = None
    class_id: str | None = None

    # Optional inline primary guardian creation
    primary_guardian: GuardianCreate | None = None
    primary_guardian_id: str | None = None  # or reference an existing guardian

class StudentOut(BaseModel):
    id: str
    admission_no: str
    first_name: str
    last_name: str
    gender: str | None = None
    dob: date | None = None
    class_id: str | None = None
    primary_guardian_id: str | None = None
    status: str

class StudentUpdate(BaseModel):
    class_id: str | None = None
    status: str | None = None