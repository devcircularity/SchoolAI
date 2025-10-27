# app/schemas/enrollment.py - Enrollment schemas
from pydantic import BaseModel
from typing import Optional
from datetime import date
import uuid

class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID
    class_id: uuid.UUID
    term_id: uuid.UUID
    enrolled_date: Optional[date] = None

class EnrollmentOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    class_id: uuid.UUID
    term_id: uuid.UUID
    status: str
    enrolled_date: date
    withdrawn_date: Optional[date] = None
    invoice_generated: bool
    
    class Config:
        from_attributes = True