# handlers/payment/dataclasses.py
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime, date
from decimal import Decimal

@dataclass
class Student:
    """Student data with guardian information"""
    id: str
    first_name: str
    last_name: str
    admission_no: str
    guardian_email: Optional[str]
    guardian_phone: Optional[str]
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

@dataclass
class OutstandingInvoice:
    """Outstanding invoice data"""
    id: str
    total: Decimal
    status: str
    
    @property
    def total_amount(self) -> float:
        return float(self.total)

@dataclass
class PaymentInfo:
    """Payment information from message or callback"""
    method: str
    amount: float
    admission_no: str
    reference: str
    phone: Optional[str] = None

@dataclass
class PaymentResult:
    """Result of payment processing"""
    success: bool
    message: str
    payment_data: Optional[Dict] = None
    suggestion: Optional[str] = None
    student_data: Optional[Dict] = None

@dataclass
class PaymentStats:
    """Payment system statistics"""
    total_payments: int
    total_collected: float
    invoices_paid: int
    payment_days: int
    avg_payment: float = 0.0

@dataclass
class PaymentMethodBreakdown:
    """Payment method breakdown"""
    method: str
    count: int
    total: float
    
    @property
    def avg_amount(self) -> float:
        return self.total / self.count if self.count > 0 else 0

@dataclass
class RecentPayment:
    """Recent payment data"""
    amount: float
    method: str
    txn_ref: Optional[str]
    posted_at: datetime
    student_name: str
    admission_no: str
    payment_id: str

@dataclass
class StudentPaymentHistory:
    """Student payment history"""
    amount: float
    method: str
    txn_ref: Optional[str]
    posted_at: datetime
    invoice_total: float
    invoice_status: str
    invoice_id: str

@dataclass
class PendingInvoice:
    """Pending invoice data"""
    id: str
    student_name: str
    admission_no: str
    class_name: str
    total: float
    due_date: Optional[date]
    created_at: datetime
    paid_amount: float
    status: str
    
    @property
    def outstanding_amount(self) -> float:
        return self.total - self.paid_amount
    
    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        return self.due_date < date.today()
    
    @property
    def days_overdue(self) -> int:
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

@dataclass
class NotificationResult:
    """Notification sending result"""
    email_sent: bool = False
    whatsapp_sent: bool = False
    email_error: Optional[str] = None
    whatsapp_error: Optional[str] = None

# Helper functions for data conversion
def row_to_student(row) -> Student:
    """Convert database row to Student dataclass"""
    return Student(
        id=str(row[0]),
        first_name=row[1],
        last_name=row[2],
        admission_no=row[3],
        guardian_email=row[4],
        guardian_phone=row[5]
    )

def row_to_outstanding_invoice(row) -> OutstandingInvoice:
    """Convert database row to OutstandingInvoice"""
    return OutstandingInvoice(
        id=str(row[0]),
        total=Decimal(str(row[1])),
        status=row[2]
    )

def row_to_payment_stats(row) -> PaymentStats:
    """Convert database row to PaymentStats"""
    if not row or row[0] == 0:
        return PaymentStats(0, 0.0, 0, 0, 0.0)
    
    total_payments = row[0]
    total_collected = float(row[1])
    invoices_paid = row[2]
    payment_days = row[3]
    avg_payment = total_collected / total_payments if total_payments > 0 else 0.0
    
    return PaymentStats(
        total_payments=total_payments,
        total_collected=total_collected,
        invoices_paid=invoices_paid,
        payment_days=payment_days,
        avg_payment=avg_payment
    )

def row_to_payment_method_breakdown(row) -> PaymentMethodBreakdown:
    """Convert database row to PaymentMethodBreakdown"""
    return PaymentMethodBreakdown(
        method=row[0],
        count=row[1],
        total=float(row[2])
    )

def row_to_recent_payment(row) -> RecentPayment:
    """Convert database row to RecentPayment"""
    return RecentPayment(
        amount=float(row[0]),
        method=row[1],
        txn_ref=row[2],
        posted_at=row[3],
        student_name=f"{row[4]} {row[5]}",
        admission_no=row[6],
        payment_id=str(row[7])
    )

