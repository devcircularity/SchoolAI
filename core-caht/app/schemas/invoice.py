from pydantic import BaseModel
from datetime import date

class InvoiceGenerateIn(BaseModel):
    term: int
    year: int
    student_id: str | None = None
    class_id: str | None = None
    include_optional: dict[str, bool] | None = None  # {"Lunch": true, "Transport": false}
    due_date: date | None = None

class InvoiceOut(BaseModel):
    id: str
    student_id: str
    term: int
    year: int
    total: float
    status: str
    due_date: date | None

class InvoiceLineOut(BaseModel):
    id: str
    invoice_id: str
    item_name: str
    amount: float