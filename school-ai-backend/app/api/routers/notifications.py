from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.api.deps.tenancy import require_school
from app.api.deps.auth import get_current_user
from app.schemas.notification import NotificationCreate, NotificationOut
from app.services.notifications import queue_notification, deliver_if_possible
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/send", response_model=NotificationOut)
def send_notification(
    payload: NotificationCreate,
    school_id: str = Depends(require_school),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = queue_notification(
        db,
        school_id=school_id,
        typ=payload.type,
        subject=payload.subject,
        body=payload.body,
        to_guardian_id=payload.to_guardian_id,
        to_user_id=payload.to_user_id,
    )
    deliver_if_possible(db, n)
    db.flush()
    return NotificationOut(
        id=n.id, type=n.type, subject=n.subject, body=n.body,
        to_guardian_id=n.to_guardian_id, to_user_id=n.to_user_id, status=n.status
    )

@router.get("", response_model=list[NotificationOut])
def list_notifications(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Notification).where(Notification.school_id == school_id).order_by(Notification.created_at.desc())
    ).scalars().all()
    return [NotificationOut(
        id=r.id, type=r.type, subject=r.subject, body=r.body,
        to_guardian_id=r.to_guardian_id, to_user_id=r.to_user_id, status=r.status
    ) for r in rows]