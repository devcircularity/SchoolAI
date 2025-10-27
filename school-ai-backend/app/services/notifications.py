from sqlalchemy.orm import Session
from app.models.notification import Notification

def queue_notification(
    db: Session,
    *,
    school_id: str,
    typ: str,
    body: str,
    subject: str | None = None,
    to_guardian_id: str | None = None,
    to_user_id: str | None = None,
) -> Notification:
    n = Notification(
        school_id=school_id,
        type=typ,
        subject=subject,
        body=body,
        to_guardian_id=to_guardian_id,
        to_user_id=to_user_id,
        status="QUEUED",
    )
    db.add(n)
    return n

# For alpha: immediately mark IN_APP as SENT; EMAIL stays QUEUED (stub)
def deliver_if_possible(db: Session, n: Notification) -> None:
    if n.type == "IN_APP":
        n.status = "SENT"