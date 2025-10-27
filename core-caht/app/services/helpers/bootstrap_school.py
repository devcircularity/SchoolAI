# app/services/helpers/bootstrap_school.py - Modified to skip fee structure creation
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.models.school import School
import uuid

# Bands → Grades (CBC)
CBC_GROUPS = {
    "Early Years Education (EYE)": ["PP1", "PP2"],
    "Lower Primary": ["Grade 1", "Grade 2", "Grade 3"],
    "Upper Primary": ["Grade 4", "Grade 5", "Grade 6"],
    "Junior Secondary (JSS)": ["Grade 7", "Grade 8", "Grade 9"],
    "Senior Secondary": ["Grade 10", "Grade 11", "Grade 12"],
}

TERMS = [
    {"term": 1, "name": "Term 1", "start_month": 1, "end_month": 4},
    {"term": 2, "name": "Term 2", "start_month": 5, "end_month": 8},
    {"term": 3, "name": "Term 3", "start_month": 9, "end_month": 11},
]

# SIMPLIFIED: Only 3 common co-curricular activities
COCURRICULAR = [
    "Sports & Games",
    "Music & Drama", 
    "Computer Club",
]

OTHER_CHARGES = [
    # (name, billing_cycle, is_optional)
    ("Application", "ONE_OFF", False),
    ("Registration", "ONE_OFF", False),
    ("Caution", "ONE_OFF", False),
    ("Annual Student Accident Insurance Cover", "ANNUAL", False),
    ("Sports T-Shirt", "ONE_OFF", True),
    ("Workbooks", "ANNUAL", False),
]

def bootstrap_school(*, db: Session, school_id: str, created_by: str):
    """
    Bootstrap school with academic structure but no fee structures.
    Fee structures are created dynamically when classes are created for each grade.
    """
    # Get the school's academic year start date
    school = db.get(School, school_id)
    if not school or not school.academic_year_start:
        # Fallback to current year if no academic year start is set
        academic_year = date.today().year
        year_start_date = date(academic_year, 1, 1)
        year_end_date = date(academic_year, 12, 31)
    else:
        # Use the school's academic year start date
        year_start_date = school.academic_year_start
        academic_year = year_start_date.year
        # Academic year typically runs for 12 months from start date
        year_end_date = date(academic_year + 1, year_start_date.month - 1, 28) if year_start_date.month > 1 else date(academic_year, 12, 31)
    
    # 1) Create academic year and terms based on school's academic calendar
    academic_year_id = _create_academic_year_and_terms(db, school_id, academic_year, year_start_date, year_end_date)
    
    # 2) CBC levels with group names - these are just templates
    _create_cbc_levels(db, school_id)
    
    # 3) Minimal GL chart
    _create_gl_accounts(db, school_id)
    
    # 4) SKIP fee structure creation - they'll be created when classes are made
    
    db.commit()


def _create_academic_year_and_terms(db: Session, school_id: str, year: int, year_start: date, year_end: date) -> str:
    """Create academic year and its 3 terms based on school's academic calendar"""
    
    now = datetime.utcnow()
    
    # Generate UUID in Python, not in SQL
    academic_year_uuid = str(uuid.uuid4())
    
    # Create academic year with proper UUID handling
    db.execute(text("""
        INSERT INTO academic_years (id, school_id, year, title, state, start_date, end_date, created_at, updated_at)
        VALUES (:academic_year_id, :school_id, :year, :title, 'DRAFT', :start_date, :end_date, :created_at, :updated_at)
    """), {
        "academic_year_id": academic_year_uuid,
        "school_id": school_id,
        "year": year,
        "title": f"Academic Year {year}",
        "start_date": year_start,
        "end_date": year_end,
        "created_at": now,
        "updated_at": now
    })
    
    # Create 3 terms based on academic year start
    for term_info in TERMS:
        # Calculate term start/end based on the academic year start
        if year_start.month <= 6:  # Academic year starts in first half of year
            term_start_month = ((term_info["start_month"] - 1) + year_start.month - 1) % 12 + 1
            term_end_month = ((term_info["end_month"] - 1) + year_start.month - 1) % 12 + 1
            term_year = year if term_start_month >= year_start.month else year + 1
        else:  # Academic year starts in second half of year
            term_start_month = ((term_info["start_month"] - 1) + year_start.month - 1) % 12 + 1
            term_end_month = ((term_info["end_month"] - 1) + year_start.month - 1) % 12 + 1
            term_year = year + 1 if term_start_month < year_start.month else year
        
        # Ensure months are valid (1-12)
        if term_start_month > 12:
            term_start_month -= 12
            term_year += 1
        if term_end_month > 12:
            term_end_month -= 12
        
        term_start_date = date(term_year, term_start_month, 1)
        term_end_date = date(term_year, term_end_month, 28)  # Simplified end dates
        
        # Generate UUID in Python for term as well
        term_uuid = str(uuid.uuid4())
        
        db.execute(text("""
            INSERT INTO academic_terms (id, school_id, year_id, term, title, state, start_date, end_date, created_at, updated_at)
            VALUES (:term_id, :school_id, :year_id, :term, :title, 'PLANNED', :start_date, :end_date, :created_at, :updated_at)
        """), {
            "term_id": term_uuid,
            "school_id": school_id,
            "year_id": academic_year_uuid,
            "term": term_info["term"],
            "title": term_info["name"],
            "start_date": term_start_date,
            "end_date": term_end_date,
            "created_at": now,
            "updated_at": now
        })
    
    return academic_year_uuid


