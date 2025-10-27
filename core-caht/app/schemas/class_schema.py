from pydantic import BaseModel

class ClassCreate(BaseModel):
    name: str
    level: str          # e.g., "Grade 4", "JSS 7"
    academic_year: str  # e.g., "2025"
    stream: str | None = None

class ClassOut(BaseModel):
    id: str
    name: str
    level: str
    academic_year: str
    stream: str | None = None