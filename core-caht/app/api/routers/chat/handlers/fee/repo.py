# handlers/fee/repo.py
from ...base import db_execute_safe, db_execute_non_select

class FeeRepo:
    """Pure data access layer for fee operations"""
    
    def __init__(self, db, school_id):
        self.db = db
        self.school_id = school_id
    
    def get_current_term(self):
        """Get current active academic term"""
        query = """
            SELECT t.id, t.title, t.term, t.start_date, t.end_date,
                   y.year, y.title as year_title
            FROM academic_terms t
            JOIN academic_years y ON t.year_id = y.id
            WHERE t.school_id = :school_id AND t.state = 'ACTIVE'
            ORDER BY y.year DESC, t.term ASC
            LIMIT 1
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def get_system_stats(self, term=None, year=None):
        """Get fee system statistics with optional term filter"""
        query = """
            SELECT 
                COUNT(DISTINCT fs.level) as active_grades,
                COUNT(fs.id) as total_structures,
                COUNT(fi.id) as total_items,
                COUNT(CASE WHEN fi.amount = 0 THEN 1 END) as zero_amounts,
                COALESCE(SUM(fi.amount), 0) as total_value
            FROM fee_structures fs
            LEFT JOIN fee_items fi ON fs.id = fi.fee_structure_id
            INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
            WHERE fs.school_id = :school_id
        """
        
        params = {"school_id": self.school_id}
        
        if term and year:
            query += " AND fs.term = :term AND fs.year = :year"
            params.update({"term": term, "year": year})
        
        return db_execute_safe(self.db, query, params)
    
    def get_fee_structures(self, term=None, year=None):
        """Get fee structures with optional term filter"""
        query = """
            SELECT fs.id, fs.name, fs.level, fs.term, fs.year, fs.is_default, fs.is_published,
                   COUNT(fi.id) as item_count,
                   COALESCE(SUM(fi.amount), 0) as total_amount,
                   COUNT(CASE WHEN fi.amount = 0 THEN 1 END) as zero_items,
                   COUNT(c.id) as class_count
            FROM fee_structures fs
            LEFT JOIN fee_items fi ON fs.id = fi.fee_structure_id
            INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
            WHERE fs.school_id = :school_id
        """
        
        params = {"school_id": self.school_id}
        
        if term and year:
            query += " AND fs.term = :term AND fs.year = :year"
            params.update({"term": term, "year": year})
        
        query += """ 
            GROUP BY fs.id, fs.name, fs.level, fs.term, fs.year, fs.is_default, fs.is_published
            ORDER BY fs.year DESC, fs.term ASC, fs.level
        """
        
        return db_execute_safe(self.db, query, params)
    
    def get_fee_items(self, term=None, year=None):
        """Get fee items with optional term filter"""
        query = """
            SELECT DISTINCT fi.item_name, fi.category, fi.is_optional, fi.billing_cycle,
                   MIN(fi.amount) as min_amount, MAX(fi.amount) as max_amount,
                   COUNT(*) as usage_count,
                   COUNT(CASE WHEN fi.amount = 0 THEN 1 END) as zero_count,
                   AVG(fi.amount) as avg_amount
            FROM fee_items fi
            JOIN fee_structures fs ON fi.fee_structure_id = fs.id
            INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
            WHERE fi.school_id = :school_id
        """
        
        params = {"school_id": self.school_id}
        
        if term and year:
            query += " AND fs.term = :term AND fs.year = :year"
            params.update({"term": term, "year": year})
        
        query += """
            GROUP BY fi.item_name, fi.category, fi.is_optional, fi.billing_cycle 
            ORDER BY fi.category, fi.item_name
        """
        
        return db_execute_safe(self.db, query, params)
    
    def get_fee_by_category(self, term=None, year=None):
        """Get fee breakdown by category"""
        query = """
            SELECT fi.category, COUNT(*) as count, 
                   COALESCE(SUM(fi.amount), 0) as total,
                   COALESCE(AVG(fi.amount), 0) as avg_amount,
                   COUNT(CASE WHEN fi.amount = 0 THEN 1 END) as zero_count
            FROM fee_items fi
            JOIN fee_structures fs ON fi.fee_structure_id = fs.id
            INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
            WHERE fi.school_id = :school_id
        """
        
        params = {"school_id": self.school_id}
        
        if term and year:
            query += " AND fs.term = :term AND fs.year = :year"
            params.update({"term": term, "year": year})
        
        query += " GROUP BY fi.category ORDER BY total DESC"
        
        return db_execute_safe(self.db, query, params)
    
    def get_grade_fees(self, grade_name, term=None, year=None):
        """Get fees for specific grade with optional term filter"""
        query = """
            SELECT fs.id, fs.name, fs.level, fs.term, fs.year, 
                   fi.item_name, fi.amount, fi.category, fi.is_optional, fi.billing_cycle
            FROM fee_structures fs
            LEFT JOIN fee_items fi ON fs.id = fi.fee_structure_id
            INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
            WHERE fs.school_id = :school_id AND fs.level ILIKE :grade
        """
        
        params = {"school_id": self.school_id, "grade": f"%{grade_name}%"}
        
        if term and year:
            query += " AND fs.term = :term AND fs.year = :year"
            params.update({"term": term, "year": year})
        
        query += " ORDER BY fs.term, fi.category, fi.item_name"
        
        return db_execute_safe(self.db, query, params)
    
    def get_student_invoice(self, admission_no, current_term=None):
        """Get student invoice with payment details"""
        query = """
            SELECT i.id, i.total, i.status, i.created_at, i.due_date, i.term, i.year,
                   s.first_name, s.last_name, s.admission_no,
                   c.name as class_name, c.level as class_level,
                   COALESCE(p.paid, 0) as paid_amount,
                   t.title as term_title
            FROM invoices i
            JOIN students s ON i.student_id = s.id
            JOIN classes c ON s.class_id = c.id
            LEFT JOIN academic_terms t ON i.term = t.term AND i.year = (
                SELECT year FROM academic_years WHERE id = t.year_id LIMIT 1
            )
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) as paid
                FROM payments
                GROUP BY invoice_id
            ) p ON i.id = p.invoice_id
            WHERE i.school_id = :school_id AND s.admission_no = :admission_no
        """
        
        params = {"school_id": self.school_id, "admission_no": admission_no}
        
        # Prioritize current term if available
        if current_term:
            query += """
                ORDER BY CASE WHEN i.term = :current_term AND i.year = :current_year 
                         THEN 0 ELSE 1 END, i.created_at DESC LIMIT 1
            """
            params.update({
                "current_term": current_term["term_number"],
                "current_year": current_term["year"]
            })
        else:
            query += " ORDER BY i.created_at DESC LIMIT 1"
        
        return db_execute_safe(self.db, query, params)
    
    def get_invoice_line_items(self, invoice_id):
        """Get invoice line items"""
        query = """
            SELECT item_name, amount
            FROM invoiceline
            WHERE invoice_id = :invoice_id
            ORDER BY item_name
        """
        return db_execute_safe(self.db, query, {"invoice_id": invoice_id})
    
    def get_payment_history(self, invoice_id):
        """Get payment history for invoice"""
        query = """
            SELECT amount, created_at, method, txn_ref
            FROM payments
            WHERE invoice_id = :invoice_id
            ORDER BY created_at DESC
        """
        return db_execute_safe(self.db, query, {"invoice_id": invoice_id})
    
    def find_existing_fee_items(self, fee_item):
        """Find existing fee items matching name"""
        query = """
            SELECT fs.level, fi.item_name, fi.amount, fi.id
            FROM fee_items fi
            JOIN fee_structures fs ON fi.fee_structure_id = fs.id
            INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
            WHERE fi.school_id = :school_id 
            AND fi.item_name ILIKE :item_name
            ORDER BY fs.level, fi.item_name
        """
        return db_execute_safe(self.db, query, {
            "school_id": self.school_id,
            "item_name": f"%{fee_item}%"
        })
    
    def get_available_fee_items(self):
        """Get list of available fee items"""
        query = """
            SELECT DISTINCT fi.item_name
            FROM fee_items fi
            JOIN fee_structures fs ON fi.fee_structure_id = fs.id
            INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
            WHERE fi.school_id = :school_id
            ORDER BY fi.item_name
            LIMIT 10
        """
        return db_execute_safe(self.db, query, {"school_id": self.school_id})
    
    def update_fee_amounts(self, fee_item, amount, grade_level=None):
        """Update fee amounts for specific item"""
        if grade_level:
            # Update for specific grade
            query = """
                UPDATE fee_items 
                SET amount = :amount, updated_at = CURRENT_TIMESTAMP
                WHERE school_id = :school_id 
                AND item_name ILIKE :item_name
                AND fee_structure_id IN (
                    SELECT fs.id FROM fee_structures fs
                    INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
                    WHERE fs.school_id = :school_id AND fs.level ILIKE :level
                )
            """
            return db_execute_non_select(self.db, query, {
                "amount": amount,
                "school_id": self.school_id,
                "item_name": f"%{fee_item}%",
                "level": f"%{grade_level}%"
            })
        else:
            # Update for all grades
            query = """
                UPDATE fee_items 
                SET amount = :amount, updated_at = CURRENT_TIMESTAMP
                WHERE school_id = :school_id 
                AND item_name ILIKE :item_name
                AND fee_structure_id IN (
                    SELECT fs.id FROM fee_structures fs
                    INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
                    WHERE fs.school_id = :school_id
                )
            """
            return db_execute_non_select(self.db, query, {
                "amount": amount,
                "school_id": self.school_id,
                "item_name": f"%{fee_item}%"
            })
    
    def get_recent_fee_updates(self, term=None, year=None, limit=5):
        """Get recent fee updates"""
        query = """
            SELECT fi.item_name, fs.level, fi.amount, fi.updated_at
            FROM fee_items fi
            JOIN fee_structures fs ON fi.fee_structure_id = fs.id
            INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
            WHERE fi.school_id = :school_id
            AND fi.updated_at > fi.created_at
        """
        
        params = {"school_id": self.school_id}
        
        if term and year:
            query += " AND fs.term = :term AND fs.year = :year"
            params.update({"term": term, "year": year})
        
        query += f" ORDER BY fi.updated_at DESC LIMIT {limit}"
        
        return db_execute_safe(self.db, query, params)