def row_to_student_payment_history(row) -> StudentPaymentHistory:
    """Convert database row to StudentPaymentHistory"""
    return StudentPaymentHistory(
        amount=float(row[0]),
        method=row[1],
        txn_ref=row[2],
        posted_at=row[3],
        invoice_total=float(row[7]),
        invoice_status=row[8],
        invoice_id=str(row[9])
    )

def row_to_pending_invoice(row) -> PendingInvoice:
    """Convert database row to PendingInvoice"""
    return PendingInvoice(
        id=str(row[0]),
        student_name=f"{row[1]} {row[2]}",
        admission_no=row[3],
        class_name=row[4],
        total=float(row[5]),
        due_date=row[6],
        created_at=row[7],
        paid_amount=float(row[8]),
        status=row[9]
    )

# Utility functions
def normalize_payment_method(raw_method: str) -> str:
    """Normalize payment method to match database constraints"""
    method_lower = raw_method.lower().strip()
    
    method_mapping = {
        "mpesa": "MPESA",
        "m-pesa": "MPESA",
        "m pesa": "MPESA",
        "cash": "CASH",
        "bank": "BANK",
        "cheque": "BANK",
        "check": "BANK"
    }
    
    return method_mapping.get(method_lower, "CASH")

def generate_payment_reference() -> str:
    """Generate payment reference for manual payments"""
    from datetime import datetime
    return f"Manual-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def format_currency(amount: float) -> str:
    """Format currency amounts consistently"""
    return f"KES {amount:,.2f}"

def calculate_payment_status(outstanding: float) -> tuple:
    """Calculate payment status and variant"""
    if outstanding <= 0:
        return "PAID", "success"
    elif outstanding > 0:
        return "PENDING", "warning"
    else:
        return "UNKNOWN", "secondary"

def get_urgency_level(days_overdue: int) -> tuple:
    """Get urgency level based on days overdue"""
    if days_overdue <= 0:
        return "current", "info"
    elif days_overdue <= 7:
        return "due_soon", "warning"
    elif days_overdue <= 30:
        return "overdue", "warning"
    else:
        return "urgent", "danger"

def get_method_icon(method: str) -> str:
    """Get icon for payment method"""
    method_icons = {
        "MPESA": "smartphone",
        "CASH": "dollar-sign",
        "BANK": "credit-card"
    }
    return method_icons.get(method, "payment")

def build_payment_data_for_notifications(student: Student, amount: float, method: str, 
                                       reference: str, remaining_balance: float,
                                       invoices_updated: List[Dict], school_id: str, 
                                       school_name: str) -> Dict:
    """Build payment data dictionary for notifications"""
    return {
        "student_id": student.id,
        "student_name": student.full_name,
        "admission_no": student.admission_no,
        "amount_paid": amount,
        "method": method,
        "reference": reference,
        "guardian_email": student.guardian_email,
        "guardian_phone": student.guardian_phone,
        "remaining_balance": remaining_balance,
        "invoices_updated": invoices_updated,
        "school_id": school_id,
        "school_name": school_name
    }

def validate_payment_info(payment_info: PaymentInfo) -> tuple:
    """Validate payment information"""
    errors = []
    
    if not payment_info.admission_no:
        errors.append("Admission number is required")
    
    if payment_info.amount <= 0:
        errors.append("Payment amount must be greater than zero")
    
    if payment_info.amount > 1000000:  # 1M KES limit
        errors.append("Payment amount seems too high (over 1M KES)")
    
    if not payment_info.method:
        errors.append("Payment method is required")
    
    if not payment_info.reference:
        errors.append("Payment reference is required")
    
    return len(errors) == 0, errors

def parse_mpesa_callback_data(callback_data: Dict) -> Optional[PaymentInfo]:
    """Parse M-Pesa callback data into PaymentInfo"""
    transaction_id = callback_data.get("TransID")
    amount = callback_data.get("TransAmount")
    phone_number = callback_data.get("MSISDN")
    account_number = callback_data.get("BillRefNumber") or callback_data.get("AccountNumber")
    
    if not all([transaction_id, amount, account_number]):
        return None
    
    try:
        return PaymentInfo(
            method="MPESA",
            amount=float(amount),
            admission_no=account_number,
            reference=transaction_id,
            phone=phone_number
        )
    except (ValueError, TypeError):
        return None