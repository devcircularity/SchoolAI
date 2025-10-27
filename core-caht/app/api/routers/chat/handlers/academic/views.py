# handlers/academic/views.py
from ...blocks import (
    text, kpis, count_kpi, table, status_column, action_row,
    empty_state, error_block, button_group, button_item,
    status_block, status_item, chart_pie
)
from ...base import ChatResponse
from .dataclasses import TermRow, EnrollmentStats, SetupStatus, serialize_date

class AcademicViews:
    """Pure presentation layer for academic responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def no_active_term(self):
        """No active term found response"""
        return ChatResponse(
            response="No active academic term found.",
            intent="no_active_term",
            blocks=[
                empty_state("No Active Term", "You need to set up and activate an academic term to manage student enrollments"),
                text("**Getting Started:**\n\n1. **Create Academic Years** - Set up your school calendar structure\n2. **Create Terms** - Add terms like 'Term 1', 'Term 2', etc.\n3. **Activate a Term** - Make one term active for current enrollments\n\nAn active term is required before students can be enrolled.")
            ],
            suggestions=[
                "Show academic calendar",
                "Help me set up academic terms",
                "Create new academic year"
            ]
        )
    
    def current_term_details(self, term: TermRow, stats: EnrollmentStats):
        """Display current active term with statistics"""
        blocks = []
        school_name = self.get_school_name()
        
        # Header
        blocks.append(text(f"**Current Academic Term - {school_name}**\n\nHere's your currently active academic term with enrollment statistics."))
        
        # Term info KPIs
        term_kpis = [
            {"label": "Term", "value": term.title, "variant": "primary"},
            {"label": "Academic Year", "value": str(term.year), "variant": "info"},
            {"label": "Status", "value": term.state, "variant": "success"}
        ]
        
        # Add date info if available
        start_date = serialize_date(term.start_date)
        end_date = serialize_date(term.end_date)
        if start_date and end_date:
            from datetime import date
            today = date.today().isoformat()
            if today < start_date:
                date_status = "Upcoming"
            elif today > end_date:
                date_status = "Completed"
            else:
                date_status = "In Progress"
            
            term_kpis.append({"label": "Period", "value": date_status, "variant": "info"})
        
        blocks.append(kpis(term_kpis))
        
        # Enrollment statistics
        enrollment_kpis = [
            count_kpi("Total Enrollments", stats.total_enrollments, "primary"),
            count_kpi("Unique Students", stats.unique_students, "success"),
            count_kpi("Classes with Students", stats.enrolled_classes, "info")
        ]
        blocks.append(kpis(enrollment_kpis))
        
        # Term details table
        detail_columns = [
            {"key": "field", "label": "Detail", "width": 150},
            {"key": "value", "label": "Value"}
        ]
        
        detail_rows = [
            {"field": "Term ID", "value": term.id},
            {"field": "Term Title", "value": term.title},
            {"field": "Academic Year", "value": f"{term.year_title} ({term.year})"},
            {"field": "Status", "value": term.state}
        ]
        
        if start_date and end_date:
            detail_rows.extend([
                {"field": "Start Date", "value": start_date},
                {"field": "End Date", "value": end_date}
            ])
        
        blocks.append(table("Term Information", detail_columns, detail_rows))
        
        # Quick actions
        action_buttons = [
            button_item("Show Enrollments", "query", {"message": "show term enrollments"}, "primary", "md", "users"),
            button_item("Enroll Students", "query", {"message": "enroll students"}, "success", "md", "user-plus"),
            button_item("Switch Term", "query", {"message": "activate different term"}, "outline", "md", "refresh-cw"),
            button_item("Academic Calendar", "query", {"message": "show academic calendar"}, "secondary", "md", "calendar")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Current term: {term.title} ({term.year})",
            intent="current_term",
            data={
                "term_id": term.id,
                "term_title": term.title,
                "academic_year": term.year,
                "state": term.state,
                "start_date": start_date,
                "end_date": end_date,
                "enrollment_stats": {
                    "total": stats.total_enrollments,
                    "unique_students": stats.unique_students,
                    "enrolled_classes": stats.enrolled_classes
                }
            },
            blocks=blocks,
            suggestions=[
                "Show term enrollments",
                "Enroll students",
                "List all academic terms",
                "Switch to different term"
            ]
        )
    
    def term_switch_confirmation(self, current_term, original_message=""):
        """Confirm switching from current active term"""
        blocks = []
        blocks.append(text(f"**Active Term Detected**\n\nThere's already an active term: **{current_term['title']} ({current_term['year']})**\n\nSwitching terms will deactivate the current term and activate a new one. This affects student enrollments."))
        
        # Confirmation buttons
        confirm_buttons = [
            button_item("Yes, switch terms", "query", {"message": "yes, switch terms"}, "warning", "md", "refresh-cw"),
            button_item("Show available terms", "query", {"message": "show available terms"}, "outline", "md", "list"),
            button_item("Keep current term", "query", {"message": "no, keep current term"}, "secondary", "md", "x")
        ]
        
        blocks.append(button_group(confirm_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response="Confirm term switch",
            intent="term_already_active",
            data={
                "current_active_term": current_term,
                "context": {
                    "handler": "academic",
                    "flow": "activate_term",
                    "step": "confirm_switch",
                    "original_message": original_message,
                    "current_active_id": current_term["id"]
                }
            },
            blocks=blocks,
            suggestions=[
                "Yes, switch terms",
                "No, keep current term",
                "Show available terms"
            ]
        )
    
    def switch_cancelled(self):
        """Term switch was cancelled"""
        return ChatResponse(
            response="Keeping the current active term.",
            intent="term_switch_cancelled",
            data={"context": {}},
            blocks=[
                text("**Term Switch Cancelled**\n\nThe current active term remains unchanged. You can switch terms anytime.")
            ],
            suggestions=[
                "Show current term",
                "List all terms",
                "Academic calendar"
            ]
        )
    
    def no_terms_to_activate(self):
        """No terms available for activation"""
        return ChatResponse(
            response="No terms available to activate.",
            intent="no_terms_to_activate",
            data={"context": {}},
            blocks=[
                empty_state("No Terms Available", "All terms are either already active or closed"),
                text("**What you can do:**\n\n• Create a new academic year with terms\n• Check your academic calendar\n• View the current active term")
            ],
            suggestions=[
                "Show academic calendar",
                "Create new academic year",
                "Show current term"
            ]
        )
    
    def term_selection(self, available_terms):
        """Show available terms for selection"""
        blocks = []
        
        # Header
        blocks.append(text("**Select Term to Activate**\n\nChoose which term you'd like to make active. The active term is used for student enrollments."))
        
        # Terms selection table
        columns = [
            {"key": "option", "label": "#", "width": 60, "align": "center"},
            {"key": "term_title", "label": "Term", "sortable": True},
            {"key": "academic_year", "label": "Year", "align": "center"},
            {"key": "period", "label": "Period"},
            {"key": "status", "label": "Status", "badge": {"map": {"PLANNED": "info", "ACTIVE": "success", "CLOSED": "secondary"}}}
        ]
        
        rows = []
        for i, term in enumerate(available_terms, 1):
            term_title = term[1]
            year = term[3]
            start_date = serialize_date(term[4])
            end_date = serialize_date(term[5])
            
            period = ""
            if start_date and end_date:
                period = f"{start_date} to {end_date}"
            else:
                period = "Dates not set"
            
            row_data = {
                "option": str(i),
                "term_title": term_title,
                "academic_year": str(year),
                "period": period,
                "status": term[2]
            }
            
            rows.append(action_row(row_data, "query", {"message": f"activate term {i}"}))
        
        blocks.append(
            table(
                "Available Terms",
                columns,
                rows,
                actions=[{"label": "Cancel", "type": "query", "payload": {"message": "cancel"}}]
            )
        )
        
        blocks.append(text("**Instructions:**\n• Click on a term to activate it\n• Type 'activate term [number]' (e.g., 'activate term 1')\n• Only PLANNED terms can be activated"))
        
        return ChatResponse(
            response="Select a term to activate",
            intent="term_selection_needed",
            data={
                "available_terms": [
                    {
                        "index": i,
                        "id": str(term[0]),
                        "title": term[1],
                        "year": term[3],
                        "start_date": serialize_date(term[4]),
                        "end_date": serialize_date(term[5])
                    }
                    for i, term in enumerate(available_terms, 1)
                ],
                "context": {
                    "handler": "academic",
                    "flow": "activate_term",
                    "step": "select_term",
                    "available_terms": [
                        {
                            "id": str(term[0]),
                            "title": term[1],
                            "year": term[3]
                        } for term in available_terms
                    ]
                }
            },
            blocks=blocks,
            suggestions=[
                f"Activate term {i}" for i in range(1, min(len(available_terms) + 1, 4))
            ] + ["Cancel"]
        )
    
    def invalid_term_selection(self, available_terms, context):
        """Invalid term selection error"""
        blocks = [
            error_block("Invalid Selection", f"Please select a valid term number (1-{len(available_terms)}) or say 'cancel'."),
            text(f"**Available options:**\n" + "\n".join([f"{i+1}. {term['title']} ({term['year']})" for i, term in enumerate(available_terms)]))
        ]
        
        return ChatResponse(
            response="Please select a valid term number.",
            intent="invalid_term_selection",
            data={"context": context},
            blocks=blocks,
            suggestions=[
                f"Activate term {i}" for i in range(1, min(len(available_terms) + 1, 4))
            ] + ["Cancel"]
        )
    
    def term_activated_success(self, term_info):
        """Term successfully activated"""
        blocks = []
        
        # Success message
        blocks.append(text(f"**Term Activated Successfully!**\n\n**{term_info['title']} ({term_info['year']})** is now the active term for student enrollments."))
        
        # Success KPIs
        success_kpis = [
            {"label": "Active Term", "value": term_info["title"], "variant": "success"},
            {"label": "Academic Year", "value": str(term_info["year"]), "variant": "primary"},
            {"label": "Status", "value": "ACTIVE", "variant": "success"}
        ]
        
        blocks.append(kpis(success_kpis))
        
        # Next steps
        blocks.append(text("**What's Next:**\n• Students can now be enrolled in this term\n• Check enrollment status across your classes\n• Generate invoices for enrolled students\n• Monitor term progress and statistics"))
        
        # Quick action buttons
        action_buttons = [
            button_item("Show Current Term", "query", {"message": "show current term"}, "primary", "md", "calendar"),
            button_item("Enroll Students", "query", {"message": "enroll students"}, "success", "md", "user-plus"),
            button_item("Check Enrollments", "query", {"message": "show enrollment status"}, "outline", "md", "users"),
            button_item("Academic Calendar", "query", {"message": "show academic calendar"}, "secondary", "md", "list")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Successfully activated: {term_info['title']} ({term_info['year']})",
            intent="term_activated",
            data={
                "activated_term": term_info,
                "context": {}
            },
            blocks=blocks,
            suggestions=[
                "Show current term",
                "Check enrollment status",
                "Enroll students",
                "Show class enrollments"
            ]
        )
    
    def activation_failed(self):
        """Term activation failed"""
        return ChatResponse(
            response="Failed to activate term - term not found.",
            intent="term_activation_failed",
            data={"context": {}},
            blocks=[error_block("Activation Failed", "The selected term could not be activated. It may have been deleted or modified.")],
            suggestions=[
                "Show academic calendar",
                "Check available terms"
            ]
        )
    
    def academic_calendar(self, years_data):
        """Display complete academic calendar"""
        blocks = []
        school_name = self.get_school_name()
        
        # Header
        blocks.append(text(f"**Academic Calendar - {school_name}**\n\nComplete overview of your academic years and terms with their current status."))
        
        # Summary statistics
        total_years = len(years_data)
        total_terms = sum(len(year_info["terms"]) for year_info in years_data.values())
        active_terms = sum(1 for year_info in years_data.values() 
                         for term in year_info["terms"] if term["state"] == "ACTIVE")
        planned_terms = sum(1 for year_info in years_data.values() 
                          for term in year_info["terms"] if term["state"] == "PLANNED")
        
        summary_kpis = [
            count_kpi("Academic Years", total_years, "primary"),
            count_kpi("Total Terms", total_terms, "info"),
            count_kpi("Active Terms", active_terms, "success"),
            count_kpi("Planned Terms", planned_terms, "warning")
        ]
        
        blocks.append(kpis(summary_kpis))
        
        # Academic calendar table
        columns = [
            {"key": "year", "label": "Year", "sortable": True, "width": 100},
            {"key": "year_title", "label": "Year Title", "sortable": True},
            {"key": "term_title", "label": "Term", "sortable": True},
            {"key": "period", "label": "Period"},
            status_column("term_state", "Status", {
                "ACTIVE": "success",
                "PLANNED": "warning", 
                "CLOSED": "secondary"
            })
        ]
        
        rows = []
        for year, year_info in sorted(years_data.items(), reverse=True):
            if year_info["terms"]:
                for term in year_info["terms"]:
                    period = ""
                    if term["start_date"] and term["end_date"]:
                        period = f"{term['start_date']} to {term['end_date']}"
                    else:
                        period = "Dates not set"
                    
                    row_data = {
                        "year": str(year),
                        "year_title": year_info["title"],
                        "term_title": term["title"],
                        "period": period,
                        "term_state": term["state"]
                    }
                    
                    # Add action based on term state
                    if term["state"] == "PLANNED":
                        action_message = f"activate term {term['title']}"
                    elif term["state"] == "ACTIVE":
                        action_message = f"show current term details"
                    else:
                        action_message = f"show term {term['title']} details"
                    
                    rows.append(action_row(row_data, "query", {"message": action_message}))
            else:
                # Year with no terms
                row_data = {
                    "year": str(year),
                    "year_title": year_info["title"],
                    "term_title": "No terms created",
                    "period": "-",
                    "term_state": "SETUP_NEEDED"
                }
                rows.append(action_row(row_data, "query", {"message": f"create terms for {year}"}))
        
        table_actions = [
            {"label": "Activate Term", "type": "query", "payload": {"message": "activate term"}},
            {"label": "Create New Year", "type": "query", "payload": {"message": "create new academic year"}},
            {"label": "Show Current Term", "type": "query", "payload": {"message": "show current term"}}
        ]
        
        table_filters = [
            {"type": "select", "key": "term_state", "label": "Status", 
             "options": ["ACTIVE", "PLANNED", "CLOSED"]},
            {"type": "number", "key": "year", "label": "Year"}
        ]
        
        blocks.append(
            table(
                "Academic Calendar",
                columns,
                rows,
                actions=table_actions,
                filters=table_filters,
                pagination={"mode": "client", "pageSize": 15} if len(rows) > 15 else None
            )
        )
        
        # Status overview
        status_items = []
        if active_terms == 1:
            status_items.append(status_item("Active Terms", "ok", f"{active_terms} term active - ready for enrollments"))
        elif active_terms == 0:
            status_items.append(status_item("Active Terms", "warning", "No active term - activate one for enrollments"))
        else:
            status_items.append(status_item("Active Terms", "error", f"{active_terms} active terms - only one should be active"))
        
        if planned_terms > 0:
            status_items.append(status_item("Upcoming Terms", "ok", f"{planned_terms} terms planned for future activation"))
        
        blocks.append(status_block(status_items))
        
        return ChatResponse(
            response=f"Academic calendar: {total_years} years, {total_terms} terms",
            intent="academic_calendar",
            data={"years": years_data, "total_years": total_years, "total_terms": total_terms, "active_terms": active_terms},
            blocks=blocks,
            suggestions=[
                "Show current term",
                "Activate a term",
                "Create new academic year",
                "Academic setup status"
            ]
        )
    
    def no_academic_setup(self):
        """No academic calendar setup"""
        return ChatResponse(
            response="No academic years found.",
            intent="no_academic_setup",
            blocks=[
                empty_state("No Academic Calendar", "Set up your academic calendar with years and terms"),
                text("**Academic Calendar Setup:**\n\n1. **Academic Years** - Create yearly structures (2024, 2025, etc.)\n2. **Academic Terms** - Add terms within each year (Term 1, Term 2, Term 3)\n3. **Activate Terms** - Make terms active for enrollments\n\nThis structure helps organize student enrollments and fee management.")
            ],
            suggestions=[
                "Help me set up academic years",
                "Create new academic year",
                "Bootstrap school setup"
            ]
        )
    
    def setup_status(self, setup: SetupStatus):
        """Academic setup status display"""
        blocks = []
        school_name = self.get_school_name()
        
        # Header
        blocks.append(text(f"**Academic Setup Status - {school_name}**\n\nCurrent status of your academic calendar configuration and setup recommendations."))
        
        # Setup status KPIs
        setup_kpis = [
            count_kpi("Academic Years", setup.year_count, "primary" if setup.year_count > 0 else "warning"),
            count_kpi("Academic Terms", setup.term_count, "primary" if setup.term_count > 0 else "warning"),
            count_kpi("Active Terms", setup.active_terms, "success" if setup.active_terms == 1 else "warning")
        ]
        
        blocks.append(kpis(setup_kpis))
        
        # Setup status and recommendations
        setup_status = []
        next_steps = []
        suggestions = []
        
        if setup.year_count == 0:
            setup_status.append(status_item("Academic Years", "error", "No academic years created"))
            next_steps.extend([
                "1. Create your first academic year (e.g., 2024, 2025)",
                "2. Set up terms within the academic year", 
                "3. Activate the current term for enrollments"
            ])
            suggestions.extend([
                "Bootstrap academic setup",
                "Create academic year manually",
                "Show setup guide"
            ])
        elif setup.term_count == 0:
            setup_status.append(status_item("Academic Years", "ok", f"{setup.year_count} years created"))
            setup_status.append(status_item("Academic Terms", "warning", "No terms created"))
            next_steps.extend([
                "1. Create terms within your academic years",
                "2. Set up term periods (start/end dates)",
                "3. Activate the current term"
            ])
            suggestions.extend([
                "Create terms for current year",
                "Bootstrap academic setup",
                "Show academic years"
            ])
        elif setup.active_terms == 0:
            setup_status.append(status_item("Academic Years", "ok", f"{setup.year_count} years created"))
            setup_status.append(status_item("Academic Terms", "ok", f"{setup.term_count} terms created"))
            setup_status.append(status_item("Active Terms", "warning", "No active term - students cannot be enrolled"))
            next_steps.extend([
                "1. Activate a term for current enrollments",
                "2. Begin student enrollment process",
                "3. Generate invoices and manage fees"
            ])
            suggestions.extend([
                "Show available terms",
                "Activate a term",
                "View academic calendar"
            ])
        elif setup.active_terms == 1:
            setup_status.append(status_item("Academic Years", "ok", f"{setup.year_count} years created"))
            setup_status.append(status_item("Academic Terms", "ok", f"{setup.term_count} terms created"))
            setup_status.append(status_item("Active Terms", "ok", "Perfect! Ready for enrollments"))
            next_steps.extend([
                "Academic setup is complete!",
                "You can now enroll students in the active term",
                "Monitor enrollment progress and generate reports"
            ])
            suggestions.extend([
                "Show current term",
                "Check enrollment status",
                "Enroll students"
            ])
        else:
            setup_status.append(status_item("Academic Years", "ok", f"{setup.year_count} years created"))
            setup_status.append(status_item("Academic Terms", "ok", f"{setup.term_count} terms created"))
            setup_status.append(status_item("Active Terms", "error", f"{setup.active_terms} active terms - only one should be active"))
            next_steps.extend([
                "1. Review active terms and close unnecessary ones",
                "2. Keep only one term active at a time",
                "3. Proceed with enrollments once fixed"
            ])
            suggestions.extend([
                "View academic calendar",
                "Show active terms",
                "Fix term conflicts"
            ])
        
        blocks.append(status_block(setup_status))
        
        # Next steps
        if next_steps:
            blocks.append(text("**Next Steps:**\n" + "\n".join(f"• {step}" for step in next_steps)))
        
        # Quick actions based on status
        action_buttons = []
        
        if setup.year_count == 0:
            action_buttons.extend([
                button_item("Bootstrap Setup", "query", {"message": "bootstrap academic setup"}, "success", "md", "zap"),
                button_item("Manual Setup", "query", {"message": "create academic year manually"}, "outline", "md", "settings")
            ])
        elif setup.active_terms == 0:
            action_buttons.extend([
                button_item("Show Available Terms", "query", {"message": "show available terms"}, "primary", "md", "list"),
                button_item("Activate Term", "query", {"message": "activate term"}, "success", "md", "play")
            ])
        elif setup.active_terms == 1:
            action_buttons.extend([
                button_item("Show Current Term", "query", {"message": "show current term"}, "primary", "md", "calendar"),
                button_item("Enroll Students", "query", {"message": "enroll students"}, "success", "md", "user-plus")
            ])
        else:
            action_buttons.extend([
                button_item("Fix Term Issues", "query", {"message": "view academic calendar"}, "warning", "md", "alert-triangle"),
                button_item("Show Current Terms", "query", {"message": "show active terms"}, "outline", "md", "list")
            ])
        
        action_buttons.append(
            button_item("Academic Calendar", "query", {"message": "show academic calendar"}, "secondary", "md", "calendar")
        )
        
        if action_buttons:
            blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Academic setup status: {setup.year_count} years, {setup.term_count} terms, {setup.active_terms} active",
            intent="academic_setup_guide",
            data={
                "year_count": setup.year_count,
                "term_count": setup.term_count,
                "active_terms": setup.active_terms,
                "setup_complete": setup.setup_complete
            },
            blocks=blocks,
            suggestions=suggestions
        )
    
    def overview(self):
        """General academic overview"""
        blocks = []
        
        blocks.append(text("**Academic Management**\n\nManage your school's academic calendar, years, and terms. Academic terms are required for student enrollments and fee management."))
        
        blocks.append(text("**What you can do:**\n• **View Current Term** - See the active academic term\n• **Academic Calendar** - View all years and terms\n• **Activate Terms** - Switch between academic terms\n• **Setup Guide** - Get help configuring your academic calendar"))
        
        # Quick action buttons
        action_buttons = [
            button_item("Show Current Term", "query", {"message": "show current term"}, "primary", "md", "calendar"),
            button_item("Academic Calendar", "query", {"message": "show academic calendar"}, "outline", "md", "list"),
            button_item("Setup Status", "query", {"message": "academic setup status"}, "secondary", "md", "settings"),
            button_item("Help & Guide", "query", {"message": "academic setup guide"}, "secondary", "md", "help-circle")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response="Academic management system ready",
            intent="academic_general",
            blocks=blocks,
            suggestions=[
                "Show current term",
                "View academic calendar", 
                "Academic setup status",
                "Help with term management"
            ]
        )
    
    def error(self, operation, error_msg):
        """Error response"""
        return ChatResponse(
            response=f"Error {operation}: {error_msg}",
            intent="error",
            blocks=[error_block(f"Error {operation.title()}", error_msg)]
        )