# handlers/general/views.py
from ...blocks import (
    text, kpis, count_kpi, table, status_column, action_row, 
    status_block, status_item, button_group, button_item, 
    action_panel, action_panel_item, empty_state, error_block, chart_xy
)
from ...base import ChatResponse

class GeneralViews:
    """Pure presentation layer for general system responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def greeting_response(self, message: str):
        """Handle greetings and casual interactions"""
        message_lower = message.lower().strip()
        
        # Determine appropriate greeting response
        if any(pattern in message_lower for pattern in ['morning']):
            greeting_response = "Good morning! "
        elif any(pattern in message_lower for pattern in ['afternoon']):
            greeting_response = "Good afternoon! "
        elif any(pattern in message_lower for pattern in ['evening']):
            greeting_response = "Good evening! "
        elif message_lower in ['testing', 'test']:
            greeting_response = "Hello! Everything's working perfectly. "
        else:
            greeting_response = "Hello! "
        
        try:
            school_name = self.get_school_name()
            greeting_response += f"Welcome to your {school_name} management system."
        except:
            greeting_response += "Welcome to your school management system."
        
        blocks = [
            text(f"**Welcome!**\n\n{greeting_response} I'm here to help you manage all aspects of your school operations efficiently."),
            text("**I can help you with:**\n• Student registration and class management\n• Academic calendar and enrollment tracking\n• Fee structures and payment processing\n• School reports and performance analytics\n• Parent communication and notifications"),
            action_panel([
                action_panel_item(
                    "Getting Started",
                    "New to the system? I'll guide you through setup",
                    "play-circle",
                    "Setup Guide",
                    "query",
                    {"message": "getting started guide"}
                ),
                action_panel_item(
                    "School Overview",
                    "See your current school status and metrics",
                    "home",
                    "View Overview",
                    "query",
                    {"message": "school overview"}
                ),
                action_panel_item(
                    "System Capabilities",
                    "Explore everything I can do for your school",
                    "info",
                    "View Capabilities",
                    "query",
                    {"message": "what can you do"}
                ),
                action_panel_item(
                    "Quick Help",
                    "Get help with specific school management tasks",
                    "help-circle",
                    "Get Help",
                    "query",
                    {"message": "help me with school management"}
                )
            ], "How can I help you today?", 2)
        ]
        
        return ChatResponse(
            response=greeting_response,
            intent="greeting",
            blocks=blocks,
            suggestions=[
                "Getting started guide",
                "School overview",
                "What can you do",
                "List all students",
                "Show academic calendar",
                "Help me get started"
            ]
        )
    
    def school_registration_complete(self, school_name: str, system_status: dict):
        """Show school registration status with setup actions"""
        blocks = [
            text(f"**Your School Account: {school_name}**\n\nYour school is already registered and active in the system! All your school information is properly configured and you can immediately start using all the management features."),
            
            text("**Current School Status:**\n• ✅ **School Account** - Active and operational\n• ✅ **User Access** - You have full administrative access\n• ✅ **System Ready** - All features available for immediate use"),
            
            text("**What You Can Do Right Now:**\nWith your school already registered, you can immediately begin setting up and managing your school operations:")
        ]
        
        # Setup actions based on system status
        setup_actions = []
        
        if system_status['academic_years'] == 0:
            setup_actions.append(
                action_panel_item(
                    "🔴 Create Academic Calendar",
                    "Set up academic years and terms - the foundation for all school operations",
                    "calendar",
                    "Create Academic Year",
                    "query",
                    {"message": "create academic year"},
                    "primary"
                )
            )
        
        if system_status['grades'] == 0:
            setup_actions.append(
                action_panel_item(
                    "🔴 Set Up Grade Levels", 
                    "Configure CBC grade levels to organize your school structure",
                    "layers",
                    "Create Grades",
                    "query",
                    {"message": "create new grade"},
                    "primary"
                )
            )
        
        if system_status['students'] == 0:
            setup_actions.append(
                action_panel_item(
                    "🟡 Register Students",
                    "Add your first students with guardian information",
                    "user-plus",
                    "Add Students",
                    "query",
                    {"message": "create new student"},
                    "warning"
                )
            )
        
        if not setup_actions:
            # School is fully set up
            setup_actions = [
                action_panel_item(
                    "📊 School Overview",
                    "View your complete school status and metrics",
                    "home",
                    "View Overview",
                    "query",
                    {"message": "school overview"},
                    "success"
                ),
                action_panel_item(
                    "👥 Manage Students",
                    "View and manage your student directory",
                    "users",
                    "View Students",
                    "query",
                    {"message": "list all students"},
                    "info"
                )
            ]
        
        blocks.append(action_panel(setup_actions, "Next Steps for Your School", 1))
        
        blocks.extend([
            text("**School Account Information:**\n• Your school registration is complete and verified\n• All administrative features are enabled\n• You can begin immediate operations like student registration, class creation, and fee management\n• The system is ready for full academic year management"),
            
            text("**Need Help Getting Started?**\nIf you're new to the system, I recommend starting with the setup guide which will walk you through creating your academic structure, adding students, and configuring your school operations.")
        ])
        
        # Action buttons
        action_buttons = [
            button_item("Getting Started Guide", "query", {"message": "getting started guide"}, "primary", "md", "play-circle"),
            button_item("School Overview", "query", {"message": "school overview"}, "outline", "md", "home"),
            button_item("System Capabilities", "query", {"message": "what can you do"}, "outline", "md", "info")
        ]
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response=f"Your school '{school_name}' is already registered and ready for use!",
            intent="school_registration_complete",
            data={
                "school_name": school_name,
                "registration_status": "complete",
                "account_active": True
            },
            blocks=blocks,
            suggestions=[
                "Getting started guide",
                "School overview",
                "What can you do",
                "Create academic year",
                "Create new student",
                "Help me get started"
            ]
        )
    
    def getting_started_guide(self, system_status: dict):
        """Complete getting started guide with system assessment"""
        blocks = []
        school_name = self.get_school_name()
        
        blocks.append(text(f"**Getting Started with {school_name}**\n\nWelcome! Let me help you set up your school management system step by step. I'll guide you through the essential components needed to get your school running smoothly."))
        
        # System readiness assessment
        setup_status = []
        next_steps = []
        priority_level = "success"
        
        # Academic Calendar Check
        if system_status['academic_years'] == 0:
            setup_status.append(status_item("Academic Calendar", "error", "No academic years created"))
            next_steps.append("Create your first academic year and terms")
            priority_level = "error"
        elif system_status['active_terms'] == 0:
            setup_status.append(status_item("Academic Calendar", "warning", "No active term"))
            next_steps.append("Activate an academic term for enrollments")
            if priority_level == "success":
                priority_level = "warning"
        else:
            setup_status.append(status_item("Academic Calendar", "ok", f"Active term ready"))
        
        # Grade Levels Check
        if system_status['grades'] == 0:
            setup_status.append(status_item("Grade Levels", "error", "No grades created"))
            next_steps.append("Set up academic grade levels (PP1, Grade 1, etc.)")
            priority_level = "error"
        else:
            setup_status.append(status_item("Grade Levels", "ok", f"{system_status['grades']} grades configured"))
        
        # Classes Check
        if system_status['classes'] == 0:
            setup_status.append(status_item("Classes", "error", "No classes created"))
            next_steps.append("Create classes for your grade levels")
            priority_level = "error"
        else:
            setup_status.append(status_item("Classes", "ok", f"{system_status['classes']} classes created"))
        
        # Students Check
        if system_status['students'] == 0:
            setup_status.append(status_item("Students", "warning", "No students registered"))
            next_steps.append("Add your first students with guardian information")
            if priority_level == "success":
                priority_level = "warning"
        else:
            setup_status.append(status_item("Students", "ok", f"{system_status['students']} students registered"))
        
        # System Status Summary
        setup_progress = 4 - len([item for item in setup_status if item["state"] in ["error", "warning"]])
        progress_kpis = [
            count_kpi("Setup Complete", f"{setup_progress}/4", "success" if setup_progress == 4 else "warning"),
            count_kpi("Students", system_status['students'], "success" if system_status['students'] > 0 else "info"),
            count_kpi("Classes", system_status['classes'], "success" if system_status['classes'] > 0 else "info"),
            count_kpi("Active Terms", system_status['active_terms'], "success" if system_status['active_terms'] > 0 else "warning")
        ]
        
        blocks.append(kpis(progress_kpis))
        blocks.append(status_block(setup_status))
        
        # Setup actions based on system state
        if not next_steps:
            # System is set up, show operational guidance
            blocks.append(text("**🎉 Your system is ready!** All basic components are configured. Here are the key operations you can now perform:"))
            
            operational_actions = [
                action_panel_item(
                    "Student Enrollment",
                    "Enroll students in the current academic term to create official records",
                    "users",
                    "Check Enrollment Status",
                    "query",
                    {"message": "show enrollment status"},
                    "primary"
                ),
                action_panel_item(
                    "Generate Invoices", 
                    "Create invoices for enrolled students based on fee structures",
                    "file-plus",
                    "Generate Invoices",
                    "query",
                    {"message": "generate invoices for all students"},
                    "primary"
                ),
                action_panel_item(
                    "Payment Processing",
                    "Record payments and track outstanding balances",
                    "credit-card",
                    "Show Pending Payments",
                    "query", 
                    {"message": "show pending payments"},
                    "primary"
                ),
                action_panel_item(
                    "Reports & Analytics",
                    "View school performance and financial summaries",
                    "bar-chart",
                    "School Overview",
                    "query",
                    {"message": "school overview"},
                    "primary"
                )
            ]
            
            blocks.append(action_panel(operational_actions, "Ready for Operations", 2))
        else:
            # Show setup steps with priority
            blocks.append(text("**Setup Required**\n\nYour school management system needs a few essential components configured before you can begin operations."))
            
            setup_actions = []
            
            # Academic Calendar Setup
            if system_status['academic_years'] == 0:
                setup_actions.append(
                    action_panel_item(
                        "🔴 Academic Calendar",
                        "Create academic years and terms - This is the foundation for everything else",
                        "calendar",
                        "Setup Academic Calendar", 
                        "query",
                        {"message": "create academic year"},
                        "danger"
                    )
                )
            
            # Grade Levels Setup
            if system_status['grades'] == 0:
                setup_actions.append(
                    action_panel_item(
                        "🔴 Grade Levels",
                        "Set up CBC grade levels (PP1, PP2, Grade 1-9, etc.) to organize your school",
                        "layers",
                        "Create Grade Levels",
                        "query", 
                        {"message": "create new grade"},
                        "danger"
                    )
                )
            
            # Classes Setup
            if system_status['classes'] == 0 and system_status['grades'] > 0:
                setup_actions.append(
                    action_panel_item(
                        "🔴 Create Classes",
                        "Add classes for each grade level to organize students into manageable groups",
                        "school",
                        "Create First Class",
                        "query",
                        {"message": "create new class"},
                        "danger"
                    )
                )
            
            # Student Registration
            if system_status['students'] == 0 and system_status['classes'] > 0:
                setup_actions.append(
                    action_panel_item(
                        "🟡 Student Registration",
                        "Register your first students with complete guardian information",
                        "user-plus",
                        "Add First Student",
                        "query",
                        {"message": "create new student"},
                        "warning"
                    )
                )
            
            blocks.append(action_panel(setup_actions, "Setup Actions", 1))
        
        # Quick action buttons
        action_buttons = []
        
        if not next_steps:
            action_buttons.append(
                button_item("School Overview", "query", {"message": "school overview"}, "primary", "md", "home")
            )
        elif system_status['academic_years'] == 0:
            action_buttons.append(
                button_item("Create Academic Year", "query", {"message": "create academic year"}, "primary", "md", "calendar")
            )
        elif system_status['grades'] == 0:
            action_buttons.append(
                button_item("Create Grade Levels", "query", {"message": "create new grade"}, "primary", "md", "layers")
            )
        elif system_status['classes'] == 0:
            action_buttons.append(
                button_item("Create First Class", "query", {"message": "create new class"}, "primary", "md", "school")
            )
        else:
            action_buttons.append(
                button_item("Add Students", "query", {"message": "create new student"}, "primary", "md", "user-plus")
            )
        
        action_buttons.extend([
            button_item("System Capabilities", "query", {"message": "what can you do"}, "outline", "md", "info"),
            button_item("Help Guide", "query", {"message": "help me with school management"}, "outline", "md", "help-circle")
        ])
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        # Build suggestions based on system state
        suggestions = []
        if next_steps:
            if system_status['academic_years'] == 0:
                suggestions.extend(["Create academic year", "Setup academic calendar"])
            elif system_status['grades'] == 0:
                suggestions.extend(["Create grade levels", "Create new grade"])
            elif system_status['classes'] == 0:
                suggestions.extend(["Create new class", "Create first class"])
            elif system_status['students'] == 0:
                suggestions.extend(["Add first student", "Create new student"])
        else:
            suggestions.extend([
                "School overview",
                "Check enrollment status", 
                "Generate invoices"
            ])
        
        suggestions.extend(["System capabilities", "Help guide"])
        
        return ChatResponse(
            response=f"Welcome! Let me help you set up your school management system.",
            intent="getting_started_guide",
            data={
                "system_status": system_status,
                "setup_complete": len(next_steps) == 0,
                "next_steps": next_steps,
                "setup_progress": setup_progress,
                "priority_level": priority_level
            },
            blocks=blocks,
            suggestions=suggestions[:6]
        )
    
    def system_capabilities(self, usage_stats: dict):
        """Show comprehensive system capabilities"""
        blocks = []
        
        blocks.append(text("**School Management System Capabilities**\n\nThis comprehensive system helps you manage all aspects of your school operations. Here's what I can help you accomplish:"))
        
        # Core capabilities organized by functional domain
        capability_sections = [
            {
                "title": "Student Management",
                "description": "Complete student lifecycle management from registration to graduation",
                "items": [
                    action_panel_item(
                        "Student Registration",
                        "Register new students with complete guardian information, medical records, and academic history",
                        "user-plus",
                        "Create Student",
                        "query",
                        {"message": "create new student"},
                        "primary"
                    ),
                    action_panel_item(
                        "Student Directory",
                        "View, search, filter, and manage all registered students with advanced filtering options",
                        "users",
                        "List Students",
                        "query",
                        {"message": "list all students"},
                        "primary"
                    )
                ]
            },
            {
                "title": "Academic Management", 
                "description": "Structure your academic programs with terms, grades, and classes",
                "items": [
                    action_panel_item(
                        "Academic Calendar",
                        "Set up academic years, terms, holidays, and manage the complete school calendar",
                        "calendar",
                        "Academic Calendar",
                        "query",
                        {"message": "show academic calendar"},
                        "primary"
                    ),
                    action_panel_item(
                        "Grade Level Configuration",
                        "Configure CBC grade levels, educational groupings, and progression pathways",
                        "layers",
                        "Show Grades",
                        "query",
                        {"message": "list grades"},
                        "primary"
                    )
                ]
            },
            {
                "title": "Financial Management",
                "description": "Comprehensive fee management, invoicing, and payment tracking",
                "items": [
                    action_panel_item(
                        "Fee Structure Design",
                        "Create flexible fee structures by grade, term, and fee categories (tuition, activities, meals)",
                        "dollar-sign",
                        "Show Fees",
                        "query",
                        {"message": "show fee structures"},
                        "primary"
                    ),
                    action_panel_item(
                        "Invoice Generation",
                        "Auto-generate invoices for students based on their grade and enrollment status",
                        "file-plus",
                        "Generate Invoices",
                        "query",
                        {"message": "generate invoices for all students"},
                        "primary"
                    )
                ]
            }
        ]
        
        # Display each capability section
        for section in capability_sections:
            blocks.append(text(f"**{section['title']}**\n{section['description']}"))
            blocks.append(action_panel(section['items'], columns=2))
        
        # Usage statistics if available
        if any(stat > 0 for stat in usage_stats.values()):
            stats_kpis = [
                count_kpi("Students Managed", usage_stats['students'], "primary"),
                count_kpi("Classes Created", usage_stats['classes'], "info"),
                count_kpi("Invoices Generated", usage_stats['invoices'], "success"),
                count_kpi("Payments Processed", usage_stats['payments'], "success")
            ]
            
            blocks.append(text("**Your System Usage**"))
            blocks.append(kpis(stats_kpis))
        
        # Quick access buttons
        quick_access_buttons = [
            button_item("Getting Started Guide", "query", {"message": "getting started guide"}, "primary", "md", "play-circle"),
            button_item("School Overview", "query", {"message": "school overview"}, "outline", "md", "home"),
            button_item("Help & Support", "query", {"message": "help me with school management"}, "outline", "md", "help-circle")
        ]
        
        blocks.append(button_group(quick_access_buttons, "horizontal", "center"))
        
        return ChatResponse(
            response="Here are all the capabilities of your school management system",
            intent="system_capabilities",
            blocks=blocks,
            suggestions=[
                "Getting started guide",
                "School overview", 
                "Create new student",
                "Show academic calendar",
                "Help with school management"
            ]
        )
    
    def help_request(self, detected_topic=None):
        """Comprehensive help system"""
        blocks = []
        
        blocks.append(text("**How Can I Help You?**\n\nI'm here to assist you with managing your school effectively. Let me know what specific area you'd like help with, or choose from the topics below."))
        
        help_sections = [
            {
                "title": "Getting Started",
                "items": [
                    action_panel_item(
                        "New User Setup",
                        "Complete system setup guide for first-time users",
                        "play-circle",
                        "Getting Started Guide",
                        "query",
                        {"message": "getting started guide"},
                        "primary"
                    ),
                    action_panel_item(
                        "Quick Start Checklist",
                        "Essential steps to get your school system operational",
                        "check-square",
                        "Quick Start",
                        "query",
                        {"message": "what should i do next"},
                        "primary"
                    )
                ]
            },
            {
                "title": "Core Functions",
                "items": [
                    action_panel_item(
                        "Student Management",
                        "Register students, manage guardians, and handle class assignments",
                        "users",
                        "Student Help",
                        "query",
                        {"message": "help me with students"},
                        "info"
                    ),
                    action_panel_item(
                        "Academic Structure",
                        "Set up terms, grades, classes, and enrollment processes",
                        "calendar",
                        "Academic Help",
                        "query",
                        {"message": "help me with academic setup"},
                        "info"
                    ),
                    action_panel_item(
                        "Financial Operations",
                        "Configure fees, generate invoices, and process payments",
                        "dollar-sign",
                        "Financial Help",
                        "query",
                        {"message": "help me with payments and fees"},
                        "info"
                    )
                ]
            }
        ]
        
        # Display help sections
        for section in help_sections:
            blocks.append(text(f"**{section['title']}**"))
            blocks.append(action_panel(section['items'], columns=2))
        
        # FAQ table
        blocks.append(text("**Frequently Asked Questions**"))
        
        faq_columns = [
            {"key": "question", "label": "Question", "sortable": True},
            {"key": "category", "label": "Category", "sortable": True}
        ]
        
        faq_rows = [
            action_row({
                "question": "How do I add my first student?",
                "category": "Student Management"
            }, "query", {"message": "create new student"}),
            action_row({
                "question": "How do I set up academic terms?",
                "category": "Academic Setup"
            }, "query", {"message": "create academic year"}),
            action_row({
                "question": "How do I generate invoices?",
                "category": "Financial Management"
            }, "query", {"message": "generate invoices for all students"})
        ]
        
        blocks.append(table("Common Questions", faq_columns, faq_rows))
        
        # Quick action buttons
        help_buttons = [
            button_item("Getting Started", "query", {"message": "getting started guide"}, "primary", "md", "play-circle"),
            button_item("System Status", "query", {"message": "school overview"}, "outline", "md", "check-circle"),
            button_item("What Can You Do", "query", {"message": "what can you do"}, "outline", "md", "help-circle")
        ]
        
        blocks.append(button_group(help_buttons, "horizontal", "center"))
        
        suggestions = [
            "Getting started guide",
            "What can you do",
            "Help me with students", 
            "Help me with academic setup",
            "Troubleshooting help"
        ]
        
        return ChatResponse(
            response="I'm here to help you with your school management system",
            intent="help_request",
            blocks=blocks,
            suggestions=suggestions
        )
    
    def next_steps_guidance(self, system_status: dict, critical_issues: list, recommended_actions: list):
        """Guide users on what to do next"""
        blocks = []
        blocks.append(text("**What Should You Do Next?**\n\nBased on your current system setup and data, here are the recommended next steps prioritized by importance and impact."))
        
        # Display critical issues first
        if critical_issues:
            blocks.append(text("**Critical Setup Required**\n\nThese items must be completed before your school system can function properly:"))
            
            critical_items = []
            for issue in critical_issues:
                critical_items.append(
                    action_panel_item(
                        issue['title'],
                        f"{issue['description']}\n\n**Impact:** {issue['impact']}\n**Time:** {issue['estimated_time']}",
                        "alert-circle",
                        issue['action'],
                        "query",
                        {"message": issue['message']},
                        "danger"
                    )
                )
            
            blocks.append(action_panel(critical_items, columns=1))
        
        # Display recommended actions
        if recommended_actions:
            blocks.append(text("**Recommended Next Steps**\n\nComplete these to fully utilize your school management system:"))
            
            recommended_items = []
            for action in recommended_actions:
                recommended_items.append(
                    action_panel_item(
                        action['title'],
                        f"{action['description']}\n\n**Impact:** {action['impact']}\n**Time:** {action['estimated_time']}",
                        "arrow-right",
                        action['action'],
                        "query", 
                        {"message": action['message']},
                        "warning"
                    )
                )
            
            blocks.append(action_panel(recommended_items, columns=1))
        
        # System is operational
        if not critical_issues and not recommended_actions:
            blocks.append(text("**System Fully Operational**\n\nAll core components are configured and your school management system is ready for daily operations!"))
            
            operational_kpis = [
                count_kpi("Students", system_status['students'], "success"),
                count_kpi("Classes", system_status['classes'], "success"), 
                count_kpi("Active Terms", system_status['active_terms'], "success"),
                count_kpi("Grade Levels", system_status['grades'], "success")
            ]
            
            blocks.append(kpis(operational_kpis))
        
        # Quick action buttons
        action_buttons = []
        
        if critical_issues:
            first_critical = critical_issues[0]
            action_buttons.append(
                button_item(first_critical['action'], "query", {"message": first_critical['message']}, "primary", "md", "alert-circle")
            )
        elif recommended_actions:
            first_recommended = recommended_actions[0]
            action_buttons.append(
                button_item(first_recommended['action'], "query", {"message": first_recommended['message']}, "primary", "md", "arrow-right")
            )
        else:
            action_buttons.append(
                button_item("School Overview", "query", {"message": "school overview"}, "primary", "md", "home")
            )
        
        action_buttons.extend([
            button_item("System Status", "query", {"message": "school overview"}, "outline", "md", "check-circle"),
            button_item("Getting Started Guide", "query", {"message": "getting started guide"}, "outline", "md", "book-open")
        ])
        
        blocks.append(button_group(action_buttons, "horizontal", "center"))
        
        # Build suggestions
        suggestions = []
        all_actions = critical_issues + recommended_actions
        
        for action in all_actions[:4]:
            suggestions.append(action['action'])
        
        suggestions.extend(["School overview", "Getting started guide"])
        
        return ChatResponse(
            response="Here are your recommended next steps based on current system status",
            intent="next_steps_guidance",
            data={
                "system_status": system_status,
                "critical_issues": len(critical_issues),
                "recommended_actions": len(recommended_actions),
                "system_operational": len(critical_issues) == 0 and len(recommended_actions) == 0
            },
            blocks=blocks,
            suggestions=suggestions[:6]
        )
    
    def general_assistance(self):
        """Default general assistance response"""
        blocks = [
            text("**School Management Assistant**\n\nI'm here to help you manage all aspects of your school operations efficiently and effectively."),
            text("**I Can Help You With:**\n• Student registration and class assignments\n• Academic calendar and enrollment management\n• Fee structures and payment processing\n• Parent communication and notifications\n• Reports and school performance analytics"),
            action_panel([
                action_panel_item(
                    "Get Started",
                    "New to the system? I'll guide you through setup",
                    "play-circle",
                    "Getting Started",
                    "query",
                    {"message": "getting started guide"}
                ),
                action_panel_item(
                    "System Capabilities",
                    "See everything the system can do for your school",
                    "list",
                    "View Capabilities",
                    "query",
                    {"message": "what can you do"}
                ),
                action_panel_item(
                    "School Status",
                    "Check your current school setup and performance",
                    "activity",
                    "School Overview",
                    "query",
                    {"message": "school overview"}
                ),
                action_panel_item(
                    "Get Help",
                    "Find specific help for any area of school management",
                    "help-circle",
                    "Help Guide",
                    "query",
                    {"message": "help me with school management"}
                )
            ], "How Can I Help?", 2)
        ]
        
        return ChatResponse(
            response="I'm here to help you manage your school effectively!",
            intent="general_assistance",
            blocks=blocks,
            suggestions=[
                "Getting started guide",
                "What can you do", 
                "School overview",
                "Help me with school management"
            ]
        )
    
    def error(self, operation, error_msg):
        """Error response"""
        return ChatResponse(
            response=f"Error {operation}: {error_msg}",
            intent="error",
            blocks=[error_block(f"Error {operation.title()}", error_msg)]
        )