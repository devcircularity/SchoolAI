# handlers/shared/payment_utils.py - Shared payment utilities
import re
from typing import Optional, Dict, List, Tuple
from decimal import Decimal
from datetime import datetime, date

def extract_payment_amount(text: str) -> Optional[float]:
    """Extract payment amount from text"""
    # Look for patterns like "payment of 15000", "15000 KES", "KES 25000"
    amount_patterns = [
        r'payment\s+of\s+(\d+(?:\.\d{1,2})?)',
        r'(\d+(?:\.\d{1,2})?)\s+kes',
        r'kes\s+(\d+(?:\.\d{1,2})?)',
        r'amount\s+(\d+(?:\.\d{1,2})?)',
        r'pay\s+(\d+(?:\.\d{1,2})?)',
        r'(\d+(?:\.\d{1,2})?)(?:\s+shillings?)?'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                amount = float(match.group(1))
                if 1 <= amount <= 1000000:  # Reasonable range for payments
                    return amount
            except ValueError:
                continue
    return None

def extract_admission_number_from_payment(text: str) -> Optional[str]:
    """Extract student admission number from payment text"""
    patterns = [
        r'student\s+(\d{3,7})',
        r'for\s+student\s+(\d{3,7})',
        r'admission\s+(?:no|number)\s+(\d{3,7})',
        r'account\s+(?:no|number)\s+(\d{3,7})',
        r'student\s+(?:id|number)\s+(\d{3,7})',
        r'(?:^|\s)(\d{4,7})(?:\s|$)'  # Standalone number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1)
    
    return None

def extract_payment_method(text: str) -> Optional[str]:
    """Extract payment method from text"""
    method_patterns = [
        (r'm-?pesa|mpesa', 'MPESA'),
        (r'cash|physical|hand', 'CASH'),
        (r'bank|transfer|cheque|check|deposit', 'BANK'),
        (r'mobile\s+money', 'MPESA'),
        (r'online', 'BANK')
    ]
    
    text_lower = text.lower()
    for pattern, method in method_patterns:
        if re.search(pattern, text_lower):
            return method
    
    return None

def extract_payment_reference(text: str) -> Optional[str]:
    """Extract payment reference from text"""
    ref_patterns = [
        r'ref(?:erence)?\s+([A-Z0-9]{6,15})',
        r'transaction\s+(?:id|ref)\s+([A-Z0-9]{6,15})',
        r'receipt\s+(?:no|number)\s+([A-Z0-9]{6,15})',
        r'confirmation\s+([A-Z0-9]{6,15})',
        r'([A-Z0-9]{8,12})'  # Generic alphanumeric codes
    ]
    
    for pattern in ref_patterns:
        match = re.search(pattern, text.upper())
        if match:
            return match.group(1)
    
    return None

def parse_payment_command(text: str) -> Dict[str, any]:
    """Parse comprehensive payment command"""
    result = {
        'method': None,
        'amount': None,
        'admission_no': None,
        'reference': None,
        'confidence': 0,
        'missing_fields': []
    }
    
    # Extract components
    result['method'] = extract_payment_method(text)
    result['amount'] = extract_payment_amount(text)
    result['admission_no'] = extract_admission_number_from_payment(text)
    result['reference'] = extract_payment_reference(text)
    
    # Calculate confidence and missing fields
    if result['method']:
        result['confidence'] += 25
    else:
        result['missing_fields'].append('payment method')
    
    if result['amount']:
        result['confidence'] += 40
    else:
        result['missing_fields'].append('amount')
    
    if result['admission_no']:
        result['confidence'] += 30
    else:
        result['missing_fields'].append('student admission number')
    
    if result['reference']:
        result['confidence'] += 5
    
    return result

def validate_payment_amount(amount: float) -> Tuple[bool, Optional[str]]:
    """Validate payment amount"""
    if amount <= 0:
        return False, "Payment amount must be greater than zero"
    
    if amount > 1000000:  # 1M KES limit
        return False, "Payment amount seems too high (over 1M KES)"
    
    if amount < 1:
        return False, "Payment amount too small (minimum 1 KES)"
    
    return True, None

def validate_admission_number(admission_no: str) -> Tuple[bool, Optional[str]]:
    """Validate admission number format"""
    if not admission_no:
        return False, "Admission number is required"
    
    if len(admission_no) < 3:
        return False, "Admission number too short (minimum 3 characters)"
    
    if len(admission_no) > 10:
        return False, "Admission number too long (maximum 10 characters)"
    
    if not re.match(r'^[a-zA-Z0-9]+$', admission_no):
        return False, "Admission number can only contain letters and numbers"
    
    return True, None

def validate_payment_method(method: str) -> Tuple[bool, Optional[str]]:
    """Validate payment method"""
    valid_methods = ['MPESA', 'CASH', 'BANK']
    
    if not method:
        return False, "Payment method is required"
    
    if method.upper() not in valid_methods:
        return False, f"Invalid payment method. Must be one of: {', '.join(valid_methods)}"
    
    return True, None

def normalize_phone_number(phone: str) -> Optional[str]:
    """Normalize phone number to international format"""
    if not phone:
        return None
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    digits_only = re.sub(r'[^\d]', '', cleaned)
    
    # Kenyan phone number normalization
    if cleaned.startswith('+254'):
        return cleaned if len(digits_only) == 12 else None
    elif cleaned.startswith('254'):
        return '+' + cleaned if len(digits_only) == 12 else None
    elif cleaned.startswith('0') and len(digits_only) == 10:
        return '+254' + cleaned[1:]
    elif len(digits_only) == 9:
        return '+254' + cleaned
    else:
        return cleaned if 9 <= len(digits_only) <= 15 else None

def generate_payment_reference(prefix: str = "PAY") -> str:
    """Generate unique payment reference"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}-{timestamp}"

def calculate_payment_distribution(payments: List[Dict]) -> Dict[str, any]:
    """Calculate payment method distribution statistics"""
    if not payments:
        return {"total": 0, "methods": {}, "avg_amount": 0}
    
    method_stats = {}
    total_amount = 0
    
    for payment in payments:
        method = payment.get('method', 'UNKNOWN')
        amount = float(payment.get('amount', 0))
        
        if method not in method_stats:
            method_stats[method] = {'count': 0, 'total': 0, 'amounts': []}
        
        method_stats[method]['count'] += 1
        method_stats[method]['total'] += amount
        method_stats[method]['amounts'].append(amount)
        total_amount += amount
    
    # Calculate percentages and averages
    for method in method_stats:
        stats = method_stats[method]
        stats['percentage'] = (stats['total'] / total_amount * 100) if total_amount > 0 else 0
        stats['avg_amount'] = stats['total'] / stats['count'] if stats['count'] > 0 else 0
        stats['min_amount'] = min(stats['amounts']) if stats['amounts'] else 0
        stats['max_amount'] = max(stats['amounts']) if stats['amounts'] else 0
        del stats['amounts']  # Remove raw amounts to save space
    
    return {
        "total": len(payments),
        "total_amount": total_amount,
        "avg_amount": total_amount / len(payments) if payments else 0,
        "methods": method_stats
    }

def format_payment_summary(stats: Dict) -> str:
    """Format payment statistics into readable summary"""
    if stats['total'] == 0:
        return "No payments recorded"
    
    summary = f"Payment Summary: {stats['total']} payments totaling KES {stats['total_amount']:,.2f}\n"
    summary += f"Average payment: KES {stats['avg_amount']:,.2f}\n\n"
    
    if stats['methods']:
        summary += "Payment Methods:\n"
        for method, method_stats in sorted(stats['methods'].items(), key=lambda x: x[1]['total'], reverse=True):
            summary += f"• {method}: {method_stats['count']} payments, "
            summary += f"KES {method_stats['total']:,.2f} ({method_stats['percentage']:.1f}%)\n"
    
    return summary

def get_overdue_urgency_level(days_overdue: int) -> Tuple[str, str]:
    """Get urgency level and color for overdue payments"""
    if days_overdue <= 0:
        return "current", "success"
    elif days_overdue <= 7:
        return "due_soon", "warning"
    elif days_overdue <= 30:
        return "overdue", "warning"
    elif days_overdue <= 60:
        return "seriously_overdue", "danger"
    else:
        return "critical", "danger"

def calculate_collection_rate(total_invoiced: float, total_collected: float) -> float:
    """Calculate collection rate percentage"""
    if total_invoiced <= 0:
        return 100.0  # No invoices means 100% collection rate
    
    return min(100.0, (total_collected / total_invoiced) * 100)

def suggest_payment_actions(outstanding_amount: float, days_overdue: int, 
                          payment_history_count: int) -> List[str]:
    """Suggest appropriate payment actions based on context"""
    actions = []
    
    if outstanding_amount <= 0:
        actions.extend([
            "Account is current - no action needed",
            "Consider generating next term's invoice"
        ])
    elif days_overdue <= 0:
        actions.extend([
            "Send friendly payment reminder",
            "Provide payment instructions"
        ])
    elif days_overdue <= 7:
        actions.extend([
            "Send urgent payment reminder",
            "Call parent/guardian if possible"
        ])
    elif days_overdue <= 30:
        actions.extend([
            "Send final notice",
            "Schedule parent meeting",
            "Consider payment plan options"
        ])
    else:
        actions.extend([
            "Escalate to administration",
            "Consider account restrictions",
            "Formal collection procedures"
        ])
    
    # Add context-specific actions
    if payment_history_count == 0:
        actions.append("First-time payer - provide clear instructions")
    elif payment_history_count > 5:
        actions.append("Regular payer - may be temporary issue")
    
    if outstanding_amount > 50000:  # High value
        actions.append("High-value account - prioritize follow-up")
    
    return actions[:4]  # Return top 4 suggestions

def parse_mpesa_webhook_data(webhook_data: Dict) -> Optional[Dict]:
    """Parse M-Pesa webhook data into standardized format"""
    try:
        # Common M-Pesa webhook fields
        transaction_id = webhook_data.get("TransID")
        amount = float(webhook_data.get("TransAmount", 0))
        phone = webhook_data.get("MSISDN")
        account_number = webhook_data.get("BillRefNumber") or webhook_data.get("AccountNumber")
        transaction_time = webhook_data.get("TransTime")
        
        if not all([transaction_id, amount, account_number]):
            return None
        
        return {
            "transaction_id": transaction_id,
            "amount": amount,
            "phone_number": normalize_phone_number(phone),
            "account_number": account_number,
            "transaction_time": transaction_time,
            "method": "MPESA",
            "reference": transaction_id,
            "raw_data": webhook_data
        }
        
    except (ValueError, TypeError, KeyError):
        return None

def build_payment_notification_data(student_info: Dict, payment_info: Dict, 
                                   balance_info: Dict, school_info: Dict) -> Dict:
    """Build comprehensive payment notification data"""
    return {
        # Student information
        "student_id": student_info.get("id"),
        "student_name": student_info.get("name"),
        "admission_no": student_info.get("admission_no"),
        "class_name": student_info.get("class_name"),
        
        # Guardian information
        "guardian_name": student_info.get("guardian_name"),
        "guardian_email": student_info.get("guardian_email"),
        "guardian_phone": student_info.get("guardian_phone"),
        
        # Payment information
        "amount_paid": payment_info.get("amount"),
        "payment_method": payment_info.get("method"),
        "payment_reference": payment_info.get("reference"),
        "payment_date": payment_info.get("date", datetime.now()),
        
        # Balance information
        "previous_balance": balance_info.get("previous_balance", 0),
        "remaining_balance": balance_info.get("remaining_balance", 0),
        "account_status": "PAID" if balance_info.get("remaining_balance", 0) <= 0 else "PARTIAL",
        
        # School information
        "school_id": school_info.get("id"),
        "school_name": school_info.get("name"),
        "school_contact": school_info.get("contact"),
        
        # Notification metadata
        "notification_time": datetime.now(),
        "notification_type": "payment_confirmation"
    }