def _create_cbc_levels(db: Session, school_id: str):
    """Create CBC level records - these are just grade templates"""
    for group_name, grades in CBC_GROUPS.items():
        for label in grades:
            # Generate UUID in Python
            cbc_level_uuid = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO cbc_level (id, school_id, label, group_name)
                VALUES (:id, :school_id, :label, :group_name)
            """), {
                "id": cbc_level_uuid,
                "school_id": school_id, 
                "label": label, 
                "group_name": group_name
            })


def _create_gl_accounts(db: Session, school_id: str):
    """Create basic GL chart of accounts"""
    gl_accounts = [
        ("1000", "Cash & Bank", "ASSET"),
        ("1100", "Accounts Receivable (Students)", "ASSET"),
        ("2000", "Unearned Revenue", "LIABILITY"),
        ("4000", "Tuition Fees", "INCOME"),
        ("4010", "Activity Fees", "INCOME"),
        ("4020", "Lunch", "INCOME"),
        ("4030", "Transport", "INCOME"),
        ("5000", "Stationery", "EXPENSE"),
        ("5010", "Utilities", "EXPENSE"),
        ("5020", "Salaries", "EXPENSE"),
    ]
    
    for code, name, account_type in gl_accounts:
        # Generate UUID in Python
        gl_account_uuid = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO gl_accounts (id, school_id, code, name, type)
            VALUES (:id, :school_id, :code, :name, :type)
        """), {
            "id": gl_account_uuid,
            "school_id": school_id, 
            "code": code, 
            "name": name, 
            "type": account_type
        })


# NEW: Helper functions for creating fee structures when classes are created

def create_fee_structures_for_grade(db: Session, school_id: str, grade_label: str, academic_year: int = None) -> list:
    """
    Create fee structures for a grade when the first class is created for that grade.
    Returns list of created fee structure IDs.
    """
    
    # Get current academic year if not provided
    if academic_year is None:
        result = db.execute(text("""
            SELECT year FROM academic_years 
            WHERE school_id = :school_id 
            ORDER BY year DESC LIMIT 1
        """), {"school_id": school_id}).fetchone()
        
        academic_year = result[0] if result else datetime.now().year
    
    # Check if fee structures already exist for this grade
    existing = db.execute(text("""
        SELECT id FROM fee_structures 
        WHERE school_id = :school_id AND level = :level AND year = :year
    """), {
        "school_id": school_id,
        "level": grade_label,
        "year": academic_year
    }).fetchall()
    
    if existing:
        return [str(row[0]) for row in existing]
    
    created_structures = []
    now = datetime.utcnow()
    
    # Check if this is the first fee structure for the school
    first_structure_check = db.execute(text("""
        SELECT COUNT(*) FROM fee_structures WHERE school_id = :school_id
    """), {"school_id": school_id}).fetchone()
    
    is_first_structure = first_structure_check[0] == 0
    
    # Create fee structures for all 3 terms
    for term_info in TERMS:
        fs_uuid = str(uuid.uuid4())
        
        db.execute(text("""
            INSERT INTO fee_structures (id, school_id, name, level, term, year, is_default, is_published, created_at, updated_at)
            VALUES (:id, :school_id, :name, :level, :term, :year, :is_default, false, :created_at, :updated_at)
        """), {
            "id": fs_uuid,
            "school_id": school_id,
            "name": f"{grade_label} — {term_info['name']} {academic_year}",
            "level": grade_label,
            "term": term_info["term"],
            "year": academic_year,
            "is_default": is_first_structure and term_info["term"] == 1,  # Only first structure is default
            "created_at": now,
            "updated_at": now,
        })
        
        # Create fee items for this structure
        create_fee_items_for_structure(db, school_id, fs_uuid)
        created_structures.append(fs_uuid)
    
    return created_structures


def create_fee_items_for_structure(db: Session, school_id: str, fee_structure_id: str):
    """Create fee items for a fee structure with zero amounts"""
    
    now = datetime.utcnow()
    
    # Tuition (required, per term) - Default amount of 0, to be set later
    tuition_uuid = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO fee_items (id, school_id, fee_structure_id, class_id, item_name, amount, is_optional, category, billing_cycle, created_at, updated_at)
        VALUES (:id, :school_id, :fee_structure_id, NULL, 'Tuition', 0, false, 'TUITION', 'TERM', :created_at, :updated_at)
    """), {
        "id": tuition_uuid,
        "school_id": school_id, 
        "fee_structure_id": fee_structure_id,
        "created_at": now,
        "updated_at": now,
    })
    
    # Co-curricular activities (optional, per term) - Default amount of 0
    for activity in COCURRICULAR:
        activity_uuid = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO fee_items (id, school_id, fee_structure_id, class_id, item_name, amount, is_optional, category, billing_cycle, created_at, updated_at)
            VALUES (:id, :school_id, :fee_structure_id, NULL, :item_name, 0, true, 'COCURRICULAR', 'TERM', :created_at, :updated_at)
        """), {
            "id": activity_uuid,
            "school_id": school_id, 
            "fee_structure_id": fee_structure_id,
            "item_name": activity,
            "created_at": now,
            "updated_at": now,
        })
    
    # Other charges (mix of billing cycles and optionality) - Default amount of 0
    for item_name, billing_cycle, is_optional in OTHER_CHARGES:
        other_uuid = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO fee_items (id, school_id, fee_structure_id, class_id, item_name, amount, is_optional, category, billing_cycle, created_at, updated_at)
            VALUES (:id, :school_id, :fee_structure_id, NULL, :item_name, 0, :is_optional, 'OTHER', :billing_cycle, :created_at, :updated_at)
        """), {
            "id": other_uuid,
            "school_id": school_id, 
            "fee_structure_id": fee_structure_id,
            "item_name": item_name,
            "is_optional": is_optional,
            "billing_cycle": billing_cycle,
            "created_at": now,
            "updated_at": now,
        })