# handlers/payment/views.py
from datetime import datetime, date
from ...blocks import (
    text, kpis, count_kpi, currency_kpi, table, status_column, action_row,
    chart_xy, empty_state, error_block, timeline, timeline_item,
    button_group, button_item, status_block, status_item
)
from ...base import ChatResponse
from .dataclasses import (
    PaymentStats, PaymentMethodBreakdown, RecentPayment, PendingInvoice,
    NotificationResult, format_currency, get_method_icon, get_urgency_level
)

class PaymentViews:
    """Pure presentation layer for payment responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def payment_info_needed(self):
        """Response when payment info is not provided"""
        return ChatResponse(
            response="Payment recording requires specific information",
            intent="payment_info_needed",
            blocks=[
                text("**Record New Payment**\n\nTo record a payment, please provide the following information:"),
                
                table(
                    "Required Information",
                    [
                        {"key": "field", "label": "Field", "width": 150},
                        {"key": "description", "label": "Description"},
                        {"key": "example", "label": "Example"}
                    ],
                    [
                        {"field": "Student ID", "description": "Admission number", "example": "2025451"},
                        {"field": "Amount", "description": "Payment amount in KES", "example": "15000"},
                        {"field": "Method", "description": "Payment method", "example": "M-Pesa, Cash, Bank"},
                        {"field": "Reference", "description": "Transaction reference", "example": "QH7K8P2M (optional)"}
                    ]
                ),
                
                text("**Supported Formats:**\n• 'Record M-Pesa payment of 15000 for student 2025451'\n• 'Payment of 25000 via cash for student 1234'\n• 'Process bank payment 30000 student 5678'"),
                
                text("**Payment Methods:**\n• **M-Pesa** - Mobile money payments\n• **Cash** - Physical cash payments\n• **Bank** - Bank transfers and checks")
            ],
            suggestions=[
                "Show payment guide",
                "Show pending invoices",
                "Payment summary",
                "List students"
            ]
        )
    
    def payment_success(self, payment_data, notification_results: NotificationResult):
        """Success response for payment recording"""
        blocks = []
        
        # Success header
        blocks.append(text(f"**Payment Recorded Successfully!**\n\nPayment has been processed and applied to the student's account."))
        
        # Payment summary KPIs
        kpi_items = [
            currency_kpi("Amount Paid", payment_data['amount_paid'], "success"),
            {"label": "Payment Method", "value": payment_data['method'], "variant": "primary"},
            currency_kpi("Remaining Balance", payment_data['remaining_balance'], "warning" if payment_data['remaining_balance'] > 0 else "success"),
            {"label": "Reference", "value": payment_data['reference'][:12], "variant": "info"}
        ]
        
        blocks.append(kpis(kpi_items))
        
        # Payment details
        details_rows = [
            {"field": "Student", "value": payment_data['student_name']},
            {"field": "Admission No", "value": payment_data['admission_no']},
            {"field": "Payment Date", "value": datetime.now().strftime('%B %d, %Y at %I:%M %p')},
            {"field": "Transaction Ref", "value": payment_data['reference']},
            {"field": "Invoices Updated", "value": str(len(payment_data.get('invoices_updated', [])))}
        ]
        
        blocks.append(table("Payment Details", 
                           [{"key": "field", "label": "Field"}, {"key": "value", "label": "Value"}], 
                           details_rows))
        
        # Invoice allocation if applicable
        if payment_data.get('invoices_updated'):
            invoice_rows = []
            for invoice in payment_data['invoices_updated']:
                invoice_rows.append({
                    "invoice_id": invoice['invoice_id'][:8],
                    "payment_applied": format_currency(invoice['payment_applied']),
                    "new_balance": format_currency(invoice['new_balance']),
                    "status": invoice['status']
                })
            
            blocks.append(table("Payment Allocation", [
                {"key": "invoice_id", "label": "Invoice"},
                {"key": "payment_applied", "label": "Applied", "align": "right"},
                {"key": "new_balance", "label": "Balance", "align": "right"},
                status_column("status", "Status", {"PAID": "success", "PARTIAL": "warning"})
            ], invoice_rows))
        
        # Notification status
        notification_status = []
        if notification_results.email_sent:
            notification_status.append(status_item("Email Notification", "ok", "Sent to parent"))
        elif notification_results.email_error:
            notification_status.append(status_item("Email Notification", "warning", notification_results.email_error[:50]))
        
        if notification_results.whatsapp_sent:
            notification_status.append(status_item("WhatsApp Notification", "ok", "Sent to parent"))
        elif notification_results.whatsapp_error:
            notification_status.append(status_item("WhatsApp Notification", "warning", notification_results.whatsapp_error[:50]))
        
        # Action buttons based on remaining balance
        if payment_data['remaining_balance'] > 0:
            blocks.append(text(f"**Account Status:** Outstanding balance of {format_currency(payment_data['remaining_balance'])} remaining"))
            
            action_buttons = [
                button_item("Record Another Payment", "query", {"message": f"record payment for student {payment_data['admission_no']}"}, "primary", "md", "credit-card"),
                button_item("Show Student Balance", "query", {"message": f"show balance for student {payment_data['admission_no']}"}, "outline", "md", "calculator"),
                button_item("Send Payment Reminder", "query", {"message": f"send reminder {payment_data['admission_no']}"}, "outline", "md", "bell")
            ]
        else:
            blocks.append(text("**Account Status:** Fully paid! All invoices settled."))
            
            action_buttons = [
                button_item("View Payment History", "query", {"message": f"payment history for student {payment_data['admission_no']}"}, "primary", "md", "history"),
                button_item("Record Payment for Another", "query", {"message": "record payment"}, "outline", "md", "users"),
                button_item("Payment Summary", "query", {"message": "payment summary"}, "outline", "md", "bar-chart")
            ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        # Build response message
        response_message = f"Payment recorded: {format_currency(payment_data['amount_paid'])} for {payment_data['student_name']}"
        if notification_results.email_sent or notification_results.whatsapp_sent:
            channels = []
            if notification_results.email_sent:
                channels.append("email")
            if notification_results.whatsapp_sent:
                channels.append("WhatsApp")
            response_message += f" - notifications sent via {' and '.join(channels)}"
        
        return ChatResponse(
            response=response_message,
            intent="payment_recorded",
            data=payment_data,
            blocks=blocks,
            suggestions=[
                "Show student balance" if payment_data['remaining_balance'] > 0 else "View payment history",
                "Record another payment",
                "Payment summary"
            ]
        )
    
    def payment_failed_no_invoice(self, student_data):
        """Error response when no invoice exists for student"""
        blocks = [
            error_block("No Invoice Found", f"Cannot record payment for {student_data.get('student_name', 'student')} - no invoice exists"),
            text("**Issue:** The student is enrolled but no invoice has been generated yet.\n\n**Required Action:** Generate an invoice first before recording payments."),
            text("**What invoices do:**\n• Create formal billing records\n• Track payment applications\n• Generate receipts and statements\n• Enable automated fee processing")
        ]
        
        action_buttons = [
            button_item("Generate Invoice", "query", {"message": f"generate invoice for student {student_data.get('admission_no', '')}"}, "primary", "md", "file-plus"),
            button_item("Generate All Invoices", "query", {"message": "generate invoices for all students"}, "outline", "md", "files"),
            button_item("Check Enrollment", "query", {"message": "show enrollment status"}, "outline", "md", "users")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Payment failed: No invoice found for student {student_data.get('admission_no', '')}",
            intent="payment_failed_no_invoice",
            data=student_data,
            blocks=blocks,
            suggestions=[
                f"Generate invoice for student {student_data.get('admission_no', '')}",
                "Generate invoices for all students",
                "Show enrolled students"
            ]
        )
    
    def payment_failed_general(self, error_message):
        """General payment failure response"""
        blocks = [
            error_block("Payment Processing Failed", error_message),
            text("**Common Issues:**\n• Student not found or not active\n• No outstanding invoices to apply payment to\n• Invalid payment amount or method\n• Database connection problems"),
            text("**Try These Steps:**\n• Verify student admission number\n• Check if student is enrolled\n• Ensure invoices have been generated\n• Confirm payment details are correct")
        ]
        
        action_buttons = [
            button_item("Check Student Details", "query", {"message": "show students"}, "primary", "md", "search"),
            button_item("Show Enrolled Students", "query", {"message": "show enrolled students"}, "outline", "md", "users"),
            button_item("Generate Invoices", "query", {"message": "generate invoices"}, "outline", "md", "file-plus")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=error_message,
            intent="payment_failed",
            blocks=blocks,
            suggestions=["Check student details", "Show enrolled students", "Generate invoices"]
        )
    
    def payment_summary(self, stats: PaymentStats, method_breakdown: list, recent_activity: list = None):
        """Payment summary overview"""
        blocks = []
        school_name = self.get_school_name()
        
        if stats.total_payments == 0:
            return self._no_payments_response()
        
        # Header
        blocks.append(text(f"**Payment Summary - {school_name}**\n\nComprehensive overview of all payments processed and financial activity."))
        
        # Main KPIs
        kpi_items = [
            count_kpi("Total Payments", stats.total_payments, "primary"),
            currency_kpi("Total Collected", stats.total_collected, "success"),
            count_kpi("Invoices Paid", stats.invoices_paid, "info"),
            {"label": "Avg per Payment", "value": format_currency(stats.avg_payment), "variant": "secondary"}
        ]
        
        blocks.append(kpis(kpi_items))
        
        # Method breakdown table
        if method_breakdown:
            method_rows = []
            for method_data in method_breakdown:
                percentage = (method_data.total / stats.total_collected * 100) if stats.total_collected > 0 else 0
                method_rows.append({
                    "payment_method": method_data.method,
                    "transaction_count": str(method_data.count),
                    "total_amount": format_currency(method_data.total),
                    "percentage": f"{percentage:.1f}%",
                    "avg_amount": format_currency(method_data.avg_amount)
                })
            
            blocks.append(table("Payment Methods Breakdown", [
                {"key": "payment_method", "label": "Method", "sortable": True},
                {"key": "transaction_count", "label": "Transactions", "align": "center"},
                {"key": "total_amount", "label": "Total Amount", "align": "right"},
                {"key": "percentage", "label": "Share", "align": "center"},
                {"key": "avg_amount", "label": "Avg Amount", "align": "right"}
            ], method_rows))
            
            # Payment distribution chart
            chart_data = [{"method": m.method, "amount": m.total} for m in method_breakdown]
            blocks.append(chart_xy("Payment Distribution by Method", "pie", "method", "amount", 
                                 [{"name": "Amount (KES)", "data": chart_data}], {"height": 250}))
        
        # Recent activity if provided
        if recent_activity:
            blocks.append(text("**Recent Payment Activity:**"))
            timeline_items = []
            for payment in recent_activity[:5]:
                method_icon = get_method_icon(payment.method)
                timeline_items.append(timeline_item(
                    time=payment.posted_at.strftime('%b %d, %Y') if payment.posted_at else "Unknown",
                    title=format_currency(payment.amount),
                    subtitle=f"{payment.student_name} (#{payment.admission_no}) via {payment.method}",
                    icon=method_icon
                ))
            
            blocks.append(timeline(timeline_items))
        
        # Action buttons
        action_buttons = [
            button_item("Show Recent Payments", "query", {"message": "show recent payments"}, "primary", "md", "clock"),
            button_item("Record New Payment", "query", {"message": "record payment"}, "success", "md", "plus"),
            button_item("Show Pending Invoices", "query", {"message": "show pending invoices"}, "outline", "md", "alert-circle"),
            button_item("Generate Report", "query", {"message": "generate payment report"}, "outline", "md", "download")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Payment summary: {stats.total_payments} payments totaling {format_currency(stats.total_collected)}",
            intent="payment_summary",
            data={
                "total_collected": stats.total_collected,
                "total_payments": stats.total_payments,
                "invoices_paid": stats.invoices_paid
            },
            blocks=blocks,
            suggestions=["Show recent payments", "Show pending invoices", "Record new payment", "Generate report"]
        )
    
    def _no_payments_response(self):
        """Response when no payments exist"""
        return ChatResponse(
            response="No payments recorded yet",
            intent="no_payments",
            blocks=[
                empty_state("No Payments Yet", "Start recording payments to track your school's financial activity"),
                text("**Getting Started:**\n• Record M-Pesa payments automatically via webhook\n• Manually record cash and bank payments\n• Send payment confirmations to parents\n• Track outstanding balances and payment history")
            ],
            suggestions=["Record new payment", "Show pending invoices", "Setup M-Pesa integration", "Payment guide"]
        )
    
    def pending_payments(self, pending_invoices: list):
        """Display pending payments"""
        blocks = []
        
        if not pending_invoices:
            return self._no_pending_payments_response()
        
        # Header
        blocks.append(text(f"**Pending Payments ({len(pending_invoices)})**\n\nOutstanding invoices requiring payment attention, prioritized by due date and urgency."))
        
        # Calculate statistics
        total_outstanding = sum(invoice.outstanding_amount for invoice in pending_invoices)
        overdue_count = sum(1 for invoice in pending_invoices if invoice.is_overdue)
        due_soon_count = sum(1 for invoice in pending_invoices 
                           if invoice.due_date and (date.today() - invoice.due_date).days <= 7 and not invoice.is_overdue)
        
        # Summary KPIs
        kpi_items = [
            count_kpi("Total Pending", len(pending_invoices), "warning"),
            currency_kpi("Outstanding Amount", total_outstanding, "danger"),
            count_kpi("Overdue", overdue_count, "danger" if overdue_count > 0 else "success"),
            count_kpi("Due Soon", due_soon_count, "warning" if due_soon_count > 0 else "info")
        ]
        
        blocks.append(kpis(kpi_items))
        
        # Pending invoices table
        invoice_rows = []
        for invoice in pending_invoices:
            if invoice.is_overdue:
                payment_status = "OVERDUE"
                due_date_formatted = f"{invoice.due_date.strftime('%b %d')} ({invoice.days_overdue}d overdue)"
            elif invoice.due_date:
                days_left = (invoice.due_date - date.today()).days
                if days_left <= 7:
                    payment_status = "DUE_SOON"
                    due_date_formatted = f"{invoice.due_date.strftime('%b %d')} ({days_left}d left)"
                else:
                    payment_status = "PENDING"
                    due_date_formatted = invoice.due_date.strftime('%b %d, %Y')
            else:
                payment_status = "PENDING"
                due_date_formatted = "No due date"
            
            if invoice.status == "PARTIAL":
                payment_status = "PARTIAL"
            
            invoice_rows.append(action_row({
                "student_name": invoice.student_name,
                "admission_no": invoice.admission_no,
                "class_name": invoice.class_name,
                "outstanding_amount": format_currency(invoice.outstanding_amount),
                "due_date_formatted": due_date_formatted,
                "payment_status": payment_status
            }, "query", {"message": f"record payment for student {invoice.admission_no}"}))
        
        blocks.append(table("Outstanding Invoices", [
            {"key": "student_name", "label": "Student", "sortable": True},
            {"key": "admission_no", "label": "Admission No", "sortable": True},
            {"key": "class_name", "label": "Class", "sortable": True},
            {"key": "outstanding_amount", "label": "Outstanding", "align": "right", "sortable": True},
            {"key": "due_date_formatted", "label": "Due Date", "sortable": True},
            status_column("payment_status", "Status", {
                "OVERDUE": "danger", "DUE_SOON": "warning", "PENDING": "info", "PARTIAL": "warning"
            })
        ], invoice_rows))
        
        # Action buttons
        action_buttons = [
            button_item("Record Payment", "query", {"message": "record payment"}, "success", "md", "credit-card"),
            button_item("Send Payment Reminders", "query", {"message": "send payment reminders"}, "warning", "md", "send")
        ]
        
        if overdue_count > 0:
            action_buttons.insert(1, button_item("Focus on Overdue", "query", {"message": "show overdue invoices only"}, "danger", "md", "alert-triangle"))
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Pending payments: {len(pending_invoices)} invoices with {format_currency(total_outstanding)} outstanding",
            intent="pending_payments",
            blocks=blocks,
            suggestions=["Record payment", "Send payment reminders", "Show overdue only" if overdue_count > 0 else "Export to Excel"]
        )
    
    def _no_pending_payments_response(self):
        """Response when no pending payments exist"""
        return ChatResponse(
            response="No pending payments found",
            intent="no_pending_payments",
            blocks=[
                text("**All Payments Current**\n\nNo pending payments found. All invoices are either fully paid or no invoices exist yet."),
                status_block([
                    status_item("Payment Status", "ok", "All invoices current"),
                    status_item("Outstanding Amount", "ok", "KES 0")
                ])
            ],
            suggestions=["Generate invoices for enrolled students", "Show payment summary", "Check enrollment status"]
        )
    
    def general_overview(self):
        """General payment overview"""
        return ChatResponse(
            response="I can help you with payment processing, recording, and management. What would you like to do?",
            intent="payment_general",
            blocks=[text("**Payment Management**\n\nI can help you record payments, track outstanding balances, and manage payment notifications.")],
            suggestions=["Record new payment", "Show payment summary", "Show pending invoices", "Payment guide"]
        )
    
    def error(self, operation, error_msg):
        """Error response"""
        return ChatResponse(
            response=f"Error {operation}: {error_msg}",
            intent="error",
            blocks=[error_block(f"Error {operation.title()}", error_msg)],
            suggestions=["Show payment summary", "Record payment", "Show pending invoices"]
        )