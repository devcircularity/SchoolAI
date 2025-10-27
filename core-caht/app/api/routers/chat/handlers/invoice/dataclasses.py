# handlers/invoice/dataclasses.py
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional, List

@dataclass
class InvoiceRow:
    """Explicit structure for invoice data rows"""
    id: str
    first_name: str
    last_name: str
    admission_no: str
    class_name: str
    class_level: str
    total: Decimal
    due_date: Optional[date]
    created_at: date
    paid_amount: Decimal
    status: str

@dataclass
class StudentInvoiceDetail:
    """Complete invoice details for a student"""
    invoice_id: str
    total: Decimal
    status: str
    created_at: date
    due_date: Optional[date]
    term: str
    year: str
    student_name: str
    admission_no: str
    class_name: str
    class_level: str
    paid_amount: Decimal
    term_title: str
    outstanding: Decimal

@dataclass
class InvoiceLineItem:
    """Invoice line item structure"""
    item_name: str
    amount: Decimal
    category: Optional[str] = None
    is_optional: bool = False

@dataclass
class PaymentRecord:
    """Payment record structure"""
    amount: Decimal
    payment_date: date
    payment_method: Optional[str]
    reference_no: Optional[str]

@dataclass
class StudentForInvoice:
    """Student data structure for invoice generation"""
    id: str
    first_name: str
    last_name: str
    admission_no: str
    class_id: str
    class_name: str
    class_level: str
    enrollment_id: str
    term_id: str
    term_title: str
    term_number: str
    academic_year: str

@dataclass
class InvoiceStatistics:
    """Invoice system statistics"""
    total_invoices: int
    issued: int
    partial: int
    paid: int
    total_value: Decimal
    total_paid: Decimal
    overdue: int
    outstanding: Decimal
    collection_rate: float

def row_to_invoice(row) -> InvoiceRow:
    """Convert database row to InvoiceRow dataclass"""
    return InvoiceRow(
        id=str(row[0]),
        first_name=row[1],
        last_name=row[2],
        admission_no=row[3],
        class_name=row[4],
        class_level=row[5],
        total=Decimal(str(row[6])),
        due_date=row[7],
        created_at=row[8],
        paid_amount=Decimal(str(row[9])),
        status=row[10]
    )

def row_to_student_invoice_detail(row) -> StudentInvoiceDetail:
    """Convert database row to StudentInvoiceDetail dataclass"""
    total = Decimal(str(row[1]))
    paid_amount = Decimal(str(row[11]))
    return StudentInvoiceDetail(
        invoice_id=str(row[0]),
        total=total,
        status=row[2],
        created_at=row[3],
        due_date=row[4],
        term=row[5],
        year=row[6],
        student_name=f"{row[7]} {row[8]}",
        admission_no=row[9],
        class_name=row[10],
        class_level=row[11],
        paid_amount=paid_amount,
        term_title=row[12],
        outstanding=total - paid_amount
    )

def row_to_student_for_invoice(row) -> StudentForInvoice:
    """Convert database row to StudentForInvoice dataclass"""
    return StudentForInvoice(
        id=str(row[0]),
        first_name=row[1],
        last_name=row[2],
        admission_no=row[3],
        class_id=str(row[4]),
        class_name=row[5],
        class_level=row[6],
        enrollment_id=str(row[7]),
        term_id=str(row[8]),
        term_title=row[9],
        term_number=row[10],
        academic_year=row[11]
    )

def row_to_line_item(row) -> InvoiceLineItem:
    """Convert database row to InvoiceLineItem dataclass"""
    return InvoiceLineItem(
        item_name=row[0],
        amount=Decimal(str(row[1]))
    )

def row_to_payment_record(row) -> PaymentRecord:
    """Convert database row to PaymentRecord dataclass"""
    return PaymentRecord(
        amount=Decimal(str(row[0])),
        payment_date=row[1],
        payment_method=row[2],
        reference_no=row[3]
    )

def stats_row_to_dataclass(row) -> InvoiceStatistics:
    """Convert statistics row to InvoiceStatistics dataclass"""
    total_value = Decimal(str(row[4]))
    total_paid = Decimal(str(row[5]))
    outstanding = total_value - total_paid
    collection_rate = (total_paid / total_value * 100) if total_value > 0 else 0
    
    return InvoiceStatistics(
        total_invoices=row[0],
        issued=row[1],
        partial=row[2],
        paid=row[3],
        total_value=total_value,
        total_paid=total_paid,
        overdue=row[6],
        outstanding=outstanding,
        collection_rate=float(collection_rate)
    )