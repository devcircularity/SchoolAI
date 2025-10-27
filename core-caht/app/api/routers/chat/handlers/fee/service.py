# handlers/fee/service.py
from ...base import ChatResponse
from .repo import FeeRepo
from .views import FeeViews
from .dataclasses import (
    row_to_current_term, row_to_fee_stats, row_to_fee_structure, 
    row_to_fee_item, row_to_category_summary, row_to_student_invoice,
    row_to_line_item, row_to_payment
)

class FeeService:
    """Business logic layer for fee operations"""
    
    def __init__(self, db, school_id, get_school_name):
        self.repo = FeeRepo(db, school_id)
        self.views = FeeViews(get_school_name)
    
    def show_system_overview(self):
        """Show fee system overview with current term context"""
        try:
            # Get current term
            current_term_rows = self.repo.get_current_term()
            current_term = row_to_current_term(current_term_rows[0]) if current_term_rows else None
            
            # Get system stats with term filter
            if current_term:
                stats_rows = self.repo.get_system_stats(current_term.term_number, current_term.year)
            else:
                stats_rows = self.repo.get_system_stats()
            
            stats = row_to_fee_stats(stats_rows[0]) if stats_rows else None
            
            # Get recent updates
            recent_updates = None
            if current_term:
                recent_updates = self.repo.get_recent_fee_updates(current_term.term_number, current_term.year)
            else:
                recent_updates = self.repo.get_recent_fee_updates()
            
            return self.views.system_overview(stats, current_term, recent_updates)
            
        except Exception as e:
            return self.views.error("getting system overview", str(e))
    
    def show_fee_structures(self):
        """Show fee structures with current term context"""
        try:
            # Get current term
            current_term_rows = self.repo.get_current_term()
            current_term = row_to_current_term(current_term_rows[0]) if current_term_rows else None
            
            # Get structures with term filter
            if current_term:
                structures_rows = self.repo.get_fee_structures(current_term.term_number, current_term.year)
            else:
                structures_rows = self.repo.get_fee_structures()
            
            structures = [row_to_fee_structure(row) for row in structures_rows] if structures_rows else []
            
            return self.views.fee_structures_list(structures, current_term)
            
        except Exception as e:
            return self.views.error("showing fee structures", str(e))
    
    def show_comprehensive_overview(self):
        """Show comprehensive fees overview with detailed analysis"""
        try:
            # Get current term
            current_term_rows = self.repo.get_current_term()
            current_term = row_to_current_term(current_term_rows[0]) if current_term_rows else None
            
            # Get comprehensive stats
            if current_term:
                stats_rows = self.repo.get_system_stats(current_term.term_number, current_term.year)
                category_rows = self.repo.get_fee_by_category(current_term.term_number, current_term.year)
            else:
                stats_rows = self.repo.get_system_stats()
                category_rows = self.repo.get_fee_by_category()
            
            stats = row_to_fee_stats(stats_rows[0]) if stats_rows else None
            category_data = [row_to_category_summary(row) for row in category_rows] if category_rows else None
            
            return self.views.comprehensive_overview(stats, current_term, category_data)
            
        except Exception as e:
            return self.views.error("getting comprehensive overview", str(e))
    
    def show_fee_items(self):
        """Show fee items with current term context"""
        try:
            # Get current term
            current_term_rows = self.repo.get_current_term()
            current_term = row_to_current_term(current_term_rows[0]) if current_term_rows else None
            
            # Get fee items with term filter
            if current_term:
                items_rows = self.repo.get_fee_items(current_term.term_number, current_term.year)
            else:
                items_rows = self.repo.get_fee_items()
            
            items = [row_to_fee_item(row) for row in items_rows] if items_rows else []
            
            return self.views.fee_items_overview(items, current_term)
            
        except Exception as e:
            return self.views.error("showing fee items", str(e))
    
    def show_grade_fees(self, grade_name):
        """Show fees for specific grade"""
        try:
            # Get current term
            current_term_rows = self.repo.get_current_term()
            current_term = row_to_current_term(current_term_rows[0]) if current_term_rows else None
            
            # Get grade fees with term filter
            if current_term:
                grade_rows = self.repo.get_grade_fees(grade_name, current_term.term_number, current_term.year)
            else:
                grade_rows = self.repo.get_grade_fees(grade_name)
            
            if not grade_rows:
                return self.views.error("grade fees not found", f"No fee structures found for grade '{grade_name}'")
            
            # Process the data into term structure
            structures_by_term = {}
            grade_level = grade_rows[0][2]  # Actual grade name from database
            
            for fee in grade_rows:
                term = fee[3]
                structure_name = fee[1]
                item_name = fee[5]
                amount = float(fee[6]) if fee[6] else 0
                category = fee[7]
                is_optional = fee[8]
                
                if term not in structures_by_term:
                    structures_by_term[term] = {
                        "structure_name": structure_name,
                        "items": [],
                        "total": 0,
                        "required_total": 0,
                        "optional_total": 0
                    }
                
                if item_name:  # Skip if no fee items
                    item_data = {
                        "name": item_name,
                        "amount": amount,
                        "category": category,
                        "is_optional": is_optional
                    }
                    
                    structures_by_term[term]["items"].append(item_data)
                    structures_by_term[term]["total"] += amount
                    
                    if is_optional:
                        structures_by_term[term]["optional_total"] += amount
                    else:
                        structures_by_term[term]["required_total"] += amount
            
            return self.views.grade_fee_breakdown(grade_level, structures_by_term, current_term)
            
        except Exception as e:
            return self.views.error("showing grade fees", str(e))
    
    def show_student_invoice(self, admission_no):
        """Show detailed student invoice"""
        try:
            # Get current term for context
            current_term_rows = self.repo.get_current_term()
            current_term = row_to_current_term(current_term_rows[0]) if current_term_rows else None
            
            # Get student invoice
            invoice_rows = self.repo.get_student_invoice(admission_no, current_term)
            
            if not invoice_rows:
                return self.views.error("invoice not found", f"No invoice found for student {admission_no}")
            
            invoice = row_to_student_invoice(invoice_rows[0])
            
            # Get line items
            line_items_rows = self.repo.get_invoice_line_items(invoice.invoice_id)
            line_items = [row_to_line_item(row) for row in line_items_rows] if line_items_rows else []
            
            # Get payment history
            payments_rows = self.repo.get_payment_history(invoice.invoice_id)
            payments = [row_to_payment(row) for row in payments_rows] if payments_rows else []
            
            return self.views.student_invoice_details(invoice, line_items, payments, current_term)
            
        except Exception as e:
            return self.views.error("showing student invoice", str(e))
    
    def extract_grade_from_message(self, message):
        """Extract grade name from message"""
        import re
        
        message_lower = message.lower()
        
        # Specific grade patterns
        patterns = [
            r'grade\s+(\d+)',
            r'form\s+(\d+)',
            r'pp(\d+)',
            r'pre-?primary\s*(\d+)',
            r'nursery|pre-?k'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                if 'nursery' in pattern or 'pre-k' in pattern:
                    return "Nursery"
                else:
                    grade_num = match.group(1)
                    if 'grade' in pattern:
                        return f"Grade {grade_num}"
                    elif 'form' in pattern:
                        return f"Form {grade_num}"
                    elif 'pp' in pattern:
                        return f"PP{grade_num}"
        
        # Broader extraction patterns
        extraction_patterns = [
            r'fees?\s+for\s+([^.\s]+(?:\s+\d+)?)',
            r'show\s+([^.\s]+(?:\s+\d+)?)\s+fees?',
            r'([^.\s]+(?:\s+\d+)?)\s+fees?'
        ]
        
        for pattern in extraction_patterns:
            match = re.search(pattern, message_lower)
            if match:
                grade = match.group(1).strip()
                grade = re.sub(r'\b(fees?|for|show|class)\b', '', grade).strip()
                
                if len(grade) > 1 and not grade.isdigit():
                    # Capitalize properly
                    words = grade.split()
                    capitalized_words = []
                    for word in words:
                        if word.lower() in ['grade', 'form', 'pp', 'pre-primary', 'nursery']:
                            capitalized_words.append(word.title())
                        elif word.isdigit():
                            capitalized_words.append(word)
                        else:
                            capitalized_words.append(word.title())
                    
                    return ' '.join(capitalized_words)
        
        return None
    
    def extract_student_from_message(self, message):
        """Extract student admission number from message"""
        import re
        
        patterns = [
            r'student\s+(\d{3,7})',
            r'for\s+student\s+(\d{3,7})',
            r'admission\s+(?:no|number)\s+(\d{3,7})',
            r'(?:^|\s)(\d{4,7})(?:\s|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1)
        
        return None
    
    def show_overview(self):
        """Show general fee overview"""
        return self.views.general_overview()