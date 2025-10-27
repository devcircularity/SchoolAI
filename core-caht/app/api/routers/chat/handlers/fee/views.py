# handlers/fee/views.py
from ...blocks import (
    text, kpis, count_kpi, currency_kpi, table, status_column, action_row,
    chart_xy, chart_pie, empty_state, error_block, timeline, timeline_item,
    button_group, button_item, status_block, status_item
)
from ...base import ChatResponse
from .dataclasses import (
    CurrentTerm, FeeSystemStats, FeeStructureRow, FeeItemRow, 
    StudentInvoice, get_term_status, format_currency, get_category_display_name
)

class FeeViews:
    """Pure presentation layer for fee responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def system_overview(self, stats: FeeSystemStats, current_term: CurrentTerm = None, recent_updates=None):
        """Fee system overview with current term context"""
        blocks = []
        school_name = self.get_school_name()
        
        # Header with current term context
        if current_term:
            term_status, status_variant = get_term_status(current_term.start_date, current_term.end_date)
            blocks.append(text(f"**Fee Management System - {school_name}**\n\nManaging fees for **{current_term.title} ({current_term.year})** - {term_status}"))
            
            # Current term status KPIs
            term_kpis = [
                {"label": "Current Term", "value": current_term.title, "variant": "primary"},
                {"label": "Academic Year", "value": str(current_term.year), "variant": "info"},
                {"label": "Term Status", "value": term_status, "variant": status_variant}
            ]
            blocks.append(kpis(term_kpis))
        else:
            blocks.append(text(f"**Fee Management System - {school_name}**\n\nManage fee structures, view current fees, and update fee amounts across all grade levels."))
        
        # Check for no active system
        if stats.active_grades == 0:
            return self._no_active_system_response(blocks, current_term)
        
        # System health KPIs
        kpi_items = [
            count_kpi("Active Grades", stats.active_grades, "primary"),
            count_kpi("Fee Structures", stats.total_structures, "info"),
            count_kpi("Fee Items", stats.total_items, "success"),
            currency_kpi("Total Value", stats.total_value, "primary" if stats.total_value > 0 else "warning")
        ]
        
        if stats.zero_amounts > 0:
            kpi_items.append(
                count_kpi("Need Updates", stats.zero_amounts, "warning",
                         action={"type": "query", "payload": {"message": "show fees needing updates"}})
            )
        
        blocks.append(kpis(kpi_items))
        
        # System status indicators
        status_items = []
        if stats.zero_amounts == 0:
            status_items.append(status_item("Fee Amounts", "ok", "All fees have amounts set"))
        elif stats.zero_amounts < stats.total_items * 0.5:
            status_items.append(status_item("Fee Amounts", "warning", f"{stats.zero_amounts} fees need amounts"))
        else:
            status_items.append(status_item("Fee Amounts", "error", f"Most fees need amounts set"))
        
        if stats.total_structures > 0:
            status_items.append(status_item("Fee Structures", "ok", f"{stats.total_structures} structures active"))
        
        if current_term:
            status_items.append(status_item("Term Context", "unknown", f"Showing {current_term.title} data"))
        
        blocks.append(status_block(status_items))
        
        # Recent updates timeline
        if recent_updates:
            blocks.append(text("**Recent Fee Updates:**"))
            timeline_items = []
            for update in recent_updates:
                timeline_items.append(
                    timeline_item(
                        time=update[3].strftime('%b %d, %Y'),
                        title=f"{update[0]} - {update[1]}",
                        subtitle=f"Updated to {format_currency(float(update[2]))}",
                        icon="dollar-sign",
                        meta={"type": "fee_update", "amount": float(update[2])}
                    )
                )
            blocks.append(timeline(timeline_items))
        
        # Action buttons
        action_buttons = [
            button_item("Fees Overview", "query", {"message": "fees overview"}, "primary", "md", "bar-chart"),
            button_item("Update Fee Amounts", "query", {"message": "update fee amounts"}, "success", "md", "edit"),
            button_item("Show Fee Structures", "query", {"message": "show fee structures"}, "outline", "md", "list")
        ]
        
        if current_term:
            action_buttons.append(button_item("View Other Terms", "query", {"message": "show all fee structures"}, "secondary", "md", "calendar"))
        
        if stats.zero_amounts > 0:
            action_buttons.insert(2, button_item("Fix Zero Amounts", "query", {"message": "show fees needing updates"}, "warning", "md", "alert-triangle"))
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        response_text = f"Fee system for {current_term.title}: {stats.active_grades} grades with {stats.total_items} fee items" if current_term else f"Fee system managing {stats.active_grades} grades with {stats.total_items} fee items"
        
        suggestions = [
            "Fees overview",
            "Update fee amounts" if stats.zero_amounts > 0 else "Generate invoices",
            "Show fee items",
            "View other terms" if current_term else "Show current term"
        ]
        
        return ChatResponse(
            response=response_text,
            intent="fee_system_overview",
            data={
                "active_grades": stats.active_grades,
                "total_structures": stats.total_structures,
                "total_items": stats.total_items,
                "zero_amounts": stats.zero_amounts,
                "total_value": stats.total_value,
                "current_term": current_term.__dict__ if current_term else None,
                "system_health": "good" if stats.zero_amounts == 0 else "needs_attention"
            },
            blocks=blocks,
            suggestions=suggestions
        )
    
    def _no_active_system_response(self, blocks, current_term):
        """Response for when no active fee system exists"""
        if current_term:
            blocks.extend([
                empty_state("No Fee Structures for Current Term", f"Fee structures haven't been set up for {current_term.title} yet"),
                text("**Current Term Setup:**\n• Create classes for each grade level in the current term\n• Fee structures are automatically generated per term\n• Set fee amounts for the current term\n• Generate invoices for enrolled students"),
                text("**Why Term-Specific Fees:**\n• Different terms may have different fee amounts\n• Seasonal activities and programs\n• Term-based billing cycles\n• Academic year progression")
            ])
            
            action_buttons = [
                button_item("Create Classes", "query", {"message": "create new class"}, "primary", "md", "plus"),
                button_item("View Other Terms", "query", {"message": "show all fee structures"}, "outline", "md", "calendar"),
                button_item("Switch Terms", "query", {"message": "activate different term"}, "outline", "md", "refresh-cw")
            ]
            
            blocks.append(button_group(action_buttons, "horizontal", "center"))
            
            return ChatResponse(
                response=f"No fee structures found for current term: {current_term.title}",
                intent="no_current_term_fees",
                blocks=blocks,
                suggestions=[
                    "Create classes for current term",
                    "View fee structures from other terms",
                    "Switch to different term",
                    "Show grades"
                ]
            )
        else:
            blocks.extend([
                empty_state("No Active Academic Term", "You need an active academic term to manage current fees"),
                text("**Getting Started:**\n• Set up academic years and terms\n• Activate a term for current operations\n• Create classes within the active term\n• Fee structures will be generated automatically")
            ])
            
            action_buttons = [
                button_item("Show Current Term", "query", {"message": "show current term"}, "primary", "md", "calendar"),
                button_item("Academic Setup", "query", {"message": "academic setup"}, "success", "md", "settings"),
                button_item("Create Classes", "query", {"message": "create new class"}, "outline", "md", "plus")
            ]
            
            blocks.append(button_group(action_buttons, "horizontal", "center"))
            
            return ChatResponse(
                response="Fee management requires an active academic term",
                intent="no_active_term_for_fees",
                blocks=blocks,
                suggestions=[
                    "Show current term",
                    "Academic setup guide",
                    "Activate a term",
                    "Create new class"
                ]
            )
    
    def fee_structures_list(self, structures, current_term=None):
        """Display fee structures with rich table and context"""
        blocks = []
        school_name = self.get_school_name()
        
        # Header
        if current_term:
            term_status, status_variant = get_term_status(current_term.start_date, current_term.end_date)
            blocks.append(text(f"**Fee Structures - {school_name}**\n\nShowing fee structures for **{current_term.title} ({current_term.year})** - {term_status}"))
        else:
            blocks.append(text(f"**Fee Structures - {school_name}**\n\nNo active term found. Showing all available fee structures."))
        
        if not structures:
            return self._no_structures_response(blocks, current_term)
        
        # Process data
        total_structures = len(structures)
        structures_by_year = {}
        structures_by_status = {"Complete": 0, "Partial": 0, "Not Set": 0}
        total_value = 0
        current_term_structures = 0
        
        for structure in structures:
            year = structure.year
            if year not in structures_by_year:
                structures_by_year[year] = 0
            structures_by_year[year] += 1
            
            total_value += structure.total_amount
            
            if current_term and structure.term == current_term.term_number and structure.year == current_term.year:
                current_term_structures += 1
            
            if structure.zero_items == 0 and structure.item_count > 0:
                structures_by_status["Complete"] += 1
            elif structure.zero_items > 0 and structure.zero_items < structure.item_count:
                structures_by_status["Partial"] += 1
            else:
                structures_by_status["Not Set"] += 1
        
        # Summary KPIs
        kpi_items = [
            count_kpi("Structures" + (f" (Current Term)" if current_term else ""), 
                     current_term_structures if current_term else total_structures, "primary"),
            count_kpi("Academic Years", len(structures_by_year), "info"),
            count_kpi("Complete", structures_by_status["Complete"], "success"),
            currency_kpi("Total Value", total_value, "primary")
        ]
        
        if structures_by_status["Partial"] > 0:
            kpi_items.append(count_kpi("Need Updates", structures_by_status["Partial"], "warning"))
        if structures_by_status["Not Set"] > 0:
            kpi_items.append(count_kpi("Not Set", structures_by_status["Not Set"], "danger"))
        
        blocks.append(kpis(kpi_items))
        
        # Table
        columns = [
            {"key": "structure_name", "label": "Fee Structure", "sortable": True},
            {"key": "grade_level", "label": "Grade", "sortable": True},
            {"key": "term", "label": "Term", "align": "center", "sortable": True},
            {"key": "year", "label": "Year", "align": "center", "sortable": True},
            {"key": "items", "label": "Items", "align": "center"},
            {"key": "total_amount", "label": "Total Amount", "align": "right"},
            status_column("status", "Status", {
                "Complete": "success",
                "Partial": "warning",
                "Not Set": "danger",
                "Published": "info"
            })
        ]
        
        rows = []
        for structure in structures:
            is_current_term = (current_term and 
                             structure.term == current_term.term_number and 
                             structure.year == current_term.year)
            
            if structure.is_published:
                status = "Published"
            elif structure.zero_items == 0 and structure.item_count > 0:
                status = "Complete"
            elif structure.zero_items > 0 and structure.zero_items < structure.item_count:
                status = "Partial"
            else:
                status = "Not Set"
            
            structure_name = structure.name
            if is_current_term:
                structure_name = f"🟢 {structure.name}"
            
            row_data = {
                "structure_name": structure_name,
                "grade_level": structure.level,
                "term": f"Term {structure.term}",
                "year": str(structure.year),
                "items": str(structure.item_count),
                "total_amount": format_currency(structure.total_amount),
                "status": status
            }
            
            rows.append(action_row(row_data, "query", {"message": f"show fees for {structure.level}"}))
        
        blocks.append(table("Fee Structures", columns, rows,
                           pagination={"mode": "client", "pageSize": 15} if len(rows) > 15 else None))
        
        return ChatResponse(
            response=f"Found {total_structures} fee structures" + (f" ({current_term_structures} for current term)" if current_term else ""),
            intent="active_fee_structures_list",
            blocks=blocks,
            suggestions=["Update fee amounts", "Show fees for specific grade", "Fees overview"]
        )
    
    def _no_structures_response(self, blocks, current_term):
        """Response when no fee structures found"""
        if current_term:
            blocks.extend([
                empty_state("No Fee Structures for Current Term", f"No fee structures found for {current_term.title} ({current_term.year})"),
                text("**Possible reasons:**\n• Fee structures haven't been created for this term yet\n• Classes haven't been created for this term")
            ])
        else:
            blocks.extend([
                empty_state("No Fee Structures Found", "Fee structures are created automatically when you create classes"),
                text("**Getting Started:**\n• Create classes for each grade level\n• Fee structures are automatically generated")
            ])
        
        return ChatResponse(
            response="No fee structures found",
            intent="no_fee_structures",
            blocks=blocks,
            suggestions=["Create new class", "Show grades", "Show current term"]
        )
    
    def comprehensive_overview(self, stats, current_term=None, category_data=None):
        """Comprehensive fees overview with charts and analysis"""
        blocks = []
        school_name = self.get_school_name()
        
        # Header
        if current_term:
            term_status, status_variant = get_term_status(current_term.start_date, current_term.end_date)
            blocks.append(text(f"**Comprehensive Fee Analysis - {school_name}**\n\n**{current_term.title} ({current_term.year})** - {term_status}"))
        else:
            blocks.append(text(f"**Comprehensive Fee Analysis - {school_name}**\n\nDetailed breakdown across all grade levels."))
        
        # Main KPIs
        kpi_items = [
            count_kpi("Active Grades", stats.active_grades, "primary"),
            count_kpi("Fee Structures", stats.total_structures, "info"),
            count_kpi("Total Fee Items", stats.total_items, "success"),
            currency_kpi("Total Fee Value", stats.total_value, "primary")
        ]
        
        blocks.append(kpis(kpi_items))
        
        # Category breakdown if available
        if category_data:
            chart_data = []
            for cat in category_data:
                chart_data.append({
                    "category": get_category_display_name(cat.category),
                    "amount": cat.total,
                    "count": cat.count
                })
            
            title_suffix = f" - {current_term.title}" if current_term else ""
            blocks.append(chart_pie(f"Fee Distribution by Category{title_suffix}", "donut", 
                                  "category", "amount", chart_data, {"height": 300}))
        
        return ChatResponse(
            response=f"Fee analysis: {format_currency(stats.total_value)} across {stats.total_items} items",
            intent="fees_comprehensive_overview",
            blocks=blocks,
            suggestions=["Update fee amounts", "Show fee structures", "Show fee items"]
        )
    
    def fee_items_overview(self, items, current_term=None):
        """Fee items overview with categorized display"""
        blocks = []
        school_name = self.get_school_name()
        
        # Header
        if current_term:
            blocks.append(text(f"**Fee Items Overview - {school_name}**\n\n**{current_term.title} ({current_term.year})**"))
        else:
            blocks.append(text(f"**Fee Items Overview - {school_name}**\n\nAll fee items across grade levels"))
        
        if not items:
            return self._no_items_response(blocks, current_term)
        
        # Process data
        categories = {}
        needs_update = 0
        optional_count = 0
        
        for item in items:
            if item.category not in categories:
                categories[item.category] = {"items": 0, "total_usage": 0}
            categories[item.category]["items"] += 1
            categories[item.category]["total_usage"] += item.usage_count
            
            if item.zero_count > 0:
                needs_update += 1
            if item.is_optional:
                optional_count += 1
        
        # Summary KPIs
        kpi_items = [
            count_kpi("Unique Fee Items", len(items), "primary"),
            count_kpi("Categories", len(categories), "info"),
            count_kpi("Optional Items", optional_count, "secondary"),
            count_kpi("Need Updates", needs_update, "warning" if needs_update > 0 else "success")
        ]
        blocks.append(kpis(kpi_items))
        
        # Table
        columns = [
            {"key": "item_name", "label": "Fee Item", "sortable": True},
            {"key": "category", "label": "Category", "sortable": True},
            {"key": "type", "label": "Type", "sortable": True},
            {"key": "amount_range", "label": "Amount Range", "align": "right"},
            {"key": "usage", "label": "Used In", "align": "center"},
            status_column("status", "Status", {"Set": "success", "Partial": "warning", "Not Set": "danger"})
        ]
        
        rows = []
        for item in items:
            if item.min_amount == item.max_amount:
                amount_range = "Not set" if item.min_amount == 0 else format_currency(item.min_amount)
            else:
                amount_range = f"{format_currency(item.min_amount)} - {format_currency(item.max_amount)}"
            
            status = "Not Set" if item.zero_count == item.usage_count else "Partial" if item.zero_count > 0 else "Set"
            
            row_data = {
                "item_name": item.item_name,
                "category": get_category_display_name(item.category),
                "type": "Optional" if item.is_optional else "Required",
                "amount_range": amount_range,
                "usage": f"{item.usage_count} structures",
                "status": status
            }
            
            rows.append(action_row(row_data, "query", {"message": f"update {item.item_name} fees"}))
        
        blocks.append(table("Fee Items Details", columns, rows))
        
        return ChatResponse(
            response=f"Found {len(items)} fee items across {len(categories)} categories",
            intent="active_fee_items_overview",
            blocks=blocks,
            suggestions=["Update fee amounts", "Show fee structures", "Fees overview"]
        )
    
    def _no_items_response(self, blocks, current_term):
        """Response when no fee items found"""
        if current_term:
            blocks.extend([
                empty_state("No Fee Items for Current Term", f"No fee items found for {current_term.title}"),
                text("**Fee items are automatically created with new grade structures**")
            ])
        else:
            blocks.extend([
                empty_state("No Fee Items Found", "Fee items are created with grade structures"),
                text("**Create classes to generate fee items automatically**")
            ])
        
        return ChatResponse(
            response="No fee items found",
            intent="no_fee_items",
            blocks=blocks,
            suggestions=["Create new class", "Show grades", "Fee structures"]
        )
    
    def grade_fee_breakdown(self, grade_level, structures_by_term, current_term=None):
        """Detailed fee breakdown for specific grade"""
        blocks = []
        
        # Header
        if current_term:
            blocks.append(text(f"**Fee Breakdown - {grade_level}**\n\n**{current_term.title} ({current_term.year})**"))
        else:
            blocks.append(text(f"**Fee Breakdown - {grade_level}**\n\nComplete fee structure across all terms"))
        
        # Calculate totals
        all_terms_total = sum(term_data["total"] for term_data in structures_by_term.values())
        total_items = sum(len(term_data["items"]) for term_data in structures_by_term.values())
        zero_amounts = sum(1 for term_data in structures_by_term.values() 
                          for item in term_data["items"] if item["amount"] == 0)
        
        # Summary KPIs
        summary_label = "Term Total" if current_term and len(structures_by_term) == 1 else "Total Value"
        kpi_items = [
            count_kpi("Terms", len(structures_by_term), "info"),
            count_kpi("Total Items", total_items, "primary"),
            currency_kpi(summary_label, all_terms_total, "success"),
            count_kpi("Need Updates", zero_amounts, "warning" if zero_amounts > 0 else "success")
        ]
        blocks.append(kpis(kpi_items))
        
        # Term breakdown
        for term in sorted(structures_by_term.keys()):
            term_data = structures_by_term[term]
            
            # Term header
            term_header = f"### Term {term}"
            if current_term and len(structures_by_term) == 1:
                term_header += f" - {current_term.title}"
            
            blocks.append(text(term_header))
            
            # Term KPIs
            term_kpis = [
                currency_kpi("Required Fees", term_data["required_total"], "primary"),
                currency_kpi("Optional Fees", term_data["optional_total"], "info"),
                currency_kpi("Term Total", term_data["total"], "success")
            ]
            blocks.append(kpis(term_kpis))
            
            # Fee items table
            if term_data["items"]:
                columns = [
                    {"key": "item_name", "label": "Fee Item", "sortable": True},
                    {"key": "category", "label": "Category", "sortable": True},
                    {"key": "amount", "label": "Amount", "align": "right"},
                    {"key": "type", "label": "Type", "sortable": True},
                    status_column("status", "Status", {"Set": "success", "Not Set": "danger"})
                ]
                
                rows = []
                for item in term_data["items"]:
                    row_data = {
                        "item_name": item["name"],
                        "category": get_category_display_name(item["category"]),
                        "amount": format_currency(item["amount"]),
                        "type": "Optional" if item["is_optional"] else "Required",
                        "status": "Set" if item["amount"] > 0 else "Not Set"
                    }
                    rows.append(row_data)
                
                blocks.append(table(f"Term {term} Fee Items", columns, rows))
        
        # Action buttons
        action_buttons = [
            button_item(f"Update {grade_level} Fees", "query", {"message": f"update fees for {grade_level}"}, "primary", "md", "edit")
        ]
        
        if all_terms_total > 0:
            action_buttons.append(button_item("Generate Invoices", "query", {"message": f"generate invoices for {grade_level}"}, "success", "md", "file-text"))
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        response_text = f"Fee breakdown for {grade_level}: {format_currency(all_terms_total)}"
        if current_term and len(structures_by_term) == 1:
            response_text += f" for {current_term.title}"
        else:
            response_text += f" annual total across {len(structures_by_term)} terms"
        
        return ChatResponse(
            response=response_text,
            intent="grade_fee_breakdown",
            blocks=blocks,
            suggestions=[f"Update {grade_level} fees", "Compare with other grades", "Generate invoices"]
        )
    
    def student_invoice_details(self, invoice: StudentInvoice, line_items=None, payments=None, current_term=None):
        """Detailed student invoice display"""
        blocks = []
        
        # Header
        if current_term and invoice.term == current_term.term_number and invoice.year == current_term.year:
            blocks.append(text(f"**Invoice Details - {invoice.student_name}**\n\n**Current Term Invoice** - {current_term.title}"))
        else:
            blocks.append(text(f"**Invoice Details - {invoice.student_name}**\n\n**{invoice.term_title} ({invoice.year})** Invoice"))
        
        # Invoice KPIs
        kpi_items = [
            {"label": "Invoice ID", "value": invoice.invoice_id[:8], "variant": "info"},
            currency_kpi("Total Amount", invoice.total, "primary"),
            currency_kpi("Paid Amount", invoice.paid_amount, "success"),
            currency_kpi("Outstanding", invoice.outstanding, "danger" if invoice.outstanding > 0 else "success")
        ]
        
        status_variant = "success" if invoice.status == "PAID" else "warning" if invoice.status == "PARTIAL" else "info"
        kpi_items.append({"label": "Status", "value": invoice.status, "variant": status_variant})
        
        blocks.append(kpis(kpi_items))
        
        # Student info table
        info_rows = [
            {"field": "Student", "value": invoice.student_name},
            {"field": "Admission No", "value": invoice.admission_no},
            {"field": "Class", "value": f"{invoice.class_name} ({invoice.class_level})"},
            {"field": "Academic Term", "value": f"{invoice.term_title} ({invoice.year})"},
            {"field": "Invoice Date", "value": invoice.created_at.strftime('%B %d, %Y')},
            {"field": "Due Date", "value": invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else "Not set"}
        ]
        
        blocks.append(table("Invoice Information", [{"key": "field", "label": "Field"}, {"key": "value", "label": "Value"}], info_rows))
        
        # Fee breakdown
        if line_items:
            fee_rows = [{"item_name": item.item_name, "amount": format_currency(item.amount)} for item in line_items]
            blocks.append(table("Fee Breakdown", [{"key": "item_name", "label": "Fee Item"}, {"key": "amount", "label": "Amount"}], fee_rows))
        
        # Payment history
        if payments:
            payment_rows = []
            for payment in payments:
                payment_rows.append({
                    "amount": format_currency(payment.amount),
                    "payment_date": payment.created_at.strftime('%b %d, %Y'),
                    "method": payment.method or "Not specified",
                    "reference": payment.txn_ref or "-"
                })
            
            blocks.append(table("Payment History", [
                {"key": "amount", "label": "Amount"},
                {"key": "payment_date", "label": "Date"},
                {"key": "method", "label": "Method"},
                {"key": "reference", "label": "Reference"}
            ], payment_rows))
        
        # Action buttons
        action_buttons = []
        if invoice.outstanding > 0:
            action_buttons.extend([
                button_item("Record Payment", "query", {"message": f"record payment for student {invoice.admission_no}"}, "success", "md", "credit-card"),
                button_item("Send Reminder", "query", {"message": f"send payment reminder {invoice.admission_no}"}, "warning", "md", "send")
            ])
        
        action_buttons.append(button_item("Back to Invoices", "query", {"message": "show pending invoices"}, "secondary", "md", "arrow-left"))
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Invoice for {invoice.student_name}: {format_currency(invoice.total)} total, {format_currency(invoice.outstanding)} outstanding",
            intent="student_invoice_details",
            blocks=blocks,
            suggestions=[
                "Record payment" if invoice.outstanding > 0 else "Download receipt",
                "View student profile",
                "Show pending invoices"
            ]
        )
    
    def error(self, operation, error_msg):
        """Error response"""
        return ChatResponse(
            response=f"Error {operation}: {error_msg}",
            intent="error",
            blocks=[error_block(f"Error {operation.title()}", error_msg)],
            suggestions=["Show fee structures", "Fees overview", "Update fee amounts"]
        )
    
    def general_overview(self):
        """General fee overview"""
        return ChatResponse(
            response="I can help you with fee management, structures, and student invoices. What would you like to know about fees?",
            intent="fee_general",
            blocks=[text("**Fee Management**\n\nI can help you with fee structures, amounts, and invoice management.")],
            suggestions=["Show fee structures", "Fees overview", "Update fee amounts", "Show fee items"]
        )