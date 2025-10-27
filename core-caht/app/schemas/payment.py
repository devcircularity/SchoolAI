from pydantic import BaseModel
from datetime import date

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    method: str  # CASH/BANK/MPESA
    txn_ref: str | None = None
    posted_at: date | None = None

class PaymentOut(BaseModel):
    id: str
    invoice_id: str
    amount: float
    method: str
    txn_ref: str | None