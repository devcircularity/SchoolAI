# app/schemas/school.py - Fixed to handle date properly
from datetime import date
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import uuid

class SchoolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="School name (required)")
    address: Optional[str] = Field(None, max_length=500, description="School address")
    contact: Optional[str] = Field(None, max_length=255, description="Contact information")
    short_code: Optional[str] = Field(None, max_length=32, description="Short code for reports/IDs")
    email: Optional[str] = Field(None, max_length=255, description="Official school email")
    phone: Optional[str] = Field(None, max_length=32, description="School phone number")
    currency: Optional[str] = Field("KES", max_length=8, description="Default currency")
    
    # FIXED: Accept date string and convert to proper date object
    academic_year_start: str = Field(..., description="Academic year start date (YYYY-MM-DD format)")
    
    @field_validator('academic_year_start')
    @classmethod
    def validate_academic_year_start(cls, v: str) -> date:
        """Convert date string to date object"""
        try:
            if isinstance(v, str):
                # Parse YYYY-MM-DD format
                return date.fromisoformat(v)
            elif isinstance(v, date):
                # Already a date object
                return v
            else:
                raise ValueError("Invalid date format")
        except ValueError:
            raise ValueError("academic_year_start must be in YYYY-MM-DD format (e.g., '2024-01-15')")

class SchoolOut(BaseModel):
    id: uuid.UUID
    name: str
    address: Optional[str] = None
    contact: Optional[str] = None

class SchoolLite(BaseModel):
    id: uuid.UUID
    name: str

class SchoolMineItem(BaseModel):
    id: uuid.UUID
    name: str
    role: Optional[str] = None

class SchoolOverview(BaseModel):
    students: int
    classes: int
    feesCollected: int
    pendingInvoices: int