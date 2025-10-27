# handlers/shared/parsing.py - Reusable extractors across handlers
import re
from typing import Optional, List, Dict

def extract_admission_number(text: str) -> Optional[str]:
    """Extract admission number from text"""
    match = re.search(r'(\d{3,7})', text)
    return match.group(1) if match else None

def extract_name(text: str, patterns: List[str] = None) -> Optional[str]:
    """Extract person name from text using patterns"""
    if patterns is None:
        patterns = [
            r'student\s+([a-zA-Z\s]+)',
            r'name\s+([a-zA-Z\s]+)',
            r'find\s+([a-zA-Z\s]+)',
            r'search\s+([a-zA-Z\s]+)'
        ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            name = match.group(1).strip()
            if len(name) >= 3:  # Minimum name length
                return name
    return None

def extract_amount(text: str) -> Optional[float]:
    """Extract monetary amount from text"""
    # Look for patterns like KES 5000, 5000, 5,000.50
    amount_patterns = [
        r'kes\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*kes',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text.lower())
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                continue
    return None

def extract_grade_level(text: str) -> Optional[str]:
    """Extract CBC grade level from text"""
    grade_patterns = [
        r'(pp[12])',  # PP1, PP2
        r'(grade\s*[1-9])',  # Grade 1-9
        r'(form\s*[1-4])',  # Form 1-4
        r'(class\s*[1-9])',  # Class 1-9
        r'(standard\s*[1-8])'  # Standard 1-8
    ]
    
    text_lower = text.lower()
    for pattern in grade_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1).title()  # Capitalize properly
    return None

def extract_academic_year(text: str) -> Optional[str]:
    """Extract academic year from text"""
    # Look for patterns like 2024, 2024-2025, 2024/2025
    year_patterns = [
        r'(\d{4}-\d{4})',
        r'(\d{4}/\d{4})', 
        r'(\d{4})'
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, text)
        if match:
            year = match.group(1)
            # Validate year range
            if len(year) == 4 and 2020 <= int(year) <= 2030:
                return year
            elif '-' in year or '/' in year:
                return year
    return None

def extract_phone_number(text: str) -> Optional[str]:
    """Extract phone number from text"""
    # Kenyan phone patterns
    phone_patterns = [
        r'(\+254\d{9})',  # +254701234567
        r'(254\d{9})',    # 254701234567
        r'(0\d{9})',      # 0701234567
        r'(\d{10})'       # 701234567 (assume it's missing 0)
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(1)
            # Normalize to standard format
            if phone.startswith('+254'):
                return phone
            elif phone.startswith('254'):
                return '+' + phone
            elif phone.startswith('0'):
                return '+254' + phone[1:]
            elif len(phone) == 10:
                return '+254' + phone
    return None

def extract_email(text: str) -> Optional[str]:
    """Extract email address from text"""
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    match = re.search(email_pattern, text.lower())
    return match.group(1) if match else None

def clean_text_input(text: str) -> str:
    """Clean and normalize text input"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove common filler words at start
    text = re.sub(r'^(please|kindly|can you|show me|tell me|get|find)\s+', '', text.lower())
    return text

def is_confirmation(text: str) -> bool:
    """Check if text is a confirmation (yes/ok/proceed)"""
    confirmations = ['yes', 'y', 'ok', 'okay', 'sure', 'proceed', 'confirm', 'continue']
    return text.lower().strip() in confirmations

def is_cancellation(text: str) -> bool:
    """Check if text is a cancellation (no/cancel/stop)"""
    cancellations = ['no', 'n', 'cancel', 'stop', 'exit', 'quit', 'abort']
    return text.lower().strip() in cancellations

def extract_date_components(text: str) -> Dict[str, Optional[str]]:
    """Extract date components from text"""
    # Look for various date formats
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
        r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})',  # DD Month YYYY
    ]
    
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08', 
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    text_lower = text.lower()
    
    for i, pattern in enumerate(date_patterns):
        match = re.search(pattern, text_lower)
        if match:
            if i == 0:  # DD/MM/YYYY
                return {'day': match.group(1), 'month': match.group(2), 'year': match.group(3)}
            elif i == 1:  # YYYY/MM/DD
                return {'day': match.group(3), 'month': match.group(2), 'year': match.group(1)}
            elif i == 2:  # DD Month YYYY
                month_num = month_map.get(match.group(2)[:3])
                return {'day': match.group(1), 'month': month_num, 'year': match.group(3)}
    
    return {'day': None, 'month': None, 'year': None}

# Common validation functions
def validate_admission_number(admission_no: str, existing_numbers: List[str] = None) -> Dict[str, any]:
    """Validate admission number format and uniqueness"""
    if not admission_no or len(admission_no) < 3:
        return {'valid': False, 'error': 'Admission number must be at least 3 characters'}
    
    if not re.match(r'^[a-zA-Z0-9]+$', admission_no):
        return {'valid': False, 'error': 'Admission number can only contain letters and numbers'}
    
    if existing_numbers and admission_no in existing_numbers:
        return {'valid': False, 'error': 'Admission number already exists'}
    
    return {'valid': True, 'normalized': admission_no.upper()}

def validate_email_format(email: str) -> Dict[str, any]:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email:
        return {'valid': False, 'error': 'Email is required'}
    
    if not re.match(email_pattern, email):
        return {'valid': False, 'error': 'Invalid email format'}
    
    return {'valid': True, 'normalized': email.lower()}

def validate_phone_format(phone: str) -> Dict[str, any]:
    """Validate and normalize phone number"""
    if not phone:
        return {'valid': False, 'error': 'Phone number is required'}
    
    # Remove spaces and special chars except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check length after cleaning
    digits_only = re.sub(r'[^\d]', '', cleaned)
    if len(digits_only) < 9 or len(digits_only) > 15:
        return {'valid': False, 'error': 'Phone number must have 9-15 digits'}
    
    # Normalize to international format for Kenya
    if cleaned.startswith('+254'):
        normalized = cleaned
    elif cleaned.startswith('254'):
        normalized = '+' + cleaned
    elif cleaned.startswith('0') and len(digits_only) == 10:
        normalized = '+254' + cleaned[1:]
    elif len(digits_only) == 9:
        normalized = '+254' + cleaned
    else:
        normalized = cleaned  # Keep as is for international numbers
    
    return {'valid': True, 'normalized': normalized}