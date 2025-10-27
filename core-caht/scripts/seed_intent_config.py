# scripts/seed_intent_config.py - COMPLETE VERSION WITH ALL PATTERNS
"""
Seed the intent configuration with initial patterns extracted from ALL existing handlers
Run this after running the migration to populate the system
"""
import sys
import os
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.intent_config import (
    IntentConfigVersion, IntentPattern, PromptTemplate, 
    ConfigStatus, PatternKind, TemplateType
)
from app.core.config import settings


def create_initial_config(db_session):
    """Create initial configuration version with patterns from existing handlers"""
    
    # Create initial version
    initial_version = IntentConfigVersion(
        id=str(uuid.uuid4()),
        name="Complete Configuration v1.0 - All Handlers",
        status=ConfigStatus.ACTIVE,
        notes="Migrated patterns from all existing hardcoded handlers: student, payment, invoice, overview, general",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        activated_at=datetime.utcnow()
    )
    
    db_session.add(initial_version)
    db_session.flush()  # Get the ID
    
    # Student handler patterns (from STUDENT_COMMANDS)
    student_patterns = [
        {
            "handler": "student",
            "intent": "student_create",
            "kind": PatternKind.POSITIVE,
            "pattern": r"create.*student|add.*student|new.*student",
            "priority": 200
        },
        {
            "handler": "student", 
            "intent": "unassigned_students",
            "kind": PatternKind.POSITIVE,
            "pattern": r"unassigned.*students|without.*class|students.*without.*class",
            "priority": 180
        },
        {
            "handler": "student",
            "intent": "student_search", 
            "kind": PatternKind.POSITIVE,
            "pattern": r"find.*student|search.*student|show.*student.*\d+|admission.*number.*\d+",
            "priority": 170
        },
        {
            "handler": "student",
            "intent": "student_list",
            "kind": PatternKind.POSITIVE, 
            "pattern": r"list.*students|all.*students|show.*students",
            "priority": 160
        },
        {
            "handler": "student",
            "intent": "student_count",
            "kind": PatternKind.POSITIVE,
            "pattern": r"student.*count|how many.*students|total.*students",
            "priority": 150
        },
        {
            "handler": "student",
            "intent": "student_details",
            "kind": PatternKind.POSITIVE,
            "pattern": r"student.*details|get.*student|student.*information",
            "priority": 140
        },
        
        # Student negative patterns (exclusions)
        {
            "handler": "student",
            "intent": "exclude_assignment",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"add.*to.*|assign.*to.*|put.*in.*|move.*to.*|place.*in.*",
            "priority": 300
        },
        {
            "handler": "student", 
            "intent": "exclude_enrollment",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"enroll|assign.*class|student.*enrollment",
            "priority": 290
        },
        
        # Student synonyms
        {
            "handler": "student",
            "intent": "learner",
            "kind": PatternKind.SYNONYM,
            "pattern": r"\bpupil\b|\blearner\b",
            "priority": 100
        },
        {
            "handler": "student",
            "intent": "student",
            "kind": PatternKind.SYNONYM,
            "pattern": r"\bkid\b|\bchild\b|\bstudents\b",
            "priority": 100
        }
    ]
    
    # Payment handler patterns (from PAYMENT_COMMANDS)
    payment_patterns = [
        {
            "handler": "payment",
            "intent": "payment_record",
            "kind": PatternKind.POSITIVE,
            "pattern": r"record.*payment|process.*payment|payment.*received|mpesa.*payment",
            "priority": 200
        },
        {
            "handler": "payment", 
            "intent": "payment_summary",
            "kind": PatternKind.POSITIVE,
            "pattern": r"payment.*summary|total.*payment|payment.*collected|payments.*today",
            "priority": 180
        },
        {
            "handler": "payment",
            "intent": "payment_history", 
            "kind": PatternKind.POSITIVE,
            "pattern": r"payment.*history|payment.*for.*student|student.*payments|payment.*details",
            "priority": 170
        },
        {
            "handler": "payment",
            "intent": "payment_pending",
            "kind": PatternKind.POSITIVE,
            "pattern": r"pending.*payment|outstanding.*payment|unpaid|overdue.*fees",
            "priority": 160
        },
        {
            "handler": "payment",
            "intent": "payment_status",
            "kind": PatternKind.POSITIVE,
            "pattern": r"payment.*status|fees.*paid|account.*balance|payment.*check",
            "priority": 150
        },
        
        # Payment synonyms
        {
            "handler": "payment",
            "intent": "fees",
            "kind": PatternKind.SYNONYM,
            "pattern": r"\btuition\b|\bschool.*fees\b",
            "priority": 100
        },
        {
            "handler": "payment",
            "intent": "mpesa",
            "kind": PatternKind.SYNONYM,
            "pattern": r"\bm-pesa\b|\bmobile.*money\b|\bpaybill\b",
            "priority": 100
        }
    ]
    
    # Invoice handler patterns (from INVOICE_COMMANDS)
    invoice_patterns = [
        {
            "handler": "invoice",
            "intent": "invoice_generate_student",
            "kind": PatternKind.POSITIVE,
            "pattern": r"generate.*invoice.*for.*student|create.*invoice.*for.*student|invoice.*for.*student",
            "priority": 200
        },
        {
            "handler": "invoice",
            "intent": "invoice_generate_bulk",
            "kind": PatternKind.POSITIVE,
            "pattern": r"generate.*invoice.*all|generate.*all.*invoice|create.*invoice.*all|bulk.*invoice",
            "priority": 190
        },
        {
            "handler": "invoice",
            "intent": "invoice_pending",
            "kind": PatternKind.POSITIVE,
            "pattern": r"pending.*invoice|outstanding.*invoice|unpaid.*invoice|overdue.*invoice",
            "priority": 180
        },
        {
            "handler": "invoice",
            "intent": "invoice_show_student",
            "kind": PatternKind.POSITIVE,
            "pattern": r"show.*invoice.*for|invoice.*details.*for|student.*invoice",
            "priority": 170
        },
        {
            "handler": "invoice",
            "intent": "invoice_list",
            "kind": PatternKind.POSITIVE,
            "pattern": r"list.*invoices|show.*invoices|all.*invoices",
            "priority": 160
        },
        {
            "handler": "invoice",
            "intent": "invoice_overview",
            "kind": PatternKind.POSITIVE,
            "pattern": r"invoice.*overview|invoice.*summary|invoice.*status",
            "priority": 150
        },
        
        # Invoice synonyms
        {
            "handler": "invoice",
            "intent": "invoice",
            "kind": PatternKind.SYNONYM,
            "pattern": r"\bbill\b|\bbilling\b",
            "priority": 100
        }
    ]
    
    # Overview handler patterns (from OVERVIEW_COMMANDS)
    overview_patterns = [
        {
            "handler": "overview",
            "intent": "school_overview",
            "kind": PatternKind.POSITIVE,
            "pattern": r"school.*overview|school.*summary|school.*stats|dashboard|overall.*numbers|school.*performance",
            "priority": 160
        },
        {
            "handler": "overview",
            "intent": "dashboard",
            "kind": PatternKind.POSITIVE,
            "pattern": r"dashboard|show.*dashboard|main.*screen",
            "priority": 150
        },
        {
            "handler": "overview",
            "intent": "school_summary",
            "kind": PatternKind.POSITIVE,
            "pattern": r"school.*summary|summary|status.*report",
            "priority": 140
        }
    ]
    
    # General handler patterns (from GENERAL_COMMANDS) 
    general_patterns = [
        # Greeting patterns
        {
            "handler": "general",
            "intent": "greeting",
            "kind": PatternKind.POSITIVE,
            "pattern": r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening)$",
            "priority": 150
        },
        {
            "handler": "general",
            "intent": "casual_conversation",
            "kind": PatternKind.POSITIVE,
            "pattern": r"^(how are you|how's it going|what's going on|how do you do|nice to meet you)(\?)?$",
            "priority": 140
        },
        
        # School registration patterns
        {
            "handler": "general",
            "intent": "school_registration",
            "kind": PatternKind.POSITIVE,
            "pattern": r"register.*school|school.*register|school.*information|school.*details|school.*data",
            "priority": 180
        },
        
        # Getting started patterns
        {
            "handler": "general",
            "intent": "getting_started",
            "kind": PatternKind.POSITIVE,
            "pattern": r"get.*started|getting.*started|where.*start|first.*steps|how.*begin|setup.*guide",
            "priority": 170
        },
        
        # System capabilities patterns
        {
            "handler": "general",
            "intent": "system_capabilities",
            "kind": PatternKind.POSITIVE,
            "pattern": r"what.*can.*you.*do|what.*can.*i.*do|capabilities|features|what.*this.*system",
            "priority": 160
        },
        
        # Help patterns
        {
            "handler": "general",
            "intent": "help",
            "kind": PatternKind.POSITIVE,
            "pattern": r"^help$|^guide$|^assistance$|help.*me|need.*help|confused|not.*sure.*how",
            "priority": 150
        },
        
        # Next steps patterns
        {
            "handler": "general",
            "intent": "next_steps",
            "kind": PatternKind.POSITIVE,
            "pattern": r"what.*should.*do|what.*next|what.*supposed.*do|what.*do.*now|where.*go.*from.*here",
            "priority": 140
        },
        
        # School management patterns
        {
            "handler": "general",
            "intent": "school_management",
            "kind": PatternKind.POSITIVE,
            "pattern": r"manage.*school|run.*school|school.*management",
            "priority": 130
        },
        
        # System introduction patterns
        {
            "handler": "general",
            "intent": "system_introduction",
            "kind": PatternKind.POSITIVE,
            "pattern": r"^(who are you|what are you|introduce yourself|tell me about yourself)(\?)?$",
            "priority": 120
        },
        
        # General catch-all for unknown queries
        {
            "handler": "general",
            "intent": "unknown",
            "kind": PatternKind.POSITIVE,
            "pattern": r"what.*is|explain|tell.*me.*about",
            "priority": 100
        }
    ]
    
    # Class handler patterns (from CLASS_COMMANDS)
    class_patterns = [
        {
            "handler": "class",
            "intent": "class_create",
            "kind": PatternKind.POSITIVE,
            "pattern": r"create.*class|add.*class|new.*class|make.*class|setup.*class",
            "priority": 180
        },
        {
            "handler": "class",
            "intent": "grade_create",
            "kind": PatternKind.POSITIVE,
            "pattern": r"create.*grade|add.*grade|new.*grade",
            "priority": 170
        },
        {
            "handler": "class",
            "intent": "class_details",
            "kind": PatternKind.POSITIVE,
            "pattern": r"show.*class.*detail|class.*detail|details.*class|view.*class.*info|info.*class",
            "priority": 160
        },
        {
            "handler": "class",
            "intent": "grade_list",
            "kind": PatternKind.POSITIVE,
            "pattern": r"^grades?$|list.*grade|show.*grade",
            "priority": 150
        },
        {
            "handler": "class",
            "intent": "class_list",
            "kind": PatternKind.POSITIVE,
            "pattern": r"list.*class|all.*class|show.*class|^classes$",
            "priority": 160
        },
        {
            "handler": "class",
            "intent": "class_count",
            "kind": PatternKind.POSITIVE,
            "pattern": r"class.*count|how many.*class|total.*class",
            "priority": 140
        },
        {
            "handler": "class",
            "intent": "class_empty",
            "kind": PatternKind.POSITIVE,
            "pattern": r"empty.*class|class.*without.*student",
            "priority": 130
        },
        
        # Class negative patterns (exclusions)
        {
            "handler": "class",
            "intent": "exclude_assignment",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"add.*student.*to.*|assign.*student.*to.*|put.*student.*in.*|move.*student.*to.*|place.*student.*in.*",
            "priority": 300
        },
        {
            "handler": "class",
            "intent": "exclude_enrollment",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"enroll|assign.*class.*to.*student|student.*enrollment|with.*admission.*no.*to",
            "priority": 290
        }
    ]
    
    # Enrollment patterns (from ENROLLMENT_COMMANDS)
    enrollment_patterns = [
        {
            "handler": "enrollment",
            "intent": "enrollment_single",
            "kind": PatternKind.POSITIVE,
            "pattern": r"enroll.*student.*\d+|enroll.*student.*[a-zA-Z]|student.*\d+.*enroll|enroll.*specific.*student",
            "priority": 180
        },
        {
            "handler": "enrollment",
            "intent": "enrollment_bulk", 
            "kind": PatternKind.POSITIVE,
            "pattern": r"enroll.*all.*student|bulk.*enroll|enroll.*ready.*student|mass.*enroll",
            "priority": 170
        },
        {
            "handler": "enrollment",
            "intent": "enrollment_status",
            "kind": PatternKind.POSITIVE,
            "pattern": r"enrollment.*status|enrollment.*statistic|show.*enrollment|enrollment.*overview",
            "priority": 160
        },
        {
            "handler": "enrollment",
            "intent": "enrollment_list",
            "kind": PatternKind.POSITIVE,
            "pattern": r"list.*enrollment|who.*enrolled|students.*enrolled",
            "priority": 150
        },
        
        # Enrollment negative patterns (exclusions)
        {
            "handler": "enrollment",
            "intent": "exclude_student_creation",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"create.*student|add.*student|new.*student",
            "priority": 300
        },
        {
            "handler": "enrollment",
            "intent": "exclude_student_listing",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"list.*student|show.*student.*detail",
            "priority": 290
        },
        {
            "handler": "enrollment",
            "intent": "exclude_fee_invoice",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"invoice.*enroll|fee.*enroll",
            "priority": 280
        }
    ]
    
    # Fees patterns (separate from payment for fee structure queries) - from FEE_COMMANDS
    fees_patterns = [
        {
            "handler": "fee",
            "intent": "fee_structure",
            "kind": PatternKind.POSITIVE,
            "pattern": r"show.*fee.*structure|list.*fee.*structure|fee.*structure",
            "priority": 180
        },
        {
            "handler": "fee",
            "intent": "fee_overview",
            "kind": PatternKind.POSITIVE,
            "pattern": r"fees.*overview|fee.*summary",
            "priority": 170
        },
        {
            "handler": "fee",
            "intent": "fee_grade_specific",
            "kind": PatternKind.POSITIVE,
            "pattern": r"fees.*for.*grade|fees.*for.*class|grade.*fees|class.*fees",
            "priority": 160
        },
        {
            "handler": "fee",
            "intent": "fee_update",
            "kind": PatternKind.POSITIVE,
            "pattern": r"update.*fee|set.*fee|change.*fee|modify.*fee|set.*tuition|update.*tuition|set.*amount",
            "priority": 190
        },
        {
            "handler": "fee",
            "intent": "fee_items",
            "kind": PatternKind.POSITIVE,
            "pattern": r"fee.*item|show.*fee.*item|list.*fee.*item",
            "priority": 150
        },
        {
            "handler": "fee",
            "intent": "fee_student_invoice",
            "kind": PatternKind.POSITIVE,
            "pattern": r"show.*invoice.*for|student.*invoice|invoice.*for.*student",
            "priority": 140
        },
        
        # Fee synonyms
        {
            "handler": "fee",
            "intent": "tuition",
            "kind": PatternKind.SYNONYM,
            "pattern": r"\btuition\b|\bcost\b|\bprice\b",
            "priority": 100
        }
    ]
    
    # Academic patterns (from ACADEMIC_COMMANDS)
    academic_patterns = [
        {
            "handler": "academic",
            "intent": "academic_current_term",
            "kind": PatternKind.POSITIVE,
            "pattern": r"current.*term|active.*term",
            "priority": 160
        },
        {
            "handler": "academic",
            "intent": "academic_activate_term",
            "kind": PatternKind.POSITIVE,
            "pattern": r"activate.*term|set.*active.*term|make.*term.*active",
            "priority": 170
        },
        {
            "handler": "academic",
            "intent": "academic_calendar",
            "kind": PatternKind.POSITIVE,
            "pattern": r"academic.*calendar|all.*terms|show.*terms|list.*terms|terms.*overview",
            "priority": 150
        },
        {
            "handler": "academic",
            "intent": "academic_setup",
            "kind": PatternKind.POSITIVE,
            "pattern": r"academic.*setup|academic.*status|setup.*status",
            "priority": 140
        },
        {
            "handler": "academic",
            "intent": "academic_overview",
            "kind": PatternKind.POSITIVE,
            "pattern": r"academic.*year|term.*overview|academic.*overview",
            "priority": 130
        },
        
        # Academic negative patterns (exclusions)
        {
            "handler": "academic",
            "intent": "exclude_enrollment",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"enroll.*student.*\d+|enroll.*\d+.*in.*term|bulk.*enroll",
            "priority": 300
        },
        {
            "handler": "academic",
            "intent": "exclude_assignment",
            "kind": PatternKind.NEGATIVE,
            "pattern": r"assign.*to|add.*to|put.*in|enrollment|in.*current.*term",
            "priority": 290
        }
    ]
    
    # Combine all patterns
    all_patterns = (student_patterns + payment_patterns + invoice_patterns + 
                   overview_patterns + general_patterns + class_patterns + 
                   enrollment_patterns + fees_patterns + academic_patterns)
    
    # Create pattern records
    for pattern_data in all_patterns:
        pattern = IntentPattern(
            id=str(uuid.uuid4()),
            version_id=initial_version.id,
            handler=pattern_data["handler"],
            intent=pattern_data["intent"],
            kind=pattern_data["kind"],
            pattern=pattern_data["pattern"],
            priority=pattern_data["priority"],
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(pattern)
    
    # Create initial prompt templates
    prompt_templates = [
        # LLM Classifier system prompt
        {
            "handler": "classifier",
            "intent": None,
            "template_type": TemplateType.SYSTEM,
            "template_text": """You are an intent classifier for a school management assistant. 
Your job is to classify user messages into specific intents and extract relevant entities.

CRITICAL RULES:
1. Only return valid JSON - no explanations or extra text
2. Choose exactly one intent from the provided allowed list
3. Confidence must be between 0.0 and 1.0
4. Extract entities according to the provided schema
5. Include up to 3 alternative intents with their confidence scores
6. If unsure, be conservative with confidence scores

Response format:
{
  "intent": "selected_intent_name",
  "confidence": 0.75,
  "entities": {"field_name": "extracted_value"},
  "alternatives": [{"intent": "alt_intent", "confidence": 0.45}]
}"""
        },
        
        # Fallback responder system prompt
        {
            "handler": "fallback",
            "intent": None,
            "template_type": TemplateType.SYSTEM,
            "template_text": """You are a helpful school management assistant.
Answer questions about school operations, student management, and educational topics.
Be concise, helpful, and professional.
If you don't know something specific about the school, suggest how the user can find the information."""
        },
        
        # Handler-specific context prompts
        {
            "handler": "student",
            "intent": "student_search",
            "template_type": TemplateType.FALLBACK_CONTEXT,
            "template_text": "I can help you find students by admission number or name. Please provide either an admission number (e.g., '4444') or student name (e.g., 'Mary Kimani')."
        },
        {
            "handler": "payment",
            "intent": "payment_record",
            "template_type": TemplateType.FALLBACK_CONTEXT,
            "template_text": "I can help you record a payment. Please provide the student details and payment information."
        },
        {
            "handler": "general",
            "intent": "help",
            "template_type": TemplateType.FALLBACK_CONTEXT,
            "template_text": "I'm here to help you manage your school. I can assist with students, classes, enrollments, payments, and academic planning."
        }
    ]
    
    # Create prompt template records
    for template_data in prompt_templates:
        template = PromptTemplate(
            id=str(uuid.uuid4()),
            version_id=initial_version.id,
            handler=template_data["handler"],
            intent=template_data["intent"],
            template_type=template_data["template_type"],
            template_text=template_data["template_text"],
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(template)
    
    db_session.commit()
    print(f"Created initial configuration '{initial_version.name}' with {len(all_patterns)} patterns and {len(prompt_templates)} templates")
    print(f"\nPatterns breakdown:")
    print(f"  - Student: {len(student_patterns)} patterns")
    print(f"  - Payment: {len(payment_patterns)} patterns")
    print(f"  - Invoice: {len(invoice_patterns)} patterns")
    print(f"  - Overview: {len(overview_patterns)} patterns")
    print(f"  - General: {len(general_patterns)} patterns")
    print(f"  - Class: {len(class_patterns)} patterns") 
    print(f"  - Enrollment: {len(enrollment_patterns)} patterns")
    print(f"  - Fees: {len(fees_patterns)} patterns")
    print(f"  - Academic: {len(academic_patterns)} patterns")
    return initial_version.id


def main():
    """Run the seeding process"""
    # Create database connection - handle different settings configurations
    try:
        # Try different ways settings might expose the database URL
        if hasattr(settings, 'DATABASE_URL'):
            db_url = settings.DATABASE_URL
        elif hasattr(settings, 'database_url'):
            db_url = settings.database_url
        elif hasattr(settings, 'db_url'):
            db_url = settings.db_url
        else:
            # Fallback to environment variable
            import os
            db_url = os.getenv('DATABASE_URL')
            
        if not db_url:
            raise ValueError("No database URL found in settings or environment")
            
        print(f"Using database URL: {db_url.replace(db_url.split('@')[0].split('://')[-1], '***') if '@' in db_url else db_url}")
        
    except Exception as e:
        print(f"Error getting database URL: {e}")
        # Fallback to environment variable
        import os
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("Please set DATABASE_URL environment variable")
            return
    
    # Create database connection
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # Check if we already have an active config
        existing = db.query(IntentConfigVersion).filter(
            IntentConfigVersion.status == ConfigStatus.ACTIVE
        ).first()
        
        if existing:
            print(f"Active configuration already exists: {existing.name}")
            print("Skipping seed. Use admin API to create new versions.")
            print("\nTo reset and re-seed:")
            print("1. Update existing config status to 'archived':")
            print(f"   UPDATE intent_config_versions SET status = 'archived' WHERE id = '{existing.id}';")
            print("2. Re-run this script")
            return
        
        # Create initial config
        version_id = create_initial_config(db)
        print(f"\n✅ Successfully created initial configuration: {version_id}")
        print("\nNext steps:")
        print("1. Test student patterns: 'create new student'")
        print("2. Test payment patterns: 'record payment for student 4444'") 
        print("3. Test invoice patterns: 'generate invoice for student'")
        print("4. Test overview patterns: 'school overview'")
        print("5. Test general patterns: 'what can you do'")
        print("6. Review logs at /admin/intent-config/logs")
        print("7. Create candidate versions for improvements")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding configuration: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()