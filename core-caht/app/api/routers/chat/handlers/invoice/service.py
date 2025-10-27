# handlers/invoice/service.py
import uuid
from decimal import Decimal
from datetime import date, timedelta
from ...base import ChatResponse
from .repo import InvoiceRepo
from .views import InvoiceViews
from .dataclasses import (
    row_to_invoice, row_to_student_invoice_detail, row_to_line_item, 
    row_to_payment_record, stats_row_to_dataclass, row_to_student_for_invoice
)
from ..shared.parsing import extract_admission_number

class InvoiceService:
    """Business logic layer for invoice operations"""
    
    def __init__(self, db, school_id, get_school_name):
        self.repo = InvoiceRepo(db, school_id)
        self.views = InvoiceViews(get_school_name)
        self.db = db
        self.school_id = school_id
    
    def show_pending_invoices(self):
        """Show all pending invoices"""
        try:
            rows = self.repo.get_pending_invoices()
            invoices = [row_to_invoice(row) for row in rows]
            return self.views.pending_invoices_table(invoices)
        except Exception as e:
            return self.views.error("getting pending invoices", str(e))
    
    def show_student_invoice(self, message: str):
        """Show specific student's invoice"""
        try:
            admission_no = extract_admission_number(message)
            if not admission_no:
                return ChatResponse(
                    response="I couldn't identify the student from your message.",
                    intent="student_parse_error",
                    blocks=[],
                    suggestions=["Show pending invoices", "List enrolled students"]
                )
            
            rows = self.repo.get_student_invoice(admission_no)
            if not rows:
                return self.views.no_invoice_found(admission_no)
            
            invoice_detail = row_to_student_invoice_detail(rows[0])
            
            # Get line items and payments
            line_items_rows = self.repo.get_invoice_line_items(invoice_detail.invoice_id)
            line_items = [row_to_line_item(row) for row in line_items_rows]
            
            payments_rows = self.repo.get_invoice_payments(invoice_detail.invoice_id)
            payments = [row_to_payment_record(row) for row in payments_rows]
            
            return self.views.student_invoice_details(invoice_detail, line_items, payments)
            
        except Exception as e:
            return self.views.error("showing student invoice", str(e))
    
    def show_overview(self):
        """Show invoice system overview"""
        try:
            stats_row = self.repo.get_invoice_statistics()
            if not stats_row or len(stats_row) == 0:
                # No data, return empty stats
                from .dataclasses import InvoiceStatistics
                stats = InvoiceStatistics(0, 0, 0, 0, Decimal('0'), Decimal('0'), 0, Decimal('0'), 0.0)
            else:
                stats = stats_row_to_dataclass(stats_row[0])
            
            ready_students_count = self.repo.get_ready_students_count()
            return self.views.invoice_overview(stats, ready_students_count)
            
        except Exception as e:
            return self.views.error("getting invoice overview", str(e))
    
    def generate_student_invoice(self, message: str):
        """Generate invoice for specific student"""
        try:
            admission_no = extract_admission_number(message)
            if not admission_no:
                return ChatResponse(
                    response="I couldn't identify the student from your message.",
                    intent="student_parse_error",
                    suggestions=["Generate invoices for all students", "Show enrolled students"]
                )
            
            # Find enrolled student
            student_rows = self.repo.find_enrolled_student(admission_no)
            if not student_rows:
                return self.views.student_not_found(admission_no)
            
            student = row_to_student_for_invoice(student_rows[0])
            
            # Check if invoice already exists
            existing = self.repo.check_existing_invoice(student.id, student.term_number, student.academic_year)
            if existing:
                return self._handle_existing_invoice(student, existing[0])
            
            # Generate the invoice
            return self._generate_invoice_for_student(student)
            
        except Exception as e:
            return self.views.error("generating student invoice", str(e))
    
    def generate_bulk_invoices(self):
        """Generate invoices for all eligible students"""
        try:
            students_rows = self.repo.get_students_needing_invoices()
            if not students_rows:
                return ChatResponse(
                    response="All enrolled students in active grades already have invoices",
                    intent="all_active_invoices_exist",
                    suggestions=["Show pending invoices", "Show invoice summary", "Record payments"]
                )
            
            students = [row_to_student_for_invoice(row) for row in students_rows]
            
            successful_invoices = 0
            failed_invoices = []
            generated_invoices = []
            
            for student in students:
                try:
                    result = self._generate_single_invoice(student)
                    
                    if result["success"]:
                        successful_invoices += 1
                        student_name = f"{student.first_name} {student.last_name}"
                        generated_invoices.append({
                            "name": student_name,
                            "admission_no": student.admission_no,
                            "class_name": student.class_name,
                            "amount": result["amount"],
                            "invoice_id": result["invoice_id"]
                        })
                    else:
                        failed_invoices.append(f"{student.first_name} {student.last_name} - {result['error']}")
                        
                except Exception as e:
                    failed_invoices.append(f"{student.first_name} {student.last_name} - {str(e)}")
                    continue
            
            if successful_invoices > 0:
                self.db.commit()
                total_value = sum(inv["amount"] for inv in generated_invoices)
                return self.views.bulk_generation_success(
                    successful_invoices, len(students), failed_invoices, generated_invoices, total_value
                )
            else:
                self.db.rollback()
                return ChatResponse(
                    response=f"Bulk invoice generation failed for all students",
                    intent="bulk_invoice_generation_failed",
                    suggestions=["Check fee structures", "Update fee amounts", "Generate individual invoices"]
                )
                
        except Exception as e:
            self.db.rollback()
            return self.views.error("bulk invoice generation", str(e))
    
    def _handle_existing_invoice(self, student, existing_invoice):
        """Handle case when invoice already exists"""
        student_name = f"{student.first_name} {student.last_name}"
        
        return ChatResponse(
            response=f"Invoice already exists for {student_name}",
            intent="invoice_already_exists",
            data={
                "invoice_id": str(existing_invoice[0]),
                "student_id": student.id,
                "amount": float(existing_invoice[1])
            },
            suggestions=["Show invoice details", "Record payment", "Generate for different student"]
        )
    
    def _generate_invoice_for_student(self, student):
        """Generate actual invoice for student"""
        try:
            # Get fee structure
            fee_structure_rows = self.repo.get_fee_structure_for_student(
                student.class_level, student.term_number, student.academic_year
            )
            
            if not fee_structure_rows:
                return ChatResponse(
                    response=f"Cannot generate invoice for {student.first_name} {student.last_name}",
                    intent="no_active_fee_structure_for_invoice",
                    suggestions=["Check student class assignment", "Show fee structures", "Update fee amounts"]
                )
            
            # Calculate total and prepare line items
            total_amount = Decimal('0.00')
            invoice_lines = []
            
            for fee in fee_structure_rows:
                item_name = fee[2]
                amount = Decimal(str(fee[3]))
                is_optional = fee[4]
                category = fee[5]
                
                total_amount += amount
                invoice_lines.append({
                    "item_name": item_name,
                    "amount": amount,
                    "category": category,
                    "is_optional": is_optional
                })
            
            if total_amount <= 0:
                return ChatResponse(
                    response=f"Cannot generate invoice for {student.first_name} {student.last_name}",
                    intent="zero_fee_amounts_active",
                    suggestions=[f"Update fees for {student.class_level}", "Show fee structure", "Set tuition fees"]
                )
            
            # Create the invoice
            invoice_id = str(uuid.uuid4())
            due_date = date.today() + timedelta(days=30)
            
            # Insert invoice record
            affected_rows = self.repo.create_invoice(
                invoice_id, student.id, student.term_number, student.academic_year, total_amount, due_date
            )
            
            if affected_rows == 0:
                return ChatResponse(
                    response="Failed to create invoice - database error",
                    intent="invoice_creation_failed"
                )
            
            # Create invoice line items
            for line in invoice_lines:
                line_id = str(uuid.uuid4())
                self.repo.create_invoice_line_item(line_id, invoice_id, line['item_name'], line['amount'])
            
            # Commit changes
            self.db.commit()
            
            # Convert to dataclass format for view
            from .dataclasses import InvoiceLineItem
            line_items = [
                InvoiceLineItem(
                    item_name=line['item_name'],
                    amount=line['amount'],
                    category=line.get('category'),
                    is_optional=line.get('is_optional', False)
                ) for line in invoice_lines
            ]
            
            student_name = f"{student.first_name} {student.last_name}"
            return self.views.invoice_generation_success(
                student_name, invoice_id, total_amount, line_items, student.admission_no, due_date
            )
            
        except Exception as e:
            self.db.rollback()
            return self.views.error("generating invoice", str(e))
    
    def _generate_single_invoice(self, student):
        """Generate single invoice for bulk processing"""
        try:
            # Get fee structure
            fee_structure_rows = self.repo.get_fee_structure_for_student(
                student.class_level, student.term_number, student.academic_year
            )
            
            if not fee_structure_rows:
                return {"success": False, "error": "No active fee structure found"}
            
            # Calculate total
            total_amount = sum(Decimal(str(fee[3])) for fee in fee_structure_rows)
            
            if total_amount <= 0:
                return {"success": False, "error": "Zero amount fees"}
            
            # Create invoice
            invoice_id = str(uuid.uuid4())
            due_date = date.today() + timedelta(days=30)
            
            self.repo.create_invoice(
                invoice_id, student.id, student.term_number, student.academic_year, total_amount, due_date
            )
            
            # Create line items
            for fee in fee_structure_rows:
                line_id = str(uuid.uuid4())
                self.repo.create_invoice_line_item(line_id, invoice_id, fee[2], str(fee[3]))
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "amount": float(total_amount)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}