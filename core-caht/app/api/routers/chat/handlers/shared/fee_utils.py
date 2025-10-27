# handlers/shared/fee_utils.py - Shared fee utilities
import re
from typing import Optional, Dict, List

def extract_fee_amount(text: str) -> Optional[float]:
    """Extract fee amount from text"""
    # Look for patterns like "set to 5000", "update to KES 15000", "change to 25000.50"
    amount_patterns = [
        r'(?:to|=)\s*(?:kes\s*)?(\d{1,6}(?:\.\d{1,2})?)',
        r'(?:kes\s*)?(\d{1,6}(?:\.\d{1,2})?)\s*(?:kes|shillings?)?',
        r'amount\s+(?:of\s+)?(?:kes\s*)?(\d{1,6}(?:\.\d{1,2})?)'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                amount = float(match.group(1))
                if 0 <= amount <= 1000000:  # Reasonable range for school fees
                    return amount
            except ValueError:
                continue
    return None

def extract_fee_item_name(text: str) -> Optional[str]:
    """Extract fee item name from update commands"""
    # Patterns to extract fee item names
    patterns = [
        r'(?:update|set|change)\s+([^0-9]+?)\s+(?:to|=|for)',
        r'(?:update|set|change)\s+([^0-9]+?)(?:\s+fee)?$',
        r'([a-z\s&]+)\s+(?:fee|fees)\s+(?:to|=)',
        r'(?:fee|fees)\s+for\s+([a-z\s&]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            fee_item = match.group(1).strip()
            # Remove common stop words
            fee_item = re.sub(r'\b(fee|fees|amount|to|for|the)\b', '', fee_item).strip()
            
            if len(fee_item) >= 3:  # Must be at least 3 characters
                return fee_item.title()
    
    return None

def normalize_fee_category(category: str) -> str:
    """Normalize fee category names"""
    category_lower = category.lower().strip()
    
    mappings = {
        'tuition': 'TUITION',
        'academic': 'TUITION',
        'school fees': 'TUITION',
        'learning': 'TUITION',
        
        'sports': 'COCURRICULAR',
        'games': 'COCURRICULAR', 
        'sports & games': 'COCURRICULAR',
        'music': 'COCURRICULAR',
        'drama': 'COCURRICULAR',
        'computer': 'COCURRICULAR',
        'club': 'COCURRICULAR',
        'activity': 'COCURRICULAR',
        'activities': 'COCURRICULAR',
        'cocurricular': 'COCURRICULAR',
        'co-curricular': 'COCURRICULAR',
        
        'transport': 'OTHER',
        'lunch': 'OTHER',
        'uniform': 'OTHER',
        'books': 'OTHER',
        'stationery': 'OTHER',
        'insurance': 'OTHER',
        'medical': 'OTHER',
        'caution': 'OTHER',
        'registration': 'OTHER',
        'application': 'OTHER'
    }
    
    return mappings.get(category_lower, 'OTHER')

def validate_fee_amount(amount: float) -> Dict[str, any]:
    """Validate fee amount"""
    if amount < 0:
        return {'valid': False, 'error': 'Fee amount cannot be negative'}
    
    if amount > 1000000:  # 1 million KES limit
        return {'valid': False, 'error': 'Fee amount seems too high (over 1M KES)'}
    
    if amount == 0:
        return {'valid': True, 'warning': 'Setting fee to zero - this will make it free'}
    
    return {'valid': True, 'normalized': round(amount, 2)}

def parse_fee_update_command(text: str) -> Dict[str, any]:
    """Parse comprehensive fee update command"""
    result = {
        'fee_item': None,
        'amount': None,
        'grade_level': None,
        'scope': 'all_grades',
        'confidence': 0
    }
    
    # Extract fee item
    fee_item = extract_fee_item_name(text)
    if fee_item:
        result['fee_item'] = fee_item
        result['confidence'] += 30
    
    # Extract amount
    amount = extract_fee_amount(text)
    if amount is not None:
        result['amount'] = amount
        result['confidence'] += 40
    
    # Extract grade level if specified
    grade_patterns = [
        r'for\s+(grade\s*\d+|pp\s*\d+|form\s*\d+|class\s*\d+)',
        r'(grade\s*\d+|pp\s*\d+|form\s*\d+)\s+(?:only|specifically)',
        r'only\s+(grade\s*\d+|pp\s*\d+|form\s*\d+)'
    ]
    
    for pattern in grade_patterns:
        match = re.search(pattern, text.lower())
        if match:
            result['grade_level'] = match.group(1).strip().title()
            result['scope'] = 'grade_specific'
            result['confidence'] += 20
            break
    
    # Check for scope indicators
    if any(word in text.lower() for word in ['all grades', 'all classes', 'everywhere', 'all students']):
        result['scope'] = 'all_grades'
        result['confidence'] += 10
    
    return result

def format_fee_command_suggestions(fee_items: List[str]) -> List[str]:
    """Generate contextual fee update suggestions"""
    suggestions = []
    
    # Common fee items with reasonable amounts
    common_fees = {
        'Tuition': ['25000', '30000', '35000'],
        'Lunch': ['3000', '5000', '7000'], 
        'Transport': ['5000', '8000', '10000'],
        'Sports & Games': ['2000', '3000', '5000'],
        'Computer Club': ['2000', '3000', '4000'],
        'Music & Drama': ['1500', '2500', '3500']
    }
    
    # Add suggestions based on available fee items
    for item in fee_items[:3]:  # Top 3 items
        if item in common_fees:
            amount = common_fees[item][1]  # Middle amount
            suggestions.append(f"Set {item} to {amount}")
    
    # Add generic suggestions
    suggestions.extend([
        "Update tuition fees",
        "Set lunch fee to 5000", 
        "Change transport fees",
        "Update fees for Grade 1"
    ])
    
    return suggestions[:4]  # Return max 4 suggestions

def extract_billing_cycle(text: str) -> str:
    """Extract billing cycle from text"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['annual', 'yearly', 'year', 'once per year']):
        return 'ANNUAL'
    elif any(word in text_lower for word in ['term', 'termly', 'per term', 'each term']):
        return 'TERM'
    elif any(word in text_lower for word in ['month', 'monthly', 'per month']):
        return 'MONTHLY'
    elif any(word in text_lower for word in ['week', 'weekly', 'per week']):
        return 'WEEKLY'
    else:
        return 'TERM'  # Default to term-based billing

def is_optional_fee(text: str) -> bool:
    """Determine if fee should be marked as optional"""
    text_lower = text.lower()
    
    optional_indicators = [
        'optional', 'choice', 'voluntary', 'elective',
        'if interested', 'if desired', 'on request'
    ]
    
    required_indicators = [
        'required', 'mandatory', 'compulsory', 'must pay',
        'all students', 'everyone', 'tuition', 'academic'
    ]
    
    # Check for explicit indicators
    if any(indicator in text_lower for indicator in optional_indicators):
        return True
    
    if any(indicator in text_lower for indicator in required_indicators):
        return False
    
    # Infer from fee item name
    optional_fee_names = [
        'computer club', 'music', 'drama', 'sports t-shirt',
        'extra classes', 'coaching', 'club', 'activity'
    ]
    
    if any(name in text_lower for name in optional_fee_names):
        return True
    
    return False  # Default to required

def generate_fee_item_variations(item_name: str) -> List[str]:
    """Generate variations of fee item names for fuzzy matching"""
    variations = [item_name.lower()]
    
    # Common variations
    if 'tuition' in item_name.lower():
        variations.extend(['school fees', 'academic fees', 'learning fees'])
    elif 'lunch' in item_name.lower():
        variations.extend(['meal', 'food', 'feeding'])
    elif 'transport' in item_name.lower():
        variations.extend(['bus', 'travel', 'commute'])
    elif 'sports' in item_name.lower():
        variations.extend(['games', 'physical education', 'pe'])
    elif 'computer' in item_name.lower():
        variations.extend(['ict', 'technology', 'tech'])
    
    # Add abbreviated forms
    words = item_name.split()
    if len(words) > 1:
        # Add acronym
        acronym = ''.join(word[0].lower() for word in words)
        variations.append(acronym)
        
        # Add individual words
        variations.extend([word.lower() for word in words])
    
    return list(set(variations))  # Remove duplicates

def calculate_fee_statistics(fee_data: List[Dict]) -> Dict[str, any]:
    """Calculate comprehensive fee statistics"""
    if not fee_data:
        return {
            'total_items': 0,
            'total_value': 0.0,
            'average_fee': 0.0,
            'zero_amounts': 0,
            'completion_rate': 0.0,
            'categories': {},
            'grade_distribution': {}
        }
    
    total_items = len(fee_data)
    total_value = sum(item.get('amount', 0) for item in fee_data)
    zero_amounts = sum(1 for item in fee_data if item.get('amount', 0) == 0)
    
    # Category breakdown
    categories = {}
    for item in fee_data:
        category = item.get('category', 'OTHER')
        if category not in categories:
            categories[category] = {'count': 0, 'total': 0}
        categories[category]['count'] += 1
        categories[category]['total'] += item.get('amount', 0)
    
    # Grade distribution
    grade_distribution = {}
    for item in fee_data:
        grade = item.get('grade', 'Unknown')
        if grade not in grade_distribution:
            grade_distribution[grade] = {'count': 0, 'total': 0}
        grade_distribution[grade]['count'] += 1
        grade_distribution[grade]['total'] += item.get('amount', 0)
    
    return {
        'total_items': total_items,
        'total_value': total_value,
        'average_fee': total_value / total_items if total_items > 0 else 0,
        'zero_amounts': zero_amounts,
        'completion_rate': ((total_items - zero_amounts) / total_items * 100) if total_items > 0 else 0,
        'categories': categories,
        'grade_distribution': grade_distribution
    }