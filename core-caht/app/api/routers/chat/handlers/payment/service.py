# handlers/payment/service.py
import uuid
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, List

from ...base import ChatResponse
from .repo import PaymentRepo
from .views import PaymentViews
from .dataclasses import (
    PaymentInfo, PaymentResult, NotificationResult,
    row_to_student, row_to_outstanding_invoice, row_to_payment_stats,
    row_to_payment_method_breakdown, row_to_recent_payment, row_to_pending_invoice,
    normalize_payment_method, generate_payment_reference, validate_payment_info,
    build_payment_data_for_notifications, parse_mpesa_callback_data
)

class PaymentService:
    """Business logic layer for payment operations"""
    
    def __init__(self, db, school_id, get_school_name, whatsapp_service_fn, email_service_fn):
        self.repo = PaymentRepo(db, school_id)
        self.views = PaymentViews(get_school_name)
        self.db = db
        self.school_id = school_id
        self.get_whatsapp_service = whatsapp_service_fn
        self.send_email_notification = email_service_fn
    
    def record_payment(self, message: str, context: Optional[Dict] = None):
        """Record a new payment"""
        try:
            payment_info = self._parse_payment_info(message, context)
            
            if not payment_info:
                return self.views.payment_info_needed()
            
            # Validate payment info
            is_valid, errors = validate_payment_info(payment_info)
            if not is_valid:
                return self.views.payment_failed_general(f"Invalid payment information: {', '.join(errors)}")
            
            # Process the payment
            result = self._process_payment(payment_info)
            
            if result.success:
                return self._handle_payment_success(result)
            else:
                return self._handle_payment_failure(result)
                
        except Exception as e:
            return self.views.error("recording payment", str(e))
    
    def show_payment_summary(self):
        """Show payment summary"""
        try:
            # Get payment statistics
            stats_rows = self.repo.get_payment_summary_stats()
            stats = row_to_payment_stats(stats_rows[0]) if stats_rows else None
            
            # Get method breakdown
            method_rows = self.repo.get_payment_by_method()
            method_breakdown = [row_to_payment_method_breakdown(row) for row in method_rows] if method_rows else []
            
            # Get recent activity
            recent_rows = self.repo.get_recent_payments(8)
            recent_activity = [row_to_recent_payment(row) for row in recent_rows] if recent_rows else []
            
            return self.views.payment_summary(stats, method_breakdown, recent_activity)
            
        except Exception as e:
            return self.views.error("getting payment summary", str(e))
    
    def show_pending_payments(self):
        """Show pending payments"""
        try:
            pending_rows = self.repo.get_pending_invoices()
            pending_invoices = [row_to_pending_invoice(row) for row in pending_rows] if pending_rows else []
            
            return self.views.pending_payments(pending_invoices)
            
        except Exception as e:
            return self.views.error("getting pending payments", str(e))
    
    def show_payment_history(self, message: str):
        """Show payment history"""
        try:
            student_info = self._parse_student_from_message(message)
            
            if student_info:
                return self._show_student_payment_history(student_info)
            else:
                return self._show_recent_payments()
                
        except Exception as e:
            return self.views.error("getting payment history", str(e))
    
    def process_mpesa_callback(self, callback_data: Dict):
        """Process M-Pesa payment callback"""
        try:
            payment_info = parse_mpesa_callback_data(callback_data)
            
            if not payment_info:
                return ChatResponse(
                    response="Invalid M-Pesa callback data received",
                    intent="invalid_callback"
                )
            
            # Process the payment
            result = self._process_payment(payment_info)
            
            # Log transaction
            status = "PROCESSED" if result.success else "FAILED"
            error_message = None if result.success else result.message
            
            self.repo.log_mpesa_transaction(
                payment_info.reference, payment_info.amount, payment_info.phone,
                payment_info.admission_no, status, error_message
            )
            
            self.db.commit()
            
            return ChatResponse(
                response=f"M-Pesa payment {'processed' if result.success else 'failed'}: {result.message}",
                intent=f"mpesa_payment_{'processed' if result.success else 'failed'}",
                data=result.payment_data if result.success else {"error": result.message}
            )
            
        except Exception as e:
            return self.views.error("processing M-Pesa callback", str(e))
    
    def show_overview(self):
        """Show general payment overview"""
        return self.views.general_overview()
    
    def _parse_payment_info(self, message: str, context: Optional[Dict] = None) -> Optional[PaymentInfo]:
        """Extract payment information from message or context"""
        # Pattern: "Record M-Pesa payment of 15000 for student 2025451"
        pattern1 = r'record\s+(mpesa|m-pesa|cash|bank)?\s*payment\s+of\s+(\d+)\s+for\s+student\s+(\d+)'
        match1 = re.search(pattern1, message.lower())
        
        if match1:
            raw_method = match1.group(1) or "mpesa"
            normalized_method = normalize_payment_method(raw_method)
            
            return PaymentInfo(
                method=normalized_method,
                amount=float(match1.group(2)),
                admission_no=match1.group(3),
                reference=generate_payment_reference()
            )
        
        # Pattern: "M-Pesa payment 15000 student 2025451"
        pattern2 = r'(mpesa|m-pesa|cash|bank)?\s*payment\s+(\d+)\s+student\s+(\d+)'
        match2 = re.search(pattern2, message.lower())
        
        if match2:
            raw_method = match2.group(1) or "mpesa"
            normalized_method = normalize_payment_method(raw_method)
            
            return PaymentInfo(
                method=normalized_method,
                amount=float(match2.group(2)),
                admission_no=match2.group(3),
                reference=generate_payment_reference()
            )
        
        # Check context for M-Pesa callback data
        if context and "mpesa_payment" in context:
            mpesa_data = context["mpesa_payment"]
            return PaymentInfo(
                method="MPESA",
                amount=float(mpesa_data.get("amount", 0)),
                admission_no=mpesa_data.get("account_number"),
                reference=mpesa_data.get("transaction_id"),
                phone=mpesa_data.get("phone_number")
            )
        
        return None
    
    def _parse_student_from_message(self, message: str) -> Optional[str]:
        """Extract student admission number from message"""
        pattern = r'(\d{4,7})'
        match = re.search(pattern, message)
        return match.group(1) if match else None
    
    def _process_payment(self, payment_info: PaymentInfo) -> PaymentResult:
        """Process the payment and update invoices"""
        try:
            # Find student
            student_rows = self.repo.find_student_by_admission(payment_info.admission_no)
            
            if not student_rows:
                return PaymentResult(
                    success=False,
                    message=f"Student with admission number {payment_info.admission_no} not found."
                )
            
            student = row_to_student(student_rows[0])
            
            # Find outstanding invoices
            invoice_rows = self.repo.get_outstanding_invoices(student.id)
            
            if not invoice_rows:
                # Check if student is enrolled but has no invoices
                enrollment = self.repo.check_student_enrollment(student.id)
                
                if enrollment:
                    return PaymentResult(
                        success=False,
                        message=f"No invoices found for {student.full_name} (#{payment_info.admission_no}).\n\n" +
                               f"The student is enrolled but no invoice has been generated yet.\n" +
                               f"Please generate an invoice first before recording payments.",
                        suggestion="generate_invoice",
                        student_data={
                            "admission_no": payment_info.admission_no,
                            "student_name": student.full_name
                        }
                    )
                else:
                    return PaymentResult(
                        success=False,
                        message=f"No invoices found for {student.full_name} (#{payment_info.admission_no}).\n\n" +
                               f"The student is not enrolled in the current term.\n" +
                               f"Please enroll the student first."
                    )
            
            # Apply payment to invoices
            outstanding_invoices = [row_to_outstanding_invoice(row) for row in invoice_rows]
            remaining_amount = Decimal(str(payment_info.amount))
            updated_invoices = []
            
            for invoice in outstanding_invoices:
                if remaining_amount <= 0:
                    break
                
                # Calculate current balance
                paid_amount = Decimal(str(self.repo.get_invoice_balance(invoice.id)))
                invoice_balance = invoice.total - paid_amount
                
                if invoice_balance > 0:
                    payment_for_invoice = min(remaining_amount, invoice_balance)
                    
                    # Create payment record
                    payment_id = str(uuid.uuid4())
                    self.repo.create_payment_record(
                        payment_id, invoice.id, payment_for_invoice, 
                        payment_info.method, payment_info.reference
                    )
                    
                    # Update invoice status
                    new_balance = invoice_balance - payment_for_invoice
                    new_status = "PAID" if new_balance <= 0 else "PARTIAL"
                    self.repo.update_invoice_status(invoice.id, new_status)
                    
                    updated_invoices.append({
                        "invoice_id": invoice.id,
                        "payment_applied": float(payment_for_invoice),
                        "new_balance": float(new_balance),
                        "status": new_status
                    })
                    
                    remaining_amount -= payment_for_invoice
            
            self.db.commit()
            
            # Get total outstanding balance after payment
            total_outstanding = self.repo.get_total_outstanding_for_student(student.id)
            
            # Build payment data
            payment_data = build_payment_data_for_notifications(
                student, payment_info.amount, payment_info.method,
                payment_info.reference, float(total_outstanding),
                updated_invoices, self.school_id, self.views.get_school_name()
            )
            
            return PaymentResult(
                success=True,
                message=f"Payment processed successfully for {student.full_name}",
                payment_data=payment_data
            )
            
        except Exception as e:
            self.db.rollback()
            return PaymentResult(
                success=False,
                message=f"Error processing payment: {str(e)}"
            )
    
    def _handle_payment_success(self, result: PaymentResult):
        """Handle successful payment processing"""
        # Send notifications
        notification_results = self._send_payment_notifications(result.payment_data)
        
        return self.views.payment_success(result.payment_data, notification_results)
    
    def _handle_payment_failure(self, result: PaymentResult):
        """Handle failed payment processing"""
        if result.suggestion == "generate_invoice":
            return self.views.payment_failed_no_invoice(result.student_data)
        else:
            return self.views.payment_failed_general(result.message)
    
    def _send_payment_notifications(self, payment_data: Dict) -> NotificationResult:
        """Send both email and WhatsApp notifications"""
        results = NotificationResult()
        
        # Send email notification
        try:
            email_sent = self.send_email_notification(payment_data)
            results.email_sent = email_sent
            if not email_sent:
                results.email_error = "No parent email found or email service unavailable"
        except Exception as e:
            results.email_error = str(e)
        
        # Send WhatsApp notification
        try:
            whatsapp_service = self.get_whatsapp_service()
            if whatsapp_service and payment_data.get("guardian_phone"):
                whatsapp_sent = whatsapp_service.send_payment_notification(payment_data)
                results.whatsapp_sent = whatsapp_sent
                if not whatsapp_sent:
                    results.whatsapp_error = "WhatsApp service unavailable"
            else:
                results.whatsapp_error = "WhatsApp service not available or no phone number"
        except Exception as e:
            results.whatsapp_error = str(e)
        
        return results
    
    def _show_student_payment_history(self, admission_no: str):
        """Show payment history for specific student"""
        # Implementation would go here - similar to existing logic
        # but using the repo and views layers
        pass
    
    def _show_recent_payments(self):
        """Show recent payments across all students"""
        # Implementation would go here - similar to existing logic
        # but using the repo and views layers
        pass