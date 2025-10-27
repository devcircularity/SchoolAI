# handlers/fee/dataclasses.py
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import date, datetime

@dataclass
class CurrentTerm:
    """Current active academic term data"""
    id: str
    title: str
    term_number: int
    start_date: Optional[str]
    end_date: Optional[str]
    year: int
    year_title: str

@dataclass
class FeeSystemStats:
    """Fee system statistics"""
    active_grades: int
    total_structures: int
    total_items: int
    zero_amounts: int
    total_value: float
    completion_rate: float = 0.0

@dataclass
class FeeStructureRow:
    """Fee structure data row"""
    id: str
    name: str
    level: str
    term: int
    year: int
    is_default: bool
    is_published: bool
    item_count: int
    total_amount: float
    zero_items: int
    class_count: int

@dataclass
class FeeItemRow:
    """Fee item data row"""
    item_name: str
    category: str
    is_optional: bool
    billing_cycle: str
    min_amount: float
    max_amount: float
    usage_count: int
    zero_count: int
    avg_amount: float

@dataclass
class CategorySummary:
    """Fee category summary"""
    category: str
    count: int
    total: float
    avg_amount: float
    zero_count: int

@dataclass
class StudentInvoice:
    """Student invoice details"""
    invoice_id: str
    total: float
    status: str
    created_at: datetime
    due_date: Optional[date]
    term: int
    year: int
    student_name: str
    admission_no: str
    class_name: str
    class_level: str
    paid_amount: float
    term_title: str
    outstanding: float

@dataclass
class InvoiceLineItem:
    """Invoice line item"""
    item_name: str
    amount: float

@dataclass
class PaymentRecord:
    """Payment record"""
    amount: float
    created_at: datetime
    method: Optional[str]
    txn_ref: Optional[str]

# Helper functions for data conversion
def row_to_current_term(row) -> Optional[CurrentTerm]:
    """Convert database row to CurrentTerm dataclass"""
    if not row:
        return None
    
    return CurrentTerm(
        id=str(row[0]),
        title=row[1],
        term_number=row[2],
        start_date=_serialize_date(row[3]),
        end_date=_serialize_date(row[4]),
        year=row[5],
        year_title=row[6]
    )

def row_to_fee_stats(row) -> FeeSystemStats:
    """Convert database row to FeeSystemStats"""
    if not row:
        return FeeSystemStats(0, 0, 0, 0, 0.0, 0.0)
    
    active_grades = row[0]
    total_structures = row[1]
    total_items = row[2]
    zero_amounts = row[3]
    total_value = float(row[4])
    
    completion_rate = ((total_items - zero_amounts) / total_items * 100) if total_items > 0 else 0.0
    
    return FeeSystemStats(
        active_grades=active_grades,
        total_structures=total_structures,
        total_items=total_items,
        zero_amounts=zero_amounts,
        total_value=total_value,
        completion_rate=completion_rate
    )

def row_to_fee_structure(row) -> FeeStructureRow:
    """Convert database row to FeeStructureRow"""
    return FeeStructureRow(
        id=str(row[0]),
        name=row[1],
        level=row[2],
        term=row[3],
        year=row[4],
        is_default=row[5],
        is_published=row[6],
        item_count=row[7],
        total_amount=float(row[8]),
        zero_items=row[9],
        class_count=row[10]
    )

def row_to_fee_item(row) -> FeeItemRow:
    """Convert database row to FeeItemRow"""
    return FeeItemRow(
        item_name=row[0],
        category=row[1],
        is_optional=row[2],
        billing_cycle=row[3],
        min_amount=float(row[4]),
        max_amount=float(row[5]),
        usage_count=row[6],
        zero_count=row[7],
        avg_amount=float(row[8])
    )

def row_to_category_summary(row) -> CategorySummary:
    """Convert database row to CategorySummary"""
    return CategorySummary(
        category=row[0],
        count=row[1],
        total=float(row[2]),
        avg_amount=float(row[3]),
        zero_count=row[4]
    )

def row_to_student_invoice(row) -> StudentInvoice:
    """Convert database row to StudentInvoice"""
    total = float(row[1])
    paid_amount = float(row[12])
    
    return StudentInvoice(
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
        term_title=row[13] or f"Term {row[5]}",
        outstanding=total - paid_amount
    )

def row_to_line_item(row) -> InvoiceLineItem:
    """Convert database row to InvoiceLineItem"""
    return InvoiceLineItem(
        item_name=row[0],
        amount=float(row[1])
    )

def row_to_payment(row) -> PaymentRecord:
    """Convert database row to PaymentRecord"""
    return PaymentRecord(
        amount=float(row[0]),
        created_at=row[1],
        method=row[2],
        txn_ref=row[3]
    )

# Utility functions
def _serialize_date(date_obj) -> Optional[str]:
    """Convert date object to string for JSON serialization"""
    if date_obj is None:
        return None
    if isinstance(date_obj, (date, datetime)):
        return date_obj.isoformat()
    return str(date_obj)

def calculate_completion_rate(total_items: int, zero_amounts: int) -> float:
    """Calculate fee setup completion percentage"""
    if total_items == 0:
        return 0.0
    return ((total_items - zero_amounts) / total_items) * 100

def get_term_status(start_date_str: Optional[str], end_date_str: Optional[str]) -> tuple:
    """Determine term status based on current date"""
    if not start_date_str or not end_date_str:
        return "Unknown", "secondary"
    
    try:
        today = date.today()
        start_date = datetime.fromisoformat(start_date_str).date()
        end_date = datetime.fromisoformat(end_date_str).date()
        
        if today < start_date:
            return "Upcoming", "warning"
        elif today > end_date:
            return "Completed", "secondary"
        else:
            return "In Progress", "success"
    except:
        return "Unknown", "secondary"

def format_currency(amount: float) -> str:
    """Format currency amounts consistently"""
    return f"KES {amount:,.2f}"

def normalize_fee_item_name(fee_item: str) -> str:
    """Normalize fee item names to match database values"""
    fee_item_lower = fee_item.lower().strip()
    
    # Common mappings
    mappings = {
        'tuition': 'Tuition',
        'school fees': 'Tuition',
        'lunch': 'Lunch',
        'lunch fee': 'Lunch', 
        'transport': 'Transport',
        'bus': 'Transport',
        'application': 'Application',
        'registration': 'Registration',
        'caution': 'Caution',
        'insurance': 'Annual Student Accident Insurance Cover',
        'accident insurance': 'Annual Student Accident Insurance Cover',
        'workbooks': 'Workbooks',
        'books': 'Workbooks',
        'sports': 'Sports & Games',
        'games': 'Sports & Games',
        'sports & games': 'Sports & Games',
        'music': 'Music & Drama',
        'drama': 'Music & Drama',
        'music & drama': 'Music & Drama',
        'computer': 'Computer Club',
        'computer club': 'Computer Club',
        't-shirt': 'Sports T-Shirt',
        'tshirt': 'Sports T-Shirt',
        'sports t-shirt': 'Sports T-Shirt'
    }
    
    return mappings.get(fee_item_lower, fee_item.title())

def get_category_display_name(category: str) -> str:
    """Get user-friendly category display name"""
    category_names = {
        "TUITION": "Tuition Fees",
        "COCURRICULAR": "Co-curricular Activities",
        "OTHER": "Other Charges"
    }
    return category_names.get(category, category)