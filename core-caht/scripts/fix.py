#!/usr/bin/env python3
# scripts/fix_patterns.py
# Run from project root: python scripts/fix_patterns.py

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.intent_config import IntentConfigVersion, IntentPattern, PatternKind
from app.core.db import get_db

def check_and_fix_patterns(db: Session):
    """Check for pattern conflicts and fix priorities"""
    
    # Get active version
    active_version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.status == 'active')\
        .first()
    
    if not active_version:
        print("❌ No active configuration version found!")
        return
    
    print(f"Active version: {active_version.name} (ID: {active_version.id})")
    
    # Check for the problematic 'unknown' pattern
    unknown_pattern = db.query(IntentPattern)\
        .filter(
            IntentPattern.version_id == active_version.id,
            IntentPattern.intent == 'unknown'
        )\
        .first()
    
    if unknown_pattern:
        print(f"\n⚠️  Found 'unknown' pattern with priority {unknown_pattern.priority}")
        print(f"   Pattern: {unknown_pattern.pattern}")
        
        # This pattern is too broad - it's matching everything with "what is"
        print("\n   This pattern is too broad and catching everything!")
        print("   Lowering priority to 10 to let specific patterns match first...")
        
        # Lower its priority significantly
        unknown_pattern.priority = 10  # Very low priority
        print(f"   → Lowered priority to 10")
    
    # Check for student_count pattern
    student_count_pattern = db.query(IntentPattern)\
        .filter(
            IntentPattern.version_id == active_version.id,
            IntentPattern.intent == 'student_count'
        )\
        .first()
    
    if not student_count_pattern:
        print("\n❌ Missing student_count pattern! Creating it...")
        
        pattern = IntentPattern(
            version_id=active_version.id,
            handler='student',
            intent='student_count',
            kind=PatternKind.POSITIVE,
            pattern=r'student.*count|how many.*student|total.*student|number of student|count.*student',
            priority=180,  # Higher priority
            enabled=True
        )
        db.add(pattern)
        print("✓ Created student_count pattern with priority 180")
    else:
        print(f"\n✓ student_count pattern exists with priority {student_count_pattern.priority}")
        print(f"   Pattern: {student_count_pattern.pattern}")
        
        # Make sure it has high enough priority
        if student_count_pattern.priority < 170:
            old_priority = student_count_pattern.priority
            student_count_pattern.priority = 180
            print(f"   → Increased priority from {old_priority} to 180")
        
        # Fix the pattern to be more inclusive
        better_pattern = r'student.*count|how many.*student|total.*student|number of student|count.*student'
        if student_count_pattern.pattern != better_pattern:
            print(f"   → Updating pattern to be more inclusive...")
            student_count_pattern.pattern = better_pattern
            print(f"   → New pattern: {better_pattern}")
    
    # Check for school_overview pattern
    school_overview_pattern = db.query(IntentPattern)\
        .filter(
            IntentPattern.version_id == active_version.id,
            IntentPattern.intent == 'school_overview'
        )\
        .first()
    
    if school_overview_pattern:
        # Add pattern for "what is the name of our school"
        current_pattern = school_overview_pattern.pattern
        if 'school.*name|name.*school' not in current_pattern:
            new_pattern = current_pattern + '|school.*name|name.*school|what.*name.*school'
            school_overview_pattern.pattern = new_pattern
            school_overview_pattern.priority = max(school_overview_pattern.priority, 170)
            print(f"\n✓ Updated school_overview pattern to include school name queries")
            print(f"   New pattern includes: school.*name|name.*school|what.*name.*school")
    
    # List all patterns with priority >= 100 to see potential conflicts
    print("\n📋 All patterns with priority >= 100:")
    high_priority_patterns = db.query(IntentPattern)\
        .filter(
            IntentPattern.version_id == active_version.id,
            IntentPattern.kind == PatternKind.POSITIVE,
            IntentPattern.enabled == True,
            IntentPattern.priority >= 100
        )\
        .order_by(IntentPattern.priority.desc())\
        .all()
    
    for p in high_priority_patterns:
        # Show first 60 chars of pattern
        pattern_preview = p.pattern[:60] + "..." if len(p.pattern) > 60 else p.pattern
        print(f"   [{p.priority:3d}] {p.intent:25s}: {pattern_preview}")
    
    # Commit changes
    try:
        db.commit()
        print("\n✅ All changes committed to database")
        print("\n🔄 Please restart your application or reload the ConfigRouter to apply changes")
        return True
    except Exception as e:
        print(f"\n❌ Error committing changes: {e}")
        db.rollback()
        return False

def test_patterns_after_fix(db: Session):
    """Test if patterns work correctly after fixes"""
    print("\n" + "="*60)
    print("Testing patterns after fixes...")
    print("="*60)
    
    from app.services.config_router import ConfigRouter
    
    # Create router and reload config
    router = ConfigRouter(db)
    router.reload_config()
    
    # Test queries
    test_queries = [
        "how many students do we have?",
        "what is the name of our school?",
        "show all students",
        "what is this?",
    ]
    
    for query in test_queries:
        result = router.route(query)
        if result:
            print(f"\n✓ '{query}'")
            print(f"  → Intent: {result.intent} (confidence: {result.confidence:.3f})")
        else:
            print(f"\n✗ '{query}'")
            print(f"  → No match found")

def main():
    print("🔧 Pattern Fix Script")
    print("="*60)
    
    # Get database session
    try:
        db = next(get_db())
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return
    
    try:
        # Fix patterns
        success = check_and_fix_patterns(db)
        
        if success:
            # Test after fixing
            test_patterns_after_fix(db)
    
    finally:
        db.close()

if __name__ == "__main__":
    main()