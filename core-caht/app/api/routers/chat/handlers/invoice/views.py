# handlers/invoice/views.py
from datetime import date
from decimal import Decimal
from ...blocks import (
    text, kpis, count_kpi, currency_kpi, table, status_column, action_row, 
    chart_xy, empty_state, error_block, timeline, timeline_item, button_group, 
    button_item, status_block, status_item
)
from ...base import ChatResponse
from .dataclasses import InvoiceRow, StudentInvoiceDetail, InvoiceLineItem, PaymentRecord, InvoiceStatistics

class InvoiceViews:
    """Pure presentation layer for invoice responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def pending_invoices_table(self, invoices: list[InvoiceRow]):
        """Rich table display for pending invoices"""
        if not invoices:
            return ChatResponse(
                response="No pending invoices found",
                intent="no_pending_invoices",
                blocks=[
                    empty_state("All Invoices Current", "No pending invoices found. All invoices are either fully paid or no invoices exist yet."),
                    text("**Current Status:**\n• All existing invoices have been paid in full\n• No outstanding amounts require collection\n• Invoice system is up to date")
                ],
                suggestions=["Generate invoices for all students", "Check enrollment status", "Show invoice summary"]
            )
        
        blocks = []
        today = date.today()
        
        # Calculate statistics
        total_outstanding = Decimal('0.00')
        overdue_count = 0
        due_soon_count = 0
        overdue_invoices = []
        
        for invoice in invoices:
            outstanding = invoice.total - invoice.paid_amount
            total_outstanding += outstanding
            
            if invoice.due_date and invoice.due_date < today:
                overdue_count += 1
                overdue_invoices.append({
                    "student_name": f"{invoice.first_name} {invoice.last_name}",
                    "admission_no": invoice.admission_no,
                    "days_overdue": (today - invoice.due_date).days,
                    "outstanding": outstanding,
                    "due_date": invoice.due_date
                })
            elif invoice.due_date and (invoice.due_date - today).days <= 7:
                due_soon_count += 1
        
        # Header
        blocks.append(text(f"**Pending Invoices ({len(invoices)})**\n\nOutstanding invoices requiring payment attention, prioritized by due date and payment urgency."))
        
        # Summary KPIs
        kpi_items = [
            count_kpi("Total Pending", len(invoices), "warning"),
            currency_kpi("Outstanding Amount", float(total_outstanding), "danger"),
            count_kpi("Overdue", overdue_count, "danger" if overdue_count > 0 else "success"),
            count_kpi("Due Soon", due_soon_count, "warning" if due_soon_count > 0 else "info")
        ]
        
        if len(invoices) > 0:
            avg_outstanding = float(total_outstanding) / len(invoices)
            kpi_items.append(currency_kpi("Average Outstanding", avg_outstanding, "info"))
        
        blocks.append(kpis(kpi_items))
        
        # Alerts
        if overdue_count > 0:
            blocks.append(text(f"**⚠️ Urgent Attention Required:** {overdue_count} invoices are overdue and need immediate follow-up with parents/guardians."))
        
        if due_soon_count > 0:
            blocks.append(text(f"**📅 Due Soon:** {due_soon_count} invoices are due within the next 7 days."))
        
        # Build table
        columns = [
            {"key": "student_name", "label": "Student", "sortable": True, "width": 200},
            {"key": "admission_no", "label": "Admission No", "sortable": True, "width": 120},
            {"key": "class_info", "label": "Class", "sortable": True, "width": 150},
            {"key": "outstanding_amount", "label": "Outstanding", "align": "right", "sortable": True, "width": 120},
            {"key": "due_date_formatted", "label": "Due Date", "sortable": True, "width": 150},
            status_column("payment_status", "Status", {
                "OVERDUE": "danger",
                "DUE_SOON": "warning", 
                "PENDING": "info",
                "PARTIAL": "warning"
            })
        ]
        
        rows = []
        for invoice in invoices:
            outstanding = invoice.total - invoice.paid_amount
            student_name = f"{invoice.first_name} {invoice.last_name}"
            
            # Determine status and formatting
            if invoice.due_date and invoice.due_date < today:
                payment_status = "OVERDUE"
                days_overdue = (today - invoice.due_date).days
                due_date_formatted = f"{invoice.due_date.strftime('%b %d')} ({days_overdue}d overdue)"
            elif invoice.due_date:
                days_left = (invoice.due_date - today).days
                if days_left <= 7:
                    payment_status = "DUE_SOON"
                    due_date_formatted = f"{invoice.due_date.strftime('%b %d')} ({days_left}d left)"
                else:
                    payment_status = "PENDING"
                    due_date_formatted = invoice.due_date.strftime('%b %d, %Y')
            else:
                payment_status = "PENDING"
                due_date_formatted = "No due date set"
            
            if invoice.status == "PARTIAL":
                payment_status = "PARTIAL"
            
            row_data = {
                "student_name": student_name,
                "admission_no": invoice.admission_no,
                "class_info": f"{invoice.class_name} ({invoice.class_level})",
                "outstanding_amount": f"KES {outstanding:,.2f}",
                "due_date_formatted": due_date_formatted,
                "payment_status": payment_status
            }
            
            rows.append(action_row(row_data, "query", {"message": f"show invoice for student {invoice.admission_no}"}))
        
        # Table actions
        table_actions = [
            {"label": "Record Payment", "type": "query", "payload": {"message": "record payment"}},
            {"label": "Send Reminders", "type": "query", "payload": {"message": "send payment reminders"}},
            {"label": "Export to Excel", "type": "query", "payload": {"message": "export pending invoices"}}
        ]
        
        # Table filters
        table_filters = [
            {"type": "select", "key": "payment_status", "label": "Payment Status", 
             "options": ["OVERDUE", "DUE_SOON", "PENDING", "PARTIAL"]},
            {"type": "text", "key": "class_info", "label": "Class"},
            {"type": "text", "key": "student_name", "label": "Student"}
        ]
        
        blocks.append(table("Outstanding Invoices", columns, rows, 
                           pagination={"mode": "client", "pageSize": 20} if len(rows) > 20 else None,
                           actions=table_actions, filters=table_filters))
        
        # Overdue timeline
        if overdue_invoices:
            blocks.append(text(f"**Most Urgent Overdue Cases ({min(5, len(overdue_invoices))}/{len(overdue_invoices)} shown):**"))
            
            timeline_items = []
            sorted_overdue = sorted(overdue_invoices, key=lambda x: x["days_overdue"], reverse=True)
            
            for overdue_inv in sorted_overdue[:5]:
                urgency_icon = "alert-circle" if overdue_inv["days_overdue"] > 30 else "clock"
                
                timeline_items.append(timeline_item(
                    time=f"{overdue_inv['days_overdue']} days overdue",
                    title=f"{overdue_inv['student_name']} (#{overdue_inv['admission_no']})",
                    subtitle=f"KES {overdue_inv['outstanding']:,.2f} • Due: {overdue_inv['due_date'].strftime('%b %d, %Y')}",
                    icon=urgency_icon,
                    meta={"status": "danger" if overdue_inv["days_overdue"] > 30 else "warning"}
                ))
            
            blocks.append(timeline(timeline_items))
        
        # Action buttons
        action_buttons = [
            button_item("Record Payment", "query", {"message": "record payment"}, "success", "md", "credit-card"),
            button_item("Send Payment Reminders", "query", {"message": "send payment reminders"}, "warning", "md", "send")
        ]
        
        if overdue_count > 0:
            action_buttons.insert(1, button_item("Focus on Overdue", "query", {"message": "show overdue invoices only"}, "danger", "md", "alert-circle"))
        
        action_buttons.extend([
            button_item("Generate Collection Report", "query", {"message": "generate collection report"}, "outline", "md", "file-text"),
            button_item("Export to Excel", "query", {"message": "export pending invoices excel"}, "outline", "md", "download")
        ])
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Found {len(invoices)} pending invoices with KES {total_outstanding:,.2f} outstanding",
            intent="pending_invoices",
            data={
                "pending_count": len(invoices),
                "total_outstanding": float(total_outstanding),
                "overdue_count": overdue_count,
                "due_soon_count": due_soon_count
            },
            blocks=blocks,
            suggestions=["Record payment", "Send payment reminders", "Show overdue invoices only", "Generate collection report"]
        )
    
    def student_invoice_details(self, invoice_detail: StudentInvoiceDetail, line_items: list[InvoiceLineItem], payments: list[PaymentRecord]):
        """Detailed invoice view for a specific student"""
        blocks = []
        
        # Header
        blocks.append(text(f"**Invoice Details - {invoice_detail.student_name}**\n\nComplete invoice information and payment history."))
        
        # Summary KPIs
        kpi_items = [
            {"label": "Invoice ID", "value": invoice_detail.invoice_id[:8], "variant": "info"},
            currency_kpi("Total Amount", float(invoice_detail.total), "primary"),
            currency_kpi("Paid Amount", float(invoice_detail.paid_amount), "success"),
            currency_kpi("Outstanding", float(invoice_detail.outstanding), "danger" if invoice_detail.outstanding > 0 else "success")
        ]
        
        # Status and due date
        status_variant = "success" if invoice_detail.status == "PAID" else "warning" if invoice_detail.status == "PARTIAL" else "info"
        kpi_items.append({"label": "Status", "value": invoice_detail.status, "variant": status_variant})
        
        if invoice_detail.due_date and invoice_detail.outstanding > 0:
            today = date.today()
            if invoice_detail.due_date < today:
                days_overdue = (today - invoice_detail.due_date).days
                kpi_items.append({"label": "Due Status", "value": f"{days_overdue}d Overdue", "variant": "danger"})
            else:
                days_left = (invoice_detail.due_date - today).days
                kpi_items.append({"label": "Due Status", "value": f"{days_left}d Left", "variant": "warning" if days_left <= 7 else "info"})
        elif invoice_detail.outstanding == 0:
            kpi_items.append({"label": "Due Status", "value": "Paid", "variant": "success"})
        
        blocks.append(kpis(kpi_items))
        
        # Student information
        info_columns = [{"key": "field", "label": "Field", "width": 150}, {"key": "value", "label": "Value"}]
        
        info_rows = [
            {"field": "Student", "value": invoice_detail.student_name},
            {"field": "Admission No", "value": invoice_detail.admission_no},
            {"field": "Class", "value": f"{invoice_detail.class_name} ({invoice_detail.class_level})"},
            {"field": "Academic Term", "value": f"{invoice_detail.term_title} ({invoice_detail.year})"},
            {"field": "Invoice Date", "value": invoice_detail.created_at.strftime('%B %d, %Y')},
            {"field": "Due Date", "value": invoice_detail.due_date.strftime('%B %d, %Y') if invoice_detail.due_date else "Not set"}
        ]
        
        blocks.append(table("Invoice Information", info_columns, info_rows))
        
        # Fee breakdown
        if line_items:
            fee_columns = [
                {"key": "item_name", "label": "Fee Item"},
                {"key": "amount", "label": "Amount", "align": "right"}
            ]
            
            fee_rows = [{"item_name": item.item_name, "amount": f"KES {item.amount:,.2f}"} for item in line_items]
            blocks.append(table("Fee Breakdown", fee_columns, fee_rows))
        
        # Payment history
        if payments:
            payment_columns = [
                {"key": "amount", "label": "Amount", "align": "right"},
                {"key": "payment_date", "label": "Date"},
                {"key": "method", "label": "Method"},
                {"key": "reference", "label": "Reference"}
            ]
            
            payment_rows = []
            for payment in payments:
                payment_rows.append({
                    "amount": f"KES {payment.amount:,.2f}",
                    "payment_date": payment.payment_date.strftime('%b %d, %Y'),
                    "method": payment.payment_method or "Not specified",
                    "reference": payment.reference_no or "-"
                })
            
            blocks.append(table("Payment History", payment_columns, payment_rows))
            
            # Payment timeline
            timeline_items = []
            for payment in payments:
                timeline_items.append(timeline_item(
                    time=payment.payment_date.strftime('%b %d, %Y'),
                    title="Payment Received",
                    subtitle=f"KES {payment.amount:,.2f} via {payment.payment_method or 'unspecified method'}",
                    icon="credit-card",
                    meta={"reference": payment.reference_no} if payment.reference_no else None
                ))
            
            blocks.append(timeline(timeline_items))
        else:
            blocks.append(text("**No payments recorded** for this invoice yet."))
        
        # Action buttons
        action_buttons = []
        
        if invoice_detail.outstanding > 0:
            action_buttons.extend([
                button_item("Record Payment", "query", {"message": f"record payment for student {invoice_detail.admission_no}"}, "success", "md", "credit-card"),
                button_item("Send Payment Reminder", "query", {"message": f"send payment reminder {invoice_detail.admission_no}"}, "warning", "md", "send")
            ])
        
        action_buttons.extend([
            button_item("Download Receipt", "query", {"message": f"download receipt {invoice_detail.admission_no}"}, "outline", "md", "download"),
            button_item("View Student Profile", "query", {"message": f"show student {invoice_detail.admission_no}"}, "outline", "md", "user"),
            button_item("Back to Pending", "query", {"message": "show pending invoices"}, "secondary", "md", "arrow-left")
        ])
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        # Status message
        if invoice_detail.outstanding > 0:
            if invoice_detail.due_date and invoice_detail.due_date < date.today():
                blocks.append(text("**⚠️ This invoice is overdue.** Consider sending a payment reminder or contacting the parent/guardian."))
            else:
                blocks.append(text("**Payment pending.** You can record payments as they are received or send reminders closer to the due date."))
        else:
            blocks.append(text("**✅ Invoice fully paid.** No further action required. Receipt can be downloaded if needed."))
        
        return ChatResponse(
            response=f"Invoice details for {invoice_detail.student_name}",
            intent="student_invoice_details",
            data={
                "invoice_id": invoice_detail.invoice_id,
                "student_name": invoice_detail.student_name,
                "admission_no": invoice_detail.admission_no,
                "total_amount": float(invoice_detail.total),
                "paid_amount": float(invoice_detail.paid_amount),
                "outstanding": float(invoice_detail.outstanding),
                "status": invoice_detail.status
            },
            blocks=blocks,
            suggestions=[
                "Record payment" if invoice_detail.outstanding > 0 else "Download receipt",
                "Send payment reminder" if invoice_detail.outstanding > 0 else "View student profile",
                "Show pending invoices"
            ]
        )
    
    def invoice_overview(self, stats: InvoiceStatistics, ready_students_count: int = 0):
        """Invoice system overview with statistics"""
        blocks = []
        school_name = self.get_school_name()
        
        # Header
        blocks.append(text(f"**Invoice Management System - {school_name}**\n\nComprehensive invoice overview and management tools for your school."))
        
        if stats.total_invoices == 0:
            # No invoices exist yet
            blocks.append(empty_state("No Invoices Found", "Get started by generating invoices for your enrolled students"))
            
            if ready_students_count > 0:
                blocks.append(text(f"**Ready for Invoice Generation**\n\nYou have **{ready_students_count} students** enrolled in active grades ready for invoice generation."))
                
                status_items = [
                    status_item("Enrolled Students", "success", f"{ready_students_count} students ready"),
                    status_item("Invoice Status", "warning", "No invoices generated yet"),
                    status_item("System Status", "info", "Ready for invoice generation")
                ]
                blocks.append(status_block(status_items))
                
                blocks.append(text("**Getting Started:**\n1. **Update fee amounts** for your grades\n2. **Generate invoices** from fee structures\n3. **Track payments** as they come in\n4. **Send reminders** for overdue invoices"))
                
                action_buttons = [
                    button_item("Generate All Invoices", "query", {"message": "generate invoices for all students"}, "success", "md", "credit-card"),
                    button_item("Update Fee Amounts", "query", {"message": "update fee amounts"}, "primary", "md", "edit"),
                    button_item("Check Enrollment", "query", {"message": "show enrolled students"}, "outline", "md", "users")
                ]
            else:
                blocks.append(text("**Setup Required**\n\nTo generate invoices, you need:\n• Classes created for your grades\n• Students enrolled in current term\n• Fee structures with amounts set"))
                
                action_buttons = [
                    button_item("Check Enrollment", "query", {"message": "show enrolled students"}, "primary", "md", "users"),
                    button_item("Setup Fee Structures", "query", {"message": "show fee structures"}, "outline", "md", "settings"),
                    button_item("Create Classes", "query", {"message": "create new class"}, "outline", "md", "plus")
                ]
            
            blocks.append(button_group(action_buttons, "horizontal", "center"))
            
            return ChatResponse(
                response="Invoice Management System ready for setup",
                intent="invoice_overview_setup",
                data={"total_invoices": 0, "ready_students": ready_students_count},
                blocks=blocks,
                suggestions=[
                    "Generate invoices for all students" if ready_students_count > 0 else "Check enrollment status",
                    "Update fee amounts",
                    "Show fee structures"
                ]
            )
        
        # Main statistics KPIs
        kpi_items = [
            count_kpi("Total Invoices", stats.total_invoices, "primary"),
            currency_kpi("Total Value", float(stats.total_value), "info"),
            currency_kpi("Collected", float(stats.total_paid), "success"),
            currency_kpi("Outstanding", float(stats.outstanding), "warning" if stats.outstanding > 0 else "success")
        ]
        
        blocks.append(kpis(kpi_items))
        
        # Status breakdown table
        status_columns = [
            {"key": "status", "label": "Status"},
            {"key": "count", "label": "Count", "align": "center"},
            {"key": "percentage", "label": "Percentage", "align": "center"}
        ]
        
        status_rows = [
            action_row({
                "status": "Fully Paid",
                "count": stats.paid,
                "percentage": f"{(stats.paid/stats.total_invoices*100):.1f}%" if stats.total_invoices > 0 else "0%"
            }, "query", {"message": "show paid invoices"}),
            action_row({
                "status": "Partial Payment",
                "count": stats.partial,
                "percentage": f"{(stats.partial/stats.total_invoices*100):.1f}%" if stats.total_invoices > 0 else "0%"
            }, "query", {"message": "show partial payment invoices"}),
            action_row({
                "status": "Pending Payment",
                "count": stats.issued,
                "percentage": f"{(stats.issued/stats.total_invoices*100):.1f}%" if stats.total_invoices > 0 else "0%"
            }, "query", {"message": "show pending invoices"})
        ]
        
        if stats.overdue > 0:
            status_rows.append(action_row({
                "status": "Overdue",
                "count": stats.overdue,
                "percentage": f"{(stats.overdue/stats.total_invoices*100):.1f}%" if stats.total_invoices > 0 else "0%"
            }, "query", {"message": "show overdue invoices"}))
        
        blocks.append(table("Invoice Status Breakdown", status_columns, status_rows))
        
        # Performance KPIs
        performance_kpis = [
            {"label": "Collection Rate", "value": f"{stats.collection_rate:.1f}%", 
             "variant": "success" if stats.collection_rate >= 80 else "warning" if stats.collection_rate >= 60 else "danger"},
            {"label": "Average Invoice", "value": f"KES {float(stats.total_value/stats.total_invoices):,.0f}" if stats.total_invoices > 0 else "KES 0", "variant": "info"},
            {"label": "Overdue Rate", "value": f"{(stats.overdue/stats.total_invoices*100):.1f}%" if stats.total_invoices > 0 else "0%", 
             "variant": "success" if stats.overdue == 0 else "danger"}
        ]
        
        blocks.append(kpis(performance_kpis))
        
        # Charts
        if stats.total_invoices > 0:
            status_chart_data = [
                {"status": "Paid", "count": stats.paid},
                {"status": "Partial", "count": stats.partial},
                {"status": "Pending", "count": stats.issued}
            ]
            
            if stats.overdue > 0:
                status_chart_data.append({"status": "Overdue", "count": stats.overdue})
            
            blocks.append(chart_xy("Invoice Status Distribution", "bar", "status", "count",
                                 [{"name": "Invoices", "data": status_chart_data}], {"height": 250}))
        
        # Management buttons
        management_buttons = [
            button_item("Show Pending Invoices", "query", {"message": "show pending invoices"}, "primary", "md", "list"),
            button_item("Record Payment", "query", {"message": "record payment"}, "success", "md", "credit-card"),
            button_item("Generate New Invoices", "query", {"message": "generate invoices for all students"}, "outline", "md", "plus"),
            button_item("Send Reminders", "query", {"message": "send payment reminders"}, "warning", "md", "send")
        ]
        
        if stats.overdue > 0:
            management_buttons.insert(1, button_item("View Overdue", "query", {"message": "show overdue invoices"}, "danger", "md", "alert-circle"))
        
        blocks.append(button_group(management_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Invoice system overview: {stats.total_invoices} invoices worth KES {stats.total_value:,.2f}",
            intent="invoice_overview_active",
            data={
                "total_invoices": stats.total_invoices,
                "total_value": float(stats.total_value),
                "total_paid": float(stats.total_paid),
                "outstanding": float(stats.outstanding),
                "collection_rate": stats.collection_rate,
                "overdue_count": stats.overdue
            },
            blocks=blocks,
            suggestions=[
                "Show pending invoices",
                "Record payment",
                "Generate new invoices" if ready_students_count > 0 else "Check enrollment",
                "Send payment reminders" if stats.overdue > 0 else "Invoice summary"
            ]
        )
    
    def invoice_generation_success(self, student_name: str, invoice_id: str, total_amount: Decimal, line_items: list[InvoiceLineItem], admission_no: str, due_date):
        """Success response for invoice generation"""
        blocks = []
        
        # Success header
        blocks.append(text(f"**Invoice Generated Successfully! ✅**\n\nInvoice created for {student_name} and is ready for payment."))
        
        # Summary KPIs
        required_total = sum(item.amount for item in line_items if not item.is_optional)
        optional_total = sum(item.amount for item in line_items if item.is_optional)
        
        kpi_items = [
            {"label": "Invoice ID", "value": invoice_id[:8], "variant": "success"},
            currency_kpi("Total Amount", float(total_amount), "primary"),
            currency_kpi("Required Fees", float(required_total), "info"),
            {"label": "Due Date", "value": due_date.strftime('%b %d'), "variant": "warning"}
        ]
        
        if optional_total > 0:
            kpi_items.append(currency_kpi("Optional Fees", float(optional_total), "secondary"))
        
        blocks.append(kpis(kpi_items))
        
        # Fee breakdown
        fee_columns = [
            {"key": "item_name", "label": "Fee Item", "sortable": True},
            {"key": "amount", "label": "Amount", "align": "right"},
            status_column("status", "Type", {"Required": "success", "Optional": "warning"})
        ]
        
        fee_rows = []
        for item in line_items:
            fee_rows.append({
                "item_name": item.item_name,
                "amount": f"KES {item.amount:,.2f}",
                "status": "Optional" if item.is_optional else "Required"
            })
        
        blocks.append(table("Fee Breakdown", fee_columns, fee_rows))
        
        # Next steps
        blocks.append(text("**Next Steps:**\n• Student/parent can now make payments against this invoice\n• Payment status will be automatically tracked\n• Partial payments are supported\n• Receipt will be generated upon payment"))
        
        # Action buttons
        action_buttons = [
            button_item("Record Payment", "query", {"message": f"record payment for student {admission_no}"}, "success", "md", "credit-card"),
            button_item("View Invoice Details", "query", {"message": f"show invoice for student {admission_no}"}, "primary", "md", "eye"),
            button_item("Send Parent Notification", "query", {"message": f"send invoice notification {admission_no}"}, "outline", "md", "send"),
            button_item("Generate Another Invoice", "query", {"message": "generate invoice for student"}, "secondary", "md", "plus")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Invoice generated successfully for {student_name}!",
            intent="invoice_generated_success",
            data={
                "invoice_id": invoice_id,
                "student_name": student_name,
                "total_amount": float(total_amount),
                "due_date": due_date.isoformat(),
                "line_items": [{"name": item.item_name, "amount": float(item.amount)} for item in line_items]
            },
            blocks=blocks,
            suggestions=["Record payment", "View invoice details", "Generate for another student", "Send parent notification"]
        )
    
    def bulk_generation_success(self, successful_count: int, total_students: int, failed_invoices: list, generated_invoices: list, total_value: float):
        """Success response for bulk invoice generation"""
        blocks = []
        
        # Success header
        blocks.append(text(f"**Bulk Generation Complete! ✅**\n\nSuccessfully generated {successful_count} invoices for active grade students."))
        
        # Summary KPIs
        kpi_items = [
            count_kpi("Generated", successful_count, "success"),
            count_kpi("Total Students", total_students, "primary")
        ]
        
        if failed_invoices:
            kpi_items.append(count_kpi("Failed", len(failed_invoices), "danger"))
        
        if total_value > 0:
            kpi_items.append(currency_kpi("Total Value", total_value, "info"))
        
        blocks.append(kpis(kpi_items))
        
        # Generated invoices table (show first 20)
        if generated_invoices:
            invoice_columns = [
                {"key": "student_name", "label": "Student", "sortable": True},
                {"key": "admission_no", "label": "Admission No", "sortable": True},
                {"key": "class_name", "label": "Class", "sortable": True},
                {"key": "amount", "label": "Amount", "align": "right"},
                {"key": "invoice_id_short", "label": "Invoice ID", "align": "center"}
            ]
            
            invoice_rows = []
            for inv in generated_invoices[:20]:
                invoice_rows.append(action_row({
                    "student_name": inv["name"],
                    "admission_no": inv["admission_no"],
                    "class_name": inv["class_name"],
                    "amount": f"KES {inv['amount']:,.2f}",
                    "invoice_id_short": inv["invoice_id"][:8]
                }, "query", {"message": f"show invoice for student {inv['admission_no']}"}))
            
            table_actions = [
                {"label": "Show All Pending", "type": "query", "payload": {"message": "show pending invoices"}},
                {"label": "Record Payments", "type": "query", "payload": {"message": "record payment"}},
                {"label": "Send Notifications", "type": "query", "payload": {"message": "send invoice notifications"}}
            ]
            
            blocks.append(table("Generated Invoices", invoice_columns, invoice_rows,
                               actions=table_actions,
                               pagination={"mode": "client", "pageSize": 20} if len(invoice_rows) > 20 else None))
        
        if failed_invoices:
            blocks.append(text(f"**Failed Generation ({len(failed_invoices)}):**\n" + 
                              "\n".join([f"• {failure}" for failure in failed_invoices[:5]]) + 
                              (f"\n• ...and {len(failed_invoices) - 5} more" if len(failed_invoices) > 5 else "")))
        
        # Next steps
        blocks.append(text("**Next Steps:**\n• Students can now make payments against their invoices\n• Send parent notifications about new invoices\n• Track payment status and send reminders\n• Generate reports for financial planning"))
        
        # Action buttons
        action_buttons = [
            button_item("Show Pending Invoices", "query", {"message": "show pending invoices"}, "primary", "md", "list"),
            button_item("Record Payment", "query", {"message": "record payment"}, "success", "md", "credit-card"),
            button_item("Send Notifications", "query", {"message": "send invoice notifications"}, "outline", "md", "send")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Successfully generated {successful_count} invoices!",
            intent="bulk_invoice_generation_success",
            data={
                "successful_count": successful_count,
                "failed_count": len(failed_invoices),
                "total_value": total_value,
                "generated_invoices": generated_invoices
            },
            blocks=blocks,
            suggestions=["Show pending invoices", "Record payments", "Send notifications", "Invoice summary"]
        )
    
    def student_not_found(self, identifier: str):
        """Student not found response"""
        return ChatResponse(
            response=f"No student found with identifier {identifier}",
            intent="student_not_found_for_invoice",
            blocks=[
                error_block("Student Not Found", f"No student exists with admission number {identifier}"),
                text("**Possible reasons:**\n• Student doesn't exist\n• Admission number is incorrect\n• Student is not enrolled")
            ],
            suggestions=[
                f"Generate invoice for different student",
                "Show enrolled students",
                "Show pending invoices"
            ]
        )
    
    def no_invoice_found(self, identifier: str):
        """No invoice found response"""
        return ChatResponse(
            response=f"No invoice found for student {identifier}",
            intent="no_invoice_found",
            blocks=[
                error_block("Invoice Not Found", f"No invoice exists for student with admission number {identifier}"),
                text("**Possible reasons:**\n• Student doesn't have an invoice generated yet\n• Admission number is incorrect\n• Student is not enrolled")
            ],
            suggestions=[
                f"Generate invoice for student {identifier}",
                "Show enrolled students",
                "Show pending invoices"
            ]
        )
    
    def error(self, operation: str, error_msg: str):
        """Error response"""
        return ChatResponse(
            response=f"Error {operation}: {error_msg}",
            intent="invoice_error",
            blocks=[error_block(f"Error {operation.title()}", error_msg)]
        )