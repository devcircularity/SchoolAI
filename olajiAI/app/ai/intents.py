# app/ai/intents.py - Fixed with better fee structure patterns

import re
from typing import Dict, Any, Optional, List

# Existing patterns
CREATE_CLASS_PAT = re.compile(r"\b(create|new|add|let's add)\s+(a\s+)?(class|grade)\b", re.I)
ENROLL_PAT = re.compile(r"\b(en[rt]oll?|admit|register|add)\b.*(student|pupil)\b", re.I)
NOTIFY_PAT = re.compile(r"\b(notify|send|message|remind|reminder)\b", re.I)
SCHOOL_FACTS_PAT = re.compile(r"\b(what(?:'s| is)\s+the\s+name\s+of\s+(?:our|the)\s+school\b|school\s+name\b)", re.I)
NAME_OF_SCHOOL_PAT = re.compile(r"\b(name\s+of\s+(?:our|the)\s+school\b)", re.I)
CLASS_QUERY_PAT = re.compile(r"\b(how\s+many|count|list|show|get).*(class|classes|grade|grades)\b", re.I)
STUDENT_QUERY_PAT = re.compile(r"\b(how\s+many|count|list|show|get).*(student|students)\b", re.I)
CLASS_STUDENT_PAT = re.compile(r"\b(list|show|display).*(classes?|students?).*(?:per|in|by|and).*(?:class|student|grade|number)\b", re.I)

# Enhanced fee patterns with BETTER PRIORITY and more specific matching
FEE_STRUCTURE_VIEW_PATTERNS = [
    r"\b(show|view|display|get|what(?:'s| is)?)\s+(fee\s+)?(structure|fees?)\b",
    r"\b(fee\s+structure|structure)\s+(for|of)\b",
    r"\b(grade\s+\d+|pp[12]|jss\s+\d+)\s+(fee|fees|structure)\b",
    r"\bhow\s+does?\s+(?:our|the)?\s*fee\s+structure\s+look\b",
    r"\bwhat\s+(?:is|are)\s+(?:the\s+)?(?:grade\s+\d+|pp[12])\s+fee",
]

SET_PRICES_PATTERNS = [
    r"\b(set|update|change)\s+(fee\s+)?prices?\b",
    r"\b(set|update)\s+(tuition|activity|exam|lunch|transport)\s+(to|:|\d)",
    r"\b\w+\s*:\s*\d+\b",  # Pattern like "Tuition: 15000"
    r"\bset\s+.*\s+fees?\s+(at|to)\s+\d+",  # "Set Grade 1 fees at 10000"
    r"\bset\s+.*\s+term\s+\d+\s+fees?\s+(at|to)\s+\d+",  # "Set Grade 1 Term 1 fees at 10000"
    r"\bmake\s+.*\s+fees?\s+(at|to|cost)\s+\d+",  # "Make Grade 1 fees at 10000"
    r"\bupdate\s+.*\s+fees?\s+(at|to)\s+\d+",  # "Update Grade 1 fees at 10000"
]

PUBLISH_PATTERNS = [r"\bpublish\b", r"\block\b", r"\bfinali[sz]e\b"]

GEN_INV_PATTERNS = [
    r"\b(generate|issue|create)\s+invoices?\b", 
    r"\bbill\s+(students?|class|classes)\b",
    r"\binvoice\s+(generation|students?)\b"
]

FEE_ADJUST_PAT = re.compile(r"\b(increase|decrease|add|remove)\b.+\b(fee|tuition|structure)\b", re.I)

