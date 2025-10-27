from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import get_db
from app.api.deps.tenancy import require_school
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services.payments import post_payment
from app.models.payment import Payment, Invoice

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("", response_model=PaymentOut)
def create_payment(
    payload: PaymentCreate,
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    try:
        p = post_payment(
            db=db,
            school_id=school_id,
            invoice_id=payload.invoice_id,
            amount=payload.amount,
            method=payload.method,
            txn_ref=payload.txn_ref,
            posted_at=payload.posted_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    db.flush()
    return PaymentOut(id=p.id, invoice_id=p.invoice_id, amount=float(p.amount), method=p.method, txn_ref=p.txn_ref)

@router.get("", response_model=list[PaymentOut])
def list_payments(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Payment).where(Payment.school_id == school_id).order_by(Payment.posted_at.desc())
    ).scalars().all()
    return [PaymentOut(id=r.id, invoice_id=r.invoice_id, amount=float(r.amount), method=r.method, txn_ref=r.txn_ref) for r in rows]