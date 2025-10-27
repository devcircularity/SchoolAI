# handlers/payment/repo.py
import uuid
from decimal import Decimal
from ...base import db_execute_safe, db_execute_non_select

class PaymentRepo:
    """Pure data access layer for payment operations"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
        self.school_uuid = uuid.UUID(school_id)
    
    def find_student_by_admission(self, admission_no):
        """Find student with guardian information"""
        query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no,
                   g.email as guardian_email, g.phone as guardian_phone
            FROM students s
            LEFT JOIN guardians g ON s.primary_guardian_id = g.id
            WHERE s.school_id = :school_id AND s.admission_no = :admission_no AND s.status = 'ACTIVE'
            LIMIT 1
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_uuid, 
            "admission_no": admission_no
        })
    
    def get_outstanding_invoices(self, student_id):
        """Get outstanding invoices for student"""
        query = """
            SELECT id, total, status
            FROM invoices
            WHERE school_id = :school_id AND student_id = :student_id
            AND status IN ('ISSUED', 'PARTIAL')
            ORDER BY due_date ASC
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_uuid, 
            "student_id": uuid.UUID(student_id)
        })
    
    def check_student_enrollment(self, student_id):
        """Check if student is enrolled in current term"""
        query = """
            SELECT e.id FROM enrollments e
            JOIN academic_terms t ON e.term_id = t.id
            WHERE e.school_id = :school_id AND e.student_id = :student_id
            AND e.status = 'ENROLLED' AND t.state = 'ACTIVE'
            LIMIT 1
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_uuid, 
            "student_id": uuid.UUID(student_id)
        })
    
    def get_invoice_balance(self, invoice_id):
        """Get current balance for invoice"""
        query = """
            SELECT COALESCE(SUM(amount), 0) 
            FROM payments 
            WHERE invoice_id = :invoice_id
        """
        result = db_execute_safe(self.db, query, {"invoice_id": uuid.UUID(invoice_id)})
        return result[0][0] if result else 0
    
    def create_payment_record(self, payment_id, invoice_id, amount, method, reference):
        """Create payment record"""
        return db_execute_non_select(self.db, """
            INSERT INTO payments (id, school_id, invoice_id, amount, method, txn_ref, posted_at, created_at, updated_at)
            VALUES (:id, :school_id, :invoice_id, :amount, :method, :txn_ref, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, {
            "id": uuid.UUID(payment_id),
            "school_id": self.school_uuid,
            "invoice_id": uuid.UUID(invoice_id),
            "amount": str(amount),
            "method": method,
            "txn_ref": reference
        })
    
    def update_invoice_status(self, invoice_id, status):
        """Update invoice status"""
        return db_execute_non_select(self.db, """
            UPDATE invoices 
            SET status = :status, updated_at = CURRENT_TIMESTAMP 
            WHERE id = :invoice_id
        """, {
            "status": status, 
            "invoice_id": uuid.UUID(invoice_id)
        })
    
    def get_total_outstanding_for_student(self, student_id):
        """Get total outstanding balance for student"""
        query = """
            SELECT COALESCE(SUM(i.total - COALESCE(p.paid, 0)), 0)
            FROM invoices i
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) as paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.id = p.invoice_id
            WHERE i.school_id = :school_id AND i.student_id = :student_id
            AND i.status IN ('ISSUED', 'PARTIAL')
        """
        result = db_execute_safe(self.db, query, {
            "school_id": self.school_uuid, 
            "student_id": uuid.UUID(student_id)
        })
        return result[0][0] if result else 0
    
    def get_payment_summary_stats(self):
        """Get comprehensive payment statistics"""
        query = """
            SELECT 
                COUNT(*) as total_payments,
                COALESCE(SUM(amount), 0) as total_collected,
                COUNT(DISTINCT invoice_id) as invoices_paid,
                COUNT(DISTINCT DATE(posted_at)) as payment_days
            FROM payments
            WHERE school_id = :school_id
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_uuid})
    
    def get_payment_by_method(self):
        """Get payment breakdown by method"""
        query = """
            SELECT method,
                   COUNT(*) as method_count,
                   COALESCE(SUM(amount), 0) as method_total
            FROM payments
            WHERE school_id = :school_id
            GROUP BY method
            ORDER BY method_total DESC
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_uuid})
    
    def get_recent_payments(self, limit=25):
        """Get recent payments across all students"""
        query = """
            SELECT p.amount, p.method, p.txn_ref, p.posted_at,
                   s.first_name, s.last_name, s.admission_no,
                   p.id as payment_id
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            JOIN students s ON i.student_id = s.id
            WHERE p.school_id = :school_id
            ORDER BY p.posted_at DESC
            LIMIT :limit
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_uuid, 
            "limit": limit
        })
    
    def get_student_payment_history(self, admission_no):
        """Get payment history for specific student"""
        query = """
            SELECT p.amount, p.method, p.txn_ref, p.posted_at,
                   s.first_name, s.last_name, s.admission_no,
                   i.total as invoice_total, i.status as invoice_status,
                   i.id as invoice_id
            FROM payments p
            JOIN invoices i ON p.invoice_id = i.id
            JOIN students s ON i.student_id = s.id
            WHERE p.school_id = :school_id AND s.admission_no = :admission_no
            ORDER BY p.posted_at DESC
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_uuid, 
            "admission_no": admission_no
        })
    
    def get_pending_invoices(self):
        """Get pending/outstanding invoices"""
        query = """
            SELECT i.id, s.first_name, s.last_name, s.admission_no,
                   c.name as class_name, i.total, i.due_date, i.created_at,
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
            ORDER BY i.due_date ASC, s.first_name, s.last_name
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_uuid})
    
    def get_pending_payment_stats(self):
        """Get pending payment statistics"""
        query = """
            SELECT COUNT(*), COALESCE(SUM(i.total - COALESCE(p.paid, 0)), 0)
            FROM invoices i
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) as paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.id = p.invoice_id
            WHERE i.school_id = :school_id
            AND i.status IN ('ISSUED', 'PARTIAL')
            AND (i.total - COALESCE(p.paid, 0)) > 0
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_uuid})
    
    def get_recent_payment_activity(self):
        """Get recent payment activity by method"""
        query = """
            SELECT p.method, COUNT(*) as count, SUM(p.amount) as total
            FROM payments p
            WHERE p.school_id = :school_id
            AND p.posted_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY p.method
            ORDER BY total DESC
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_uuid})
    
    def get_students_with_outstanding_balances(self, student_ids=None):
        """Get students with outstanding balances for reminders"""
        base_query = """
            SELECT s.id, s.first_name, s.last_name, s.admission_no,
                   g.email as guardian_email, g.phone as guardian_phone,
                   SUM(i.total - COALESCE(p.paid, 0)) as outstanding_amount
            FROM students s
            LEFT JOIN guardians g ON s.primary_guardian_id = g.id
            JOIN invoices i ON s.id = i.student_id
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) as paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.id = p.invoice_id
            WHERE s.school_id = :school_id 
            AND s.status = 'ACTIVE'
            AND i.status IN ('ISSUED', 'PARTIAL')
            AND (i.total - COALESCE(p.paid, 0)) > 0
        """
        
        params = {"school_id": self.school_uuid}
        
        if student_ids:
            student_ids_formatted = ','.join([f"'{sid}'" for sid in student_ids])
            base_query += f" AND s.id = ANY(ARRAY[{student_ids_formatted}]::uuid[])"
        
        base_query += """
            GROUP BY s.id, s.first_name, s.last_name, s.admission_no, g.email, g.phone
            HAVING SUM(i.total - COALESCE(p.paid, 0)) > 0
            ORDER BY outstanding_amount DESC
        """
        
        return db_execute_safe(self.db, base_query, params)
    
    def log_mpesa_transaction(self, transaction_id, amount, phone_number, account_number, status, error_message=None):
        """Log M-Pesa transaction"""
        return db_execute_non_select(self.db, """
            INSERT INTO mpesa_transactions (id, school_id, transaction_id, amount, 
                   phone_number, account_number, status, error_message, processed_at, created_at, updated_at)
            VALUES (:id, :school_id, :transaction_id, :amount, :phone_number, 
                   :account_number, :status, :error_message, 
                   CASE WHEN :status = 'PROCESSED' THEN CURRENT_TIMESTAMP ELSE NULL END,
                   CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, {
            "id": uuid.uuid4(),
            "school_id": self.school_uuid,
            "transaction_id": transaction_id,
            "amount": str(amount),
            "phone_number": phone_number,
            "account_number": account_number,
            "status": status,
            "error_message": error_message
        })
    
    def get_active_student_count(self):
        """Get count of active students"""
        query = """
            SELECT COUNT(*) 
            FROM students 
            WHERE school_id = :school_id AND status = 'ACTIVE'
        """
        result = db_execute_safe(self.db, query, {"school_id": self.school_uuid})
        return result[0][0] if result else 0
    
    def get_invoice_count(self):
        """Get count of invoices"""
        query = """
            SELECT COUNT(*) 
            FROM invoices 
            WHERE school_id = :school_id
        """
        result = db_execute_safe(self.db, query, {"school_id": self.school_uuid})
        return result[0][0] if result else 0