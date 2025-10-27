from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.deps.tenancy import require_school
from app.schemas.guardian import GuardianCreate, GuardianOut
from app.models.guardian import Guardian

router = APIRouter(prefix="/guardians", tags=["Guardians"])

@router.post("", response_model=GuardianOut)
def create_guardian(
    payload: GuardianCreate,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    g = Guardian(
        school_id=school_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        email=payload.email,
        relationship=payload.relationship,
    )
    db.add(g); db.flush()
    return GuardianOut(
        id=g.id, first_name=g.first_name, last_name=g.last_name, phone=g.phone, email=g.email,
        relationship=g.relationship
    )

@router.get("", response_model=list[GuardianOut])
def list_guardians(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    rows = db.query(Guardian).filter(Guardian.school_id == school_id).order_by(Guardian.last_name).all()
    return [
        GuardianOut(
            id=r.id, first_name=r.first_name, last_name=r.last_name,
            phone=r.phone, email=r.email, relationship=r.relationship
        )
        for r in rows
    ]