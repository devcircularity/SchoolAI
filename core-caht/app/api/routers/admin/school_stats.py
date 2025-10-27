# app/api/routers/admin/school_stats.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.db import get_db
from app.models.school import School
from app.api.deps.auth import require_admin

router = APIRouter(prefix="/admin/schools", tags=["Admin - School Stats"])

class SchoolStatsResponse(BaseModel):
    total_schools: int

@router.get("/stats", response_model=SchoolStatsResponse)
def get_school_stats(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get school statistics"""
    
    total_schools = db.query(School).count()
    
    return SchoolStatsResponse(
        total_schools=total_schools
    )