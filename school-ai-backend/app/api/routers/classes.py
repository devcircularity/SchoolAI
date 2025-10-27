from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.deps.tenancy import require_school
from app.schemas.class_schema import ClassCreate, ClassOut
from app.models.class_model import Class
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/classes", tags=["Classes"])

@router.post("", response_model=ClassOut)
async def create_class(
    request: Request,
    payload: ClassCreate,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    # Log the raw request body for debugging
    body = await request.body()
    logger.info(f"Raw request body: {body.decode('utf-8')}")
    logger.info(f"Parsed payload: {payload}")
    logger.info(f"School ID from tenancy: {school_id}")
    
    c = Class(
        school_id=school_id,
        name=payload.name,
        level=payload.level,
        academic_year=payload.academic_year,
        stream=payload.stream,
    )
    db.add(c); db.flush()
    return ClassOut(id=c.id, name=c.name, level=c.level, academic_year=c.academic_year, stream=c.stream)

@router.get("", response_model=list[ClassOut])
def list_classes(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    rows = db.query(Class).filter(Class.school_id == school_id).order_by(Class.level, Class.name).all()
    return [ClassOut(id=r.id, name=r.name, level=r.level, academic_year=r.academic_year, stream=r.stream) for r in rows]