def detect_intent(text: str) -> Optional[str]:
    """Detect user intent from message text with improved fee detection"""
    t = text.lower()
    
    print(f"🔍 DEBUG: Checking intent for: '{text}'")
    
    # Fee structure view (HIGHEST PRIORITY - check first)
    if any(re.search(p, text, re.I) for p in FEE_STRUCTURE_VIEW_PATTERNS):
        print(f"🔍 DEBUG: Matched view_fee_structure via patterns")
        return "view_fee_structure"
    
    # Special check for fee-related queries that mention specific grades
    if re.search(r"\b(grade\s+\d+|pp[12]|jss\s+\d+)\b", t) and re.search(r"\bfee", t):
        print(f"🔍 DEBUG: Matched view_fee_structure via grade+fee combo")
        return "view_fee_structure"
    
    # Generate invoices (high priority)
    if any(re.search(p, t) for p in GEN_INV_PATTERNS):
        print(f"🔍 DEBUG: Matched generate_invoices")
        return "generate_invoices"
    
    # Price setting (specific patterns)
    if any(re.search(p, t) for p in SET_PRICES_PATTERNS) or _has_clear_price_pairs(t):
        print(f"🔍 DEBUG: Matched set_fee_prices")
        return "set_fee_prices"
    
    # Publish fee structure
    if any(re.search(p, t) for p in PUBLISH_PATTERNS) and re.search(r"\bfee", t):
        print(f"🔍 DEBUG: Matched publish_fee_structure") 
        return "publish_fee_structure"
    
    # Fee adjustments
    if FEE_ADJUST_PAT.search(text):
        print(f"🔍 DEBUG: Matched adjust_fee")
        return "adjust_fee"
    
    # Existing intents (AFTER fee intents to avoid conflicts)
    if CREATE_CLASS_PAT.search(text):
        print(f"🔍 DEBUG: Matched create_class")
        return "create_class"
    if CLASS_STUDENT_PAT.search(text):
        print(f"🔍 DEBUG: Matched class_student_analytics")
        return "class_student_analytics"
    if CLASS_QUERY_PAT.search(text):
        print(f"🔍 DEBUG: Matched class_query")
        return "class_query"
    if STUDENT_QUERY_PAT.search(text):
        print(f"🔍 DEBUG: Matched student_query")
        return "student_query"
    if ENROLL_PAT.search(text):
        print(f"🔍 DEBUG: Matched enroll_student")
        return "enroll_student"
    if NOTIFY_PAT.search(text):
        print(f"🔍 DEBUG: Matched send_notification")
        return "send_notification"
    
    # School facts LAST (most restrictive patterns)
    if SCHOOL_FACTS_PAT.search(text) or NAME_OF_SCHOOL_PAT.search(text):
        print(f"🔍 DEBUG: Matched school_facts")
        return "school_facts"
    
    print(f"🔍 DEBUG: NO INTENT MATCHED - falling back to LLM")
    return None

# Enhanced price pair detection for CBC grades
CBC_LEVEL_PAT = re.compile(
    r"(?P<level>PP[12]|Grade\s+\d+|JSS\s+\d+|Senior\s+\d+)\s+"
    r"(?P<fee_name>[A-Za-z\s/()]+?)\s*[:=-]\s*"
    r"(?P<amount>\d{1,3}(?:[,\s]?\d{3})*(?:\.\d{1,2})?)", 
    re.IGNORECASE
)

SIMPLE_PRICE_PAT = re.compile(
    r"(?P<fee_name>(?:tuition|ballet|chess|transport|lunch|insurance|workbooks|registration)(?:\s+fee)?)\s*[:=-]\s*"
    r"(?P<amount>\d{1,3}(?:[,\s]?\d{3})*(?:\.\d{1,2})?)", 
    re.IGNORECASE
)

# New pattern for natural language fee setting: "Set Grade 1 fees at 10000"
NATURAL_FEE_PAT = re.compile(
    r"\b(set|update|make|change)\s+"
    r"(?P<level>PP[12]|Grade\s+\d+|JSS\s+\d+|Senior\s+\d+)?\s*"
    r"(?:term\s+(?P<term>\d+)\s+)?"
    r"(?P<fee_name>tuition|fees?|ballet|chess|transport|lunch|insurance|workbooks|registration)?\s+"
    r"(?:at|to|cost)\s+"
    r"(?P<amount>\d{1,3}(?:[,\s]?\d{3})*(?:\.\d{1,2})?)",
    re.IGNORECASE
)

def _has_clear_price_pairs(text: str) -> bool:
    """Check if text clearly contains price setting patterns"""
    return bool(CBC_LEVEL_PAT.search(text) or SIMPLE_PRICE_PAT.search(text) or NATURAL_FEE_PAT.search(text))

def extract_price_pairs(text: str) -> List[Dict[str, Any]]:
    """Extract fee name and amount pairs with CBC level support"""
    pairs = []
    
    # First try level-specific patterns: "Grade 1 Tuition: 150000"
    for m in CBC_LEVEL_PAT.finditer(text):
        level = m.group("level").strip()
        fee_name = m.group("fee_name").strip().rstrip(",.")
        amt_raw = m.group("amount").replace(",", "").replace(" ", "")
        
        try:
            amount = float(amt_raw)
        except ValueError:
            continue
        
        pairs.append({
            "item_name": _normalize_fee_name(fee_name),
            "amount": amount,
            "level": level
        })
    
    # Try natural language patterns: "Set Grade 1 fees at 10000"
    if not pairs:
        for m in NATURAL_FEE_PAT.finditer(text):
            level = m.group("level")
            term = m.group("term")
            fee_name = m.group("fee_name") or "fees"  # Default to "fees" if not specified
            amt_raw = m.group("amount").replace(",", "").replace(" ", "")
            
            try:
                amount = float(amt_raw)
            except ValueError:
                continue
            
            # If fee_name is generic "fees", default to "Tuition"
            if fee_name.lower() in ["fees", "fee"]:
                fee_name = "Tuition"
            
            pair_data = {
                "item_name": _normalize_fee_name(fee_name),
                "amount": amount,
                "level": level.strip() if level else None
            }
            
            if term:
                pair_data["term"] = int(term)
            
            pairs.append(pair_data)
    
    # Then try simple patterns: "Tuition: 150000" (applies to current context)
    if not pairs:
        for m in SIMPLE_PRICE_PAT.finditer(text):
            fee_name = m.group("fee_name").strip().rstrip(",.")
            amt_raw = m.group("amount").replace(",", "").replace(" ", "")
            
            try:
                amount = float(amt_raw)
            except ValueError:
                continue
            
            pairs.append({
                "item_name": _normalize_fee_name(fee_name),
                "amount": amount,
                "level": None  # Will be determined by context
            })
    
    return pairs

def _normalize_fee_name(name: str) -> str:
    """Normalize fee names to match your CBC catalog"""
    norm = name.lower().strip()
    canonical_names = {
        "tuition": "Tuition",
        "ballet": "Ballet / Dance",
        "dance": "Ballet / Dance", 
        "chess": "Chess",
        "swimming": "Swimming (KG/Clubs)",
        "french": "French (KG/Clubs)",
        "tennis": "Tennis",
        "football": "Football Academy (Sat)",
        "coding": "Coding",
        "robotics": "Robotics",
        "transport": "Transport",
        "lunch": "Lunch",
        "insurance": "Annual Student Accident Insurance Cover",
        "workbooks": "Workbooks",
        "registration": "Registration",
        "application": "Application",
        "caution": "Caution",
    }
    return canonical_names.get(norm, name.title())

def extract_slots(intent: str, text: str) -> Dict[str, Any]:
    """Extract relevant parameters based on intent"""
    slots: Dict[str, Any] = {}
    t = text.strip()

    if intent == "view_fee_structure":
        # Extract CBC level - more comprehensive patterns
        level_patterns = [
            r"\b(PP[12])\b",
            r"\b(Grade\s+\d+)\b", 
            r"\b(JSS\s+\d+)\b",
            r"\b(Senior\s+\d+)\b",
            r"\b(grade\s+\d+)\b"  # lowercase variant
        ]
        
        for pattern in level_patterns:
            level_match = re.search(pattern, t, re.I)
            if level_match:
                level = level_match.group(1).title()
                # Normalize "grade 5" to "Grade 5"
                if level.lower().startswith("grade "):
                    level = "Grade " + level.split()[-1]
                slots["level"] = level
                break
        
        # Extract term/year
        term_match = re.search(r"\bterm\s+(\d+)\b", t, re.I)
        if term_match:
            slots["term"] = int(term_match.group(1))
        
        year_match = re.search(r"\b(20\d{2})\b", t)
        if year_match:
            slots["year"] = int(year_match.group(1))

    elif intent == "set_fee_prices":
        pairs = extract_price_pairs(text)
        slots["price_pairs"] = pairs
        
        # Extract context if not in pairs
        if not any(p.get("level") for p in pairs):
            level_match = re.search(r"\b(PP[12]|Grade\s+\d+|JSS\s+\d+|Senior\s+\d+)\b", t, re.I)
            if level_match:
                slots["default_level"] = level_match.group(1).title()
        
        # Extract term/year context
        term_match = re.search(r"\bterm\s+(\d+)\b", t, re.I)
        if term_match:
            slots["term"] = int(term_match.group(1))
        
        year_match = re.search(r"\b(20\d{2})\b", t)
        if year_match:
            slots["year"] = int(year_match.group(1))

    elif intent == "adjust_fee":
        # Extract CBC level
        level_match = re.search(r"\b(PP[12]|Grade\s+\d+|JSS\s+\d+|Senior\s+\d+)\b", t, re.I)
        if level_match:
            slots["level"] = level_match.group(1).title()
        
        # Extract operation and details
        op_match = re.search(r"\b(increase|decrease|raise|lower)\b", t, re.I)
        if op_match:
            slots["operation"] = "increase" if op_match.group(1).lower() in ["increase", "raise"] else "decrease"
        
        fee_match = re.search(r"\b(tuition|ballet|chess|transport|lunch|insurance|workbooks)\b", t, re.I)
        if fee_match:
            slots["fee_name"] = _normalize_fee_name(fee_match.group(1))
        
        amount_match = re.search(r"\bby\s+(\d+(?:,\d{3})*)\b", t, re.I)
        if amount_match:
            slots["amount"] = int(amount_match.group(1).replace(',', ''))

    elif intent == "generate_invoices":
        # Extract level for invoice generation
        level_match = re.search(r"\b(PP[12]|Grade\s+\d+|JSS\s+\d+|Senior\s+\d+)\b", t, re.I)
        if level_match:
            slots["level"] = level_match.group(1).title()
        
        # Extract term/year
        term_match = re.search(r"\bterm\s+(\d+)\b", t, re.I)
        if term_match:
            slots["term"] = int(term_match.group(1))
        
        year_match = re.search(r"\b(20\d{2})\b", t)
        if year_match:
            slots["year"] = int(year_match.group(1))

    # ... existing slot extraction for other intents ...
    elif intent == "enroll_student":
        # ... (your existing enroll_student slot extraction)
        pass
    
    # ... other existing intents ...

    return slots

# Required slots for CBC model
REQUIRED_SLOTS = {
    "view_fee_structure": [],  # Optional - can show level selection
    "set_fee_prices": ["price_pairs"],
    "adjust_fee": ["level", "operation", "fee_name", "amount"],
    "generate_invoices": [],  # Can auto-detect structure
    "publish_fee_structure": [],  # Can auto-detect structure
    # ... existing slots ...
    "create_class": ["name", "level", "academic_year"],
    "class_query": ["query_type"],
    "student_query": ["query_type"],
    "class_student_analytics": ["query_type"],
    "enroll_student": ["first_name", "last_name", "gender", ["class_id", "class_name"]],
    "send_notification": ["type", "subject", "body", "target"],
    "school_facts": [],
}

def missing_slots(intent: str, slots: Dict[str, Any]) -> list:
    """Check which required slots are missing for an intent"""
    missing = []
    reqs = REQUIRED_SLOTS.get(intent, [])
    
    print(f"🔍 DEBUG missing_slots: intent={intent}, slots={slots}, required={reqs}")
    
    for r in reqs:
        if isinstance(r, (list, tuple)):
            if not any((k in slots and slots[k]) for k in r):
                missing.append(f"one of: {', '.join(map(str, r))}")
        else:
            if r not in slots or slots[r] in (None, "", []):
                missing.append(r)
                print(f"🔍 DEBUG: Missing slot '{r}' - value: {slots.get(r, 'NOT_FOUND')}")
    
    print(f"🔍 DEBUG: Missing slots result: {missing}")
    return missing