from sqlalchemy.orm import Session
from datetime import date

from app.models.payment import Payment, Invoice
from app.models.accounting import JournalEntry, JournalLine, GLAccount

def _get_account(db: Session, school_id: str, code: str) -> str:
    acc = db.query(GLAccount).filter(GLAccount.school_id == school_id, GLAccount.code == code).first()
    if not acc:
        raise ValueError(f"GL account {code} missing")
    return acc.id

def post_payment(
    db: Session,
    school_id: str,
    invoice_id: str,
    amount: float,
    method: str,
    txn_ref: str | None,
    posted_at: date | None,
) -> Payment:
    inv = db.get(Invoice, invoice_id)
    if not inv or inv.school_id != school_id:
        raise ValueError("Invoice not found")

    # Create payment
    p = Payment(
        school_id=school_id,
        invoice_id=inv.id,
        amount=amount,
        method=method,
        txn_ref=txn_ref,
        posted_at=posted_at or date.today(),
    )
    db.add(p)

    # Update invoice status/total paid
    # For alpha, compute paid so far
    paid_sum = (
        db.query(Payment)
        .filter(Payment.school_id == school_id, Payment.invoice_id == inv.id)
        .with_entities((Payment.amount))
        .all()
    )
    already = sum(float(x[0]) for x in paid_sum) if paid_sum else 0.0
    new_total_paid = already + float(amount)

    if new_total_paid >= float(inv.total):
        inv.status = "PAID"
    else:
        inv.status = "PARTIAL"

    # GL posting (minimal)
    # Cash/Bank (1000) DR, A/R (1100) CR
    cash_acc = _get_account(db, school_id, "1000")
    ar_acc = _get_account(db, school_id, "1100")

    je = JournalEntry(school_id=school_id, date=posted_at or date.today(), memo=f"Payment {txn_ref or ''}".strip())
    db.add(je); db.flush()

    db.add(JournalLine(school_id=school_id, journal_id=je.id, account_id=cash_acc, debit=amount, credit=0))
    db.add(JournalLine(school_id=school_id, journal_id=je.id, account_id=ar_acc, debit=0, credit=amount))

    return p