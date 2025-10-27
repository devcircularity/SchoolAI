# handlers/invoice/repo.py
from decimal import Decimal
from datetime import date, timedelta
from ...base import db_execute_safe, db_execute_non_select

class InvoiceRepo:
    """Pure data access layer for invoice operations"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
    
    def get_pending_invoices(self):
        """Get all pending invoices with student details"""
        return db_execute_safe(self.db,
            """SELECT i.id, s.first_name, s.last_name, s.admission_no,
                      c.name as class_name, c.level as class_level, i.total, i.due_date, i.created_at,
                      COALESCE(p.paid, 0) as paid_amount, i.status
               FROM invoices i
               JOIN students s ON i.student_id = s.id
               JOIN classes c ON s.class_id = c.id
               LEFT JOIN (
                   SELECT invoice_id, SUM(amount) as paid
                   FROM payments
                   GROUP BY invoice_id
               ) p ON i.id = p.invoice_id
               WHERE i.school_id = :school_id
               AND i.status IN ('ISSUED', 'PARTIAL')
               AND (i.total - COALESCE(p.paid, 0)) > 0
               ORDER BY i.due_date ASC, s.first_name, s.last_name""",
            {"school_id": self.school_id}
        )
    
    def get_student_invoice(self, admission_no):
        """Get student's invoice with details"""
        return db_execute_safe(self.db,
            """SELECT i.id, i.total, i.status, i.created_at, i.due_date, i.term, i.year,
                      s.first_name, s.last_name, s.admission_no,
                      c.name as class_name, c.level as class_level,
                      COALESCE(p.paid, 0) as paid_amount,
                      t.title as term_title
               FROM invoices i
               JOIN students s ON i.student_id = s.id
               JOIN classes c ON s.class_id = c.id
               JOIN academic_terms t ON i.term = t.term AND i.year = (SELECT year FROM academic_years WHERE id = t.year_id)
               LEFT JOIN (
                   SELECT invoice_id, SUM(amount) as paid
                   FROM payments
                   GROUP BY invoice_id
               ) p ON i.id = p.invoice_id
               WHERE i.school_id = :school_id AND s.admission_no = :admission_no
               ORDER BY i.created_at DESC
               LIMIT 1""",
            {"school_id": self.school_id, "admission_no": admission_no}
        )
    
    def get_invoice_line_items(self, invoice_id):
        """Get line items for an invoice"""
        return db_execute_safe(self.db,
            """SELECT item_name, amount
               FROM invoiceline
               WHERE invoice_id = :invoice_id
               ORDER BY item_name""",
            {"invoice_id": invoice_id}
        )
    
    def get_invoice_payments(self, invoice_id):
        """Get payment history for an invoice"""
        return db_execute_safe(self.db,
            """SELECT amount, created_at, payment_method, reference_no
               FROM payments
               WHERE invoice_id = :invoice_id
               ORDER BY created_at DESC""",
            {"invoice_id": invoice_id}
        )
    
    def get_invoice_statistics(self):
        """Get comprehensive invoice statistics"""
        return db_execute_safe(self.db,
            """SELECT 
                COUNT(*) as total_invoices,
                COUNT(*) FILTER (WHERE i.status = 'ISSUED') as issued,
                COUNT(*) FILTER (WHERE i.status = 'PARTIAL') as partial,
                COUNT(*) FILTER (WHERE i.status = 'PAID') as paid,
                COALESCE(SUM(i.total), 0) as total_value,
                COALESCE(SUM(p.paid), 0) as total_paid,
                COUNT(*) FILTER (WHERE i.due_date < CURRENT_DATE AND i.status IN ('ISSUED', 'PARTIAL')) as overdue
            FROM invoices i
            JOIN students s ON i.student_id = s.id
            JOIN classes c ON s.class_id = c.id
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) as paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.id = p.invoice_id
            WHERE i.school_id = :school_id
            AND EXISTS (
                SELECT 1 FROM fee_structures fs
                INNER JOIN classes c2 ON c2.level = fs.level AND c2.school_id = fs.school_id
                WHERE fs.school_id = i.school_id AND fs.level = c.level
            )""",
            {"school_id": self.school_id}
        )
    
    def get_students_needing_invoices(self):
        """Get students who need invoices generated"""
        return db_execute_safe(self.db,
            """SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id,
                      c.name as class_name, c.level as class_level,
                      e.id as enrollment_id, e.term_id, t.title as term_title, 
                      t.term, y.year
               FROM students s
               JOIN classes c ON s.class_id = c.id
               JOIN enrollments e ON s.id = e.student_id
               JOIN academic_terms t ON e.term_id = t.id
               JOIN academic_years y ON t.year_id = y.id
               WHERE s.school_id = :school_id
               AND s.status = 'ACTIVE' 
               AND e.status = 'ENROLLED' 
               AND t.state = 'ACTIVE'
               AND EXISTS (
                   SELECT 1 FROM fee_structures fs
                   INNER JOIN classes c2 ON c2.level = fs.level AND c2.school_id = fs.school_id
                   WHERE fs.school_id = s.school_id AND fs.level = c.level
               )
               AND NOT EXISTS (
                   SELECT 1 FROM invoices i 
                   WHERE i.student_id = s.id 
                   AND i.term = t.term 
                   AND i.year = y.year
               )
               ORDER BY c.name, s.first_name, s.last_name""",
            {"school_id": self.school_id}
        )
    
    def get_ready_students_count(self):
        """Get count of students ready for invoice generation"""
        result = db_execute_safe(self.db,
            """SELECT COUNT(*) FROM students s
               JOIN classes c ON s.class_id = c.id
               JOIN enrollments e ON s.id = e.student_id
               JOIN academic_terms t ON e.term_id = t.id
               WHERE s.school_id = :school_id
               AND s.status = 'ACTIVE' 
               AND e.status = 'ENROLLED' 
               AND t.state = 'ACTIVE'
               AND EXISTS (
                   SELECT 1 FROM fee_structures fs
                   INNER JOIN classes c2 ON c2.level = fs.level AND c2.school_id = fs.school_id
                   WHERE fs.school_id = s.school_id AND fs.level = c.level
               )""",
            {"school_id": self.school_id}
        )
        return result[0][0] if result and len(result) > 0 else 0
    
    def check_existing_invoice(self, student_id, term, year):
        """Check if invoice already exists for student in term/year"""
        return db_execute_safe(self.db,
            """SELECT id, total, status, created_at, due_date
               FROM invoices
               WHERE school_id = :school_id AND student_id = :student_id 
               AND term = :term AND year = :year
               LIMIT 1""",
            {
                "school_id": self.school_id,
                "student_id": student_id,
                "term": term,
                "year": year
            }
        )
    
    def get_fee_structure_for_student(self, class_level, term, year):
        """Get fee structure for student's grade level"""
        return db_execute_safe(self.db,
            """SELECT fs.id, fs.name, fi.item_name, fi.amount, fi.is_optional, 
                      fi.category, fi.billing_cycle
               FROM fee_structures fs
               JOIN fee_items fi ON fs.id = fi.fee_structure_id
               INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
               WHERE fs.school_id = :school_id 
               AND fs.level ILIKE :level
               AND fs.term = :term
               AND fs.year = :year
               ORDER BY fi.category, fi.item_name""",
            {
                "school_id": self.school_id,
                "level": f"%{class_level}%",
                "term": term,
                "year": year
            }
        )
    
    def create_invoice(self, invoice_id, student_id, term, year, total_amount, due_date):
        """Create new invoice record"""
        return db_execute_non_select(self.db,
            """INSERT INTO invoices (id, school_id, student_id, term, year, total, status, due_date, created_at, updated_at)
               VALUES (:id, :school_id, :student_id, :term, :year, :total, 'ISSUED', :due_date, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            {
                "id": invoice_id,
                "school_id": self.school_id,
                "student_id": student_id,
                "term": term,
                "year": year,
                "total": str(total_amount),
                "due_date": due_date
            }
        )
    
    def create_invoice_line_item(self, line_id, invoice_id, item_name, amount):
        """Create invoice line item"""
        return db_execute_non_select(self.db,
            """INSERT INTO invoiceline (id, school_id, invoice_id, item_name, amount, created_at, updated_at)
               VALUES (:id, :school_id, :invoice_id, :item_name, :amount, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            {
                "id": line_id,
                "school_id": self.school_id,
                "invoice_id": invoice_id,
                "item_name": item_name,
                "amount": str(amount)
            }
        )
    
    def find_enrolled_student(self, admission_no):
        """Find student who is enrolled in current term"""
        return db_execute_safe(self.db,
            """SELECT s.id, s.first_name, s.last_name, s.admission_no, s.class_id,
                      c.name as class_name, c.level as class_level,
                      e.id as enrollment_id, e.term_id, t.title as term_title, 
                      t.term, y.year
               FROM students s
               JOIN classes c ON s.class_id = c.id
               JOIN enrollments e ON s.id = e.student_id
               JOIN academic_terms t ON e.term_id = t.id
               JOIN academic_years y ON t.year_id = y.id
               WHERE s.school_id = :school_id AND s.admission_no = :admission_no 
               AND s.status = 'ACTIVE' AND e.status = 'ENROLLED' AND t.state = 'ACTIVE'
               LIMIT 1""",
            {"school_id": self.school_id, "admission_no": admission_no}
        )