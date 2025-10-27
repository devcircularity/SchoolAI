from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.school import School
from app.models.student import Student
from app.models.class_model import Class
from app.models.payment import Payment, Invoice


def get_school_name(db: Session, school_id: str) -> str | None:
    """
    Return the school's name or None if not found.
    Assumes RLS is already set by require_school().
    """
    return db.execute(
        select(School.name).where(School.id == school_id)
    ).scalar_one_or_none()


def get_school_overview(db: Session, school_id: str) -> dict:
    """
    Return key stats for dashboards/chat answers:
      - students: count of students
      - classes: count of classes
      - feesCollected: sum of all payments (int)
      - pendingInvoices: count of invoices with status ISSUED/PARTIAL
    """
    students = db.execute(
        select(func.count()).select_from(Student).where(Student.school_id == school_id)
    ).scalar_one() or 0

    classes = db.execute(
        select(func.count()).select_from(Class).where(Class.school_id == school_id)
    ).scalar_one() or 0

    fees_collected = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.school_id == school_id)
    ).scalar_one() or 0

    pending_invoices = db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.school_id == school_id,
            Invoice.status.in_(["ISSUED", "PARTIAL"])
        )
    ).scalar_one() or 0

    return {
        "students": int(students),
        "classes": int(classes),
        "feesCollected": int(fees_collected),
        "pendingInvoices": int(pending_invoices),
    }