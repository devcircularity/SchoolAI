# app/models/__init__.py - Import all models so SQLAlchemy can discover them

from app.models.base import Base

# Import all model classes
from app.models.user import User
from app.models.school import School, SchoolMember
from app.models.student import Student
from app.models.class_model import Class
from app.models.guardian import Guardian, StudentGuardian
from app.models.academic import AcademicYear, AcademicTerm, Enrollment, EnrollmentStatusEvent
from app.models.fee import FeeStructure, FeeItem
from app.models.payment import Invoice, InvoiceLine, Payment
from app.models.chat import ChatConversation, ChatMessage
from app.models.accounting import GLAccount, JournalEntry, JournalLine
from app.models.cbc_level import CbcLevel
from app.models.notification import Notification

# Import forward references for proper relationship configuration
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

# Export the Base for other modules
__all__ = [
    "Base",
    "User",
    "School", 
    "SchoolMember",
    "Student",
    "Class",
    "Guardian",
    "StudentGuardian", 
    "AcademicYear",
    "AcademicTerm",
    "Enrollment",
    "EnrollmentStatusEvent",
    "FeeStructure",
    "FeeItem", 
    "Invoice",
    "InvoiceLine",
    "Payment",
    "ChatConversation",
    "ChatMessage",
    "GLAccount",
    "JournalEntry", 
    "JournalLine",
    "CbcLevel",
    "Notification",
]