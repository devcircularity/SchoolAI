# handlers/class/views.py
from ...blocks import (
    text, kpis, count_kpi, table, status_column, action_row, 
    chart_xy, chart_pie, empty_state, error_block, button_group, button_item
)
from ...base import ChatResponse
from .dataclasses import ClassRow, ClassDetailRow, GradeRow, determine_grade_group, format_class_display_name

class ClassViews:
    """Pure presentation layer for class responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def no_classes_found(self):
        """Handle case where no classes are found"""
        return ChatResponse(
            response="No classes found in your school.",
            intent="no_classes",
            blocks=[
                empty_state("No Classes Found", "Create classes to organize your students by grade and section"),
                text("Classes group students by grade level and section. Each class belongs to a specific grade and can have its own teacher assignments."),
                text("**Getting Started:**\n1. Ensure you have grades set up\n2. Create classes within those grades\n3. Assign students to classes")
            ],
            suggestions=[
                "Create new class",
                "Setup grades first",
                "Bootstrap school setup",
                "Show grades"
            ]
        )
    
    def no_grades_found(self):
        """Handle case where no grades are found"""
        return ChatResponse(
            response="No grades found in your school.",
            intent="no_grades",
            blocks=[
                empty_state("No Grades Found", "Create grades to organize your classes by academic levels"),
                text("Grades help you organize classes by academic level (like Grade 1, PP1, Form 1, etc.). Each grade can have multiple classes and its own fee structure."),
                text("**Getting Started:**\n• Create individual grades manually\n• Use CBC system setup for Kenyan schools\n• Import from existing grade structure")
            ],
            suggestions=[
                "Create new grade",
                "Setup CBC grades", 
                "Bootstrap school setup",
                "Import grades"
            ]
        )
    
    def list_classes_table(self, classes):
        """Rich table display for class list"""
        blocks = []
        
        # Header
        school_name = self.get_school_name()
        blocks.append(text(f"**Classes - {school_name}**\n\nComplete directory of classes organized by grade groups and academic years."))
        
        # Summary statistics
        total_classes = len(classes)
        total_students = sum(cls.student_count for cls in classes)
        active_students = sum(cls.active_students for cls in classes)
        empty_classes = sum(1 for cls in classes if cls.student_count == 0)
        
        kpi_items = [
            count_kpi("Total Classes", total_classes, "primary"),
            count_kpi("Total Students", total_students, "success"),
            count_kpi("Active Students", active_students, "info")
        ]
        
        if empty_classes > 0:
            kpi_items.append(
                count_kpi("Empty Classes", empty_classes, "warning",
                         action={"type": "query", "payload": {"message": "show empty classes"}})
            )
        
        blocks.append(kpis(kpi_items))
        
        # Classes table
        blocks.append(self._create_classes_table(classes))
        
        # Class distribution charts
        classes_by_group = self._group_classes_by_grade(classes)
        if len(classes_by_group) > 1:
            blocks.append(self._create_classes_chart(classes_by_group))
        
        return ChatResponse(
            response=f"Found {total_classes} classes with {total_students} students",
            intent="class_list",
            data={
                "total_classes": total_classes,
                "total_students": total_students,
                "active_students": active_students,
                "empty_classes": empty_classes,
                "classes_by_group": {group: len(classes) for group, classes in classes_by_group.items()}
            },
            blocks=blocks,
            suggestions=[
                "Create new class",
                "Show empty classes",
                "Show grades",
                "Assign students to classes"
            ]
        )
    
    def class_details(self, class_detail, multiple_matches=False, total_matches=1, searched_name=""):
        """Format detailed class information"""
        blocks = []
        
        # Header with class name
        full_class_name = format_class_display_name(class_detail.name, class_detail.stream)
        
        header_text = f"**{full_class_name} - Class Details**\n\nComplete information about this class including enrollment, demographics, and academic details."
        
        if multiple_matches:
            header_text += f"\n\n*Note: Found {total_matches} classes matching '{searched_name}'. Showing details for '{class_detail.name}'.*"
        
        blocks.append(text(header_text))
        
        # Key metrics
        status = "Active" if class_detail.active_students > 0 else "Empty"
        status_variant = "success" if class_detail.active_students > 0 else "warning"
        
        kpi_items = [
            count_kpi("Total Students", class_detail.total_students, "primary"),
            count_kpi("Active Students", class_detail.active_students, "success"),
            count_kpi("Status", status, status_variant)
        ]
        
        # Add gender breakdown if we have active students
        if class_detail.active_students > 0:
            kpi_items.extend([
                count_kpi("Male", class_detail.male_students, "info"),
                count_kpi("Female", class_detail.female_students, "info")
            ])
        
        blocks.append(kpis(kpi_items))
        
        # Class information table
        info_rows = [
            {"property": "Class Name", "value": class_detail.name},
            {"property": "Grade Level", "value": class_detail.level},
            {"property": "Academic Year", "value": str(class_detail.academic_year)},
            {"property": "Stream", "value": class_detail.stream if class_detail.stream else "None"},
            {"property": "Created", "value": class_detail.created_at.strftime("%B %d, %Y") if class_detail.created_at else "Unknown"}
        ]
        
        blocks.append(
            table(
                "Class Information",
                [
                    {"key": "property", "label": "Property", "sortable": False},
                    {"key": "value", "label": "Value", "sortable": False}
                ],
                [action_row(row, "copy", {"text": row["value"]}) for row in info_rows]
            )
        )
        
        # Quick actions
        action_suggestions = []
        if class_detail.active_students == 0:
            action_suggestions.extend([
                f"Assign students to {class_detail.name}",
                "Show unassigned students"
            ])
        else:
            action_suggestions.extend([
                f"Add more students to {class_detail.name}",
                f"Show {class_detail.name} attendance"
            ])
        
        action_suggestions.extend([
            "List all classes",
            f"Show {class_detail.level} classes",
            "Class statistics"
        ])
        
        return ChatResponse(
            response=f"Class details for {class_detail.name}: {class_detail.active_students} active students out of {class_detail.total_students} total",
            intent="class_details",
            data={
                "class_id": class_detail.id,
                "class_name": class_detail.name,
                "level": class_detail.level,
                "academic_year": class_detail.academic_year,
                "stream": class_detail.stream,
                "total_students": class_detail.total_students,
                "active_students": class_detail.active_students,
                "male_students": class_detail.male_students,
                "female_students": class_detail.female_students,
                "status": status
            },
            blocks=blocks,
            suggestions=action_suggestions
        )
    
    def class_not_found(self, class_name):
        """Handle case where requested class is not found"""
        return ChatResponse(
            response=f"No class found matching '{class_name}'. Please check the class name and try again.",
            intent="class_not_found",
            blocks=[
                text(f"**Class Not Found: '{class_name}'**\n\nI couldn't find a class with that name in your school."),
                text("**Suggestions:**\n• Check the spelling of the class name\n• Try using just part of the name\n• View all classes to see available options"),
                text("**Examples of Valid Requests:**\n• Show class 10 A details\n• View Grade 2 Blue info\n• Class Form 1 East details")
            ],
            suggestions=[
                "List all classes",
                "Show empty classes", 
                "Create new class",
                f"Search for {class_name.split()[0] if class_name.split() else class_name}"
            ]
        )
    
    def class_details_missing_name(self):
        """Handle case where user requests class details but doesn't specify which class"""
        return ChatResponse(
            response="Please specify which class you'd like to see details for.",
            intent="class_details_missing_name",
            blocks=[
                text("**Which Class?**\n\nTo show class details, please specify the class name."),
                text("**Examples:**\n• Show class 10 A details\n• View Grade 2 Blue info\n• Class Form 1 East details")
            ],
            suggestions=[
                "List all classes", 
                "Show class 10 A details", 
                "Show Grade 2 Blue details",
                "Class statistics"
            ]
        )
    
    def list_grades_table(self, grades, grade_class_counts):
        """Rich table display for grades list"""
        blocks = []
        
        # Header
        school_name = self.get_school_name()
        blocks.append(text(f"**Academic Grades - {school_name}**\n\nAll grade levels available in your school with their associated classes."))
        
        # Summary KPIs
        total_grades = len(grades)
        total_classes = sum(grade_class_counts.values())
        grades_with_classes = sum(1 for count in grade_class_counts.values() if count > 0)
        
        kpi_items = [
            count_kpi("Total Grades", total_grades, "primary"),
            count_kpi("With Classes", grades_with_classes, "success"),
            count_kpi("Total Classes", total_classes, "info")
        ]
        
        if grades_with_classes < total_grades:
            kpi_items.append(
                count_kpi("Without Classes", total_grades - grades_with_classes, "warning",
                         action={"type": "query", "payload": {"message": "show grades without classes"}})
            )
        
        blocks.append(kpis(kpi_items))
        
        # Grades table
        blocks.append(self._create_grades_table(grades, grade_class_counts))
        
        # Grade distribution chart if we have multiple groups
        grades_by_group = self._group_grades_by_group(grades)
        if len(grades_by_group) > 1:
            blocks.append(self._create_grades_chart(grades_by_group))
        
        return ChatResponse(
            response=f"Found {total_grades} grades across {len(grades_by_group)} groups",
            intent="grade_list",
            data={
                "grades": [{"id": g.id, "label": g.label, "group_name": g.group_name} for g in grades],
                "class_counts": grade_class_counts,
                "total_grades": total_grades,
                "total_classes": total_classes
            },
            blocks=blocks,
            suggestions=[
                "Create new grade",
                "Create new class",
                "List all classes",
                "Show fee structures"
            ]
        )
    
    def empty_classes_list(self, empty_classes):
        """Show empty classes with blocks"""
        if not empty_classes:
            return ChatResponse(
                response="All classes have students assigned to them.",
                intent="no_empty_classes",
                blocks=[
                    text("**All Classes Have Students!**\n\nEvery class in your school has students assigned to it. This shows good enrollment management."),
                    text("You can continue creating more classes or check enrollment statistics."),
                    text("**What's Next:**\n• Create additional classes if needed\n• Review class capacity and distribution\n• Monitor enrollment trends")
                ],
                suggestions=[
                    "List all classes",
                    "Show enrollment status",
                    "Create new class",
                    "Class statistics"
                ]
            )
        
        blocks = []
        
        # Header
        blocks.append(text(f"**Empty Classes ({len(empty_classes)})**\n\nClasses without any active students assigned. Consider assigning students or removing unused classes."))
        
        # Summary KPI
        blocks.append(kpis([
            count_kpi("Empty Classes", len(empty_classes), "warning")
        ]))
        
        # Empty classes table
        blocks.append(self._create_empty_classes_table(empty_classes))
        
        # Action suggestions
        blocks.append(text("**Next Steps:**\n• Assign existing students to these classes\n• Check if you have unassigned students\n• Remove classes that are no longer needed"))
        
        # Group by grade for summary
        empty_by_group = self._group_empty_classes_by_grade(empty_classes)
        
        return ChatResponse(
            response=f"Found {len(empty_classes)} empty classes that need student assignments",
            intent="empty_classes",
            data={
                "empty_classes": [
                    {
                        "id": str(cls.id),
                        "name": cls.name,
                        "level": cls.level,
                        "academic_year": cls.academic_year,
                        "stream": cls.stream,
                        "group_name": determine_grade_group(cls.level)
                    }
                    for cls in empty_classes
                ],
                "count": len(empty_classes),
                "empty_by_group": {group: len(classes) for group, classes in empty_by_group.items()}
            },
            blocks=blocks,
            suggestions=[
                "Show unassigned students",
                "Assign students to classes",
                "Create new class",
                "List all classes"
            ]
        )
    
    def class_statistics(self, stats):
        """Build comprehensive class statistics response"""
        blocks = []
        
        # Header
        school_name = self.get_school_name()
        blocks.append(text(f"**Class Statistics - {school_name}**\n\nDetailed breakdown of class distribution and utilization across your school."))
        
        # Main KPIs
        kpi_items = [
            count_kpi("Total Classes", stats["total"], "primary"),
            count_kpi("With Students", stats["active"], "success"),
            count_kpi("Empty Classes", stats["empty"], "warning" if stats["empty"] > 0 else "success")
        ]
        
        blocks.append(kpis(kpi_items))
        
        # Level breakdown table
        if stats["by_level"]:
            blocks.append(self._create_class_statistics_table(stats["by_level"]))
        
        # Utilization chart
        if stats["total"] > 0:
            blocks.append(self._create_class_utilization_chart(stats["active"], stats["empty"]))
        
        suggestions = ["List all classes", "Show grades"]
        if stats["empty"] > 0:
            suggestions.insert(0, "Show empty classes")
        if stats["total"] > 0:
            suggestions.append("Create new class")
        
        return ChatResponse(
            response=f"Class statistics: {stats['total']} total classes, {stats['active']} with students, {stats['empty']} empty",
            intent="class_count",
            data=stats,
            blocks=blocks,
            suggestions=suggestions
        )
    
    def overview(self, stats):
        """General class overview with blocks"""
        blocks = []
        
        # Header
        blocks.append(text("**Class & Grade Management**\n\nManage classes and academic grades in your school. Classes organize students by grade level and section."))
        
        # Show overview based on current state
        if stats['total_classes'] > 0 or stats['total_grades'] > 0:
            blocks.append(self._create_overview_kpis(stats))
        
        # Explanatory content based on setup state
        blocks.append(self._create_overview_guidance(stats))
        
        # Quick action cards if we have data
        if stats['total_classes'] > 0:
            blocks.append(self._create_quick_actions_table(stats))
        
        suggestions = self._get_overview_suggestions(stats)
        
        return ChatResponse(
            response="Class & Grade Management System ready",
            intent="class_system_overview",
            data=stats,
            blocks=blocks,
            suggestions=suggestions
        )
    
    def error(self, operation, error_msg):
        """Error response"""
        return ChatResponse(
            response=f"Error {operation}: {error_msg}",
            intent="error",
            blocks=[error_block(f"Error {operation.title()}", error_msg)]
        )
    
    # Helper methods for building UI components
    def _create_classes_table(self, classes):
        """Create classes table block"""
        columns = [
            {"key": "class_name", "label": "Class Name", "sortable": True},
            {"key": "grade_level", "label": "Grade", "sortable": True},
            {"key": "group_name", "label": "Group", "sortable": True},
            {"key": "academic_year", "label": "Year", "align": "center"},
            {"key": "student_count", "label": "Students", "align": "center"},
            status_column("status", "Status", {
                "Active": "success",
                "Empty": "warning",
                "Inactive": "danger"
            })
        ]
        
        rows = []
        for cls in classes:
            group_name = determine_grade_group(cls.level)
            
            # Determine status
            if cls.student_count == 0:
                status = "Empty"
            elif cls.active_students == 0:
                status = "Inactive"
            else:
                status = "Active"
            
            # Build display name
            full_class_name = format_class_display_name(cls.name, cls.stream)
            
            row_data = {
                "class_name": full_class_name,
                "grade_level": cls.level,
                "group_name": group_name,
                "academic_year": cls.academic_year,
                "student_count": cls.student_count,
                "status": status
            }
            
            # Add action to view class details
            rows.append(
                action_row(row_data, "query", {"message": f"show class {cls.name} details"})
            )
        
        table_actions = [
            {"label": "Create New Class", "type": "query", "payload": {"message": "create new class"}},
            {"label": "Show Empty Classes", "type": "query", "payload": {"message": "show empty classes"}},
            {"label": "Assign Students", "type": "query", "payload": {"message": "assign students to classes"}}
        ]
        
        table_filters = [
            {"type": "select", "key": "group_name", "label": "Grade Group", 
             "options": sorted(list(set(row["group_name"] for row in rows)))},
            {"type": "select", "key": "status", "label": "Status", "options": ["Active", "Empty", "Inactive"]},
            {"type": "number", "key": "academic_year", "label": "Academic Year"}
        ]
        
        return table(
            "Class Directory",
            columns,
            rows,
            pagination={"mode": "client", "page": 1, "pageSize": 20, "total": len(rows)},
            actions=table_actions,
            filters=table_filters
        )
    
    def _create_grades_table(self, grades, grade_class_counts):
        """Create the grades table block"""
        columns = [
            {"key": "grade_name", "label": "Grade", "sortable": True},
            {"key": "group_name", "label": "Group", "sortable": True},
            {"key": "class_count", "label": "Classes", "align": "center"},
            status_column("status", "Status", {
                "Active": "success",
                "No Classes": "warning"
            })
        ]
        
        rows = []
        for grade in grades:
            class_count = grade_class_counts.get(grade.label, 0)
            status = "Active" if class_count > 0 else "No Classes"
            
            row_data = {
                "grade_name": grade.label,
                "group_name": grade.group_name,
                "class_count": class_count,
                "status": status
            }
            
            # Add action to create class for this grade
            if class_count == 0:
                action_message = f"create class for {grade.label}"
            else:
                action_message = f"show classes for {grade.label}"
            
            rows.append(
                action_row(row_data, "query", {"message": action_message})
            )
        
        table_actions = [
            {"label": "Create New Grade", "type": "query", "payload": {"message": "create new grade"}},
            {"label": "Create New Class", "type": "query", "payload": {"message": "create new class"}},
            {"label": "Show All Classes", "type": "query", "payload": {"message": "list all classes"}}
        ]
        
        table_filters = [
            {"type": "select", "key": "group_name", "label": "Grade Group", 
             "options": sorted(list(set(grade.group_name for grade in grades)))},
            {"type": "select", "key": "status", "label": "Status", "options": ["Active", "No Classes"]}
        ]
        
        return table(
            "Academic Grades",
            columns,
            rows,
            pagination={"mode": "client", "pageSize": 15} if len(rows) > 15 else None,
            actions=table_actions,
            filters=table_filters
        )
    
    def _create_empty_classes_table(self, empty_classes):
        """Create table for empty classes"""
        columns = [
            {"key": "class_name", "label": "Class Name", "sortable": True},
            {"key": "grade_level", "label": "Grade", "sortable": True},
            {"key": "group_name", "label": "Group", "sortable": True},
            {"key": "academic_year", "label": "Year", "align": "center"}
        ]
        
        rows = []
        for cls in empty_classes:
            group_name = determine_grade_group(cls.level)
            full_class_name = format_class_display_name(cls.name, cls.stream)
            
            row_data = {
                "class_name": full_class_name,
                "grade_level": cls.level,
                "group_name": group_name,
                "academic_year": cls.academic_year
            }
            
            # Add action to assign students to this class
            rows.append(
                action_row(row_data, "query", {"message": f"assign students to {cls.name}"})
            )
        
        table_actions = [
            {"label": "Assign Students", "type": "query", "payload": {"message": "assign students to classes"}},
            {"label": "Show Unassigned Students", "type": "query", "payload": {"message": "show unassigned students"}},
            {"label": "Create New Class", "type": "query", "payload": {"message": "create new class"}}
        ]
        
        return table(
            "Empty Classes",
            columns,
            rows,
            actions=table_actions,
            filters=[
                {"type": "select", "key": "group_name", "label": "Grade Group", 
                 "options": sorted(list(set(row["group_name"] for row in rows)))},
                {"type": "number", "key": "academic_year", "label": "Academic Year"}
            ]
        )
    
    def _create_class_statistics_table(self, classes_by_level):
        """Create class statistics breakdown table"""
        columns = [
            {"key": "grade_level", "label": "Grade Level", "sortable": True},
            {"key": "grade_group", "label": "Group", "sortable": True},
            {"key": "total_classes", "label": "Classes", "align": "center"},
            {"key": "with_students", "label": "With Students", "align": "center"},
            {"key": "utilization", "label": "Utilization", "align": "center"}
        ]
        
        rows = []
        for level_data in classes_by_level:
            level = level_data["level"]
            count = level_data["count"]
            with_students = level_data["with_students"]
            utilization_pct = (with_students / count * 100) if count > 0 else 0
            
            row_data = {
                "grade_level": level,
                "grade_group": determine_grade_group(level),
                "total_classes": count,
                "with_students": with_students,
                "utilization": f"{utilization_pct:.0f}%"
            }
            
            rows.append(
                action_row(row_data, "query", {"message": f"show {level} classes"})
            )
        
        return table(
            "Classes by Grade Level",
            columns,
            rows,
            actions=[
                {"label": "View All Classes", "type": "query", "payload": {"message": "list all classes"}},
                {"label": "Create New Class", "type": "query", "payload": {"message": "create new class"}}
            ]
        )
    
    def _group_classes_by_grade(self, classes):
        """Group classes by grade group"""
        classes_by_group = {}
        
        for cls in classes:
            group_name = determine_grade_group(cls.level)
            
            if group_name not in classes_by_group:
                classes_by_group[group_name] = []
            classes_by_group[group_name].append(cls)
        
        return classes_by_group
    
    def _group_grades_by_group(self, grades):
        """Group grades by their group name"""
        grades_by_group = {}
        for grade in grades:
            group = grade.group_name
            if group not in grades_by_group:
                grades_by_group[group] = []
            grades_by_group[group].append(grade)
        return grades_by_group
    
    def _group_empty_classes_by_grade(self, empty_classes):
        """Group empty classes by grade group"""
        empty_by_group = {}
        
        for cls in empty_classes:
            group_name = determine_grade_group(cls.level)
            
            if group_name not in empty_by_group:
                empty_by_group[group_name] = []
            empty_by_group[group_name].append(cls)
        
        return empty_by_group
    
    def _create_classes_chart(self, classes_by_group):
        """Create class distribution chart"""
        chart_data = [
            {"group": group, "classes": len(group_classes)}
            for group, group_classes in classes_by_group.items()
        ]
        
        return chart_xy(
            "Classes by Grade Group",
            "bar",
            "group",
            "classes",
            [{"name": "Classes", "data": chart_data}],
            {"height": 200, "yAxisFormat": "integer"}
        )
    
    def _create_grades_chart(self, grades_by_group):
        """Create grade distribution chart"""
        chart_data = [
            {"group": group, "grades": len(group_grades)}
            for group, group_grades in grades_by_group.items()
        ]
        
        return chart_xy(
            "Grades by Group",
            "bar",
            "group",
            "grades",
            [{"name": "Grades", "data": chart_data}],
            {"height": 200, "yAxisFormat": "integer"}
        )
    
    def _create_class_utilization_chart(self, active_classes, empty_classes):
        """Create class utilization pie chart"""
        chart_data = [
            {"category": "With Students", "count": active_classes},
            {"category": "Empty", "count": empty_classes}
        ]
        
        return chart_pie(  # ✅ Correct function for pie chart
            "Class Utilization",
            "pie",           # ✅ chart_pie supports pie
            "category",      # ✅ labelField
            "count",         # ✅ valueField
            chart_data,      # ✅ data (not wrapped in series)
            {"height": 300}
        )
    
    def _create_overview_kpis(self, stats):
        """Create overview KPIs block"""
        kpi_items = []
        
        if stats['total_grades'] > 0:
            kpi_items.append(
                count_kpi("Academic Grades", stats['total_grades'], "info",
                         action={"type": "query", "payload": {"message": "list grades"}})
            )
        
        if stats['total_classes'] > 0:
            kpi_items.append(
                count_kpi("Total Classes", stats['total_classes'], "primary",
                         action={"type": "query", "payload": {"message": "list classes"}})
            )
            
            if stats['total_students'] > 0:
                kpi_items.append(
                    count_kpi("Students", stats['total_students'], "success")
                )
        else:
            kpi_items.append(
                {"label": "Classes", "value": "Create First", "variant": "warning",
                 "action": {"type": "query", "payload": {"message": "create new class"}}}
            )
        
        if stats['empty_classes'] > 0:
            kpi_items.append(
                count_kpi("Empty Classes", stats['empty_classes'], "warning",
                         action={"type": "query", "payload": {"message": "show empty classes"}})
            )
        
        return kpis(kpi_items)
    
    def _create_overview_guidance(self, stats):
        """Create guidance text based on current setup state"""
        if stats['total_grades'] == 0:
            return text("**Getting Started:**\n\n1. **Create Grades** - Set up academic levels (Grade 1, PP1, Form 1, etc.)\n2. **Create Classes** - Add specific classes for each grade\n3. **Assign Students** - Place students in appropriate classes\n\nGrades help organize fee structures, while classes group students for daily management.")
        
        elif stats['total_classes'] == 0:
            return text(f"You have {stats['total_grades']} grades set up. Now create classes within these grades to organize your students.\n\n**Classes** group students by grade level and section (like 'Grade 1 East' or 'Form 2A').")
        
        elif stats['empty_classes'] > 0:
            return text(f"Your class system is operational with {stats['total_classes']} classes and {stats['total_students']} students. You have {stats['empty_classes']} empty classes that could use student assignments.")
        
        else:
            return text("Your class system is fully operational! You can create more classes, view existing ones, or manage student assignments.")
    
    def _create_quick_actions_table(self, stats):
        """Create quick actions table"""
        actions_data = []
        
        actions_data.append({
            "action": "View All Classes",
            "description": f"Browse all {stats['total_classes']} classes",
            "status": "Available"
        })
        
        if stats['empty_classes'] > 0:
            actions_data.append({
                "action": "Show Empty Classes",
                "description": f"Review {stats['empty_classes']} classes needing students",
                "status": "Needs Attention"
            })
        
        actions_data.append({
            "action": "Create New Class", 
            "description": "Add another class to any grade",
            "status": "Available"
        })
        
        if stats['total_grades'] > 0:
            actions_data.append({
                "action": "View Grades",
                "description": f"Manage {stats['total_grades']} academic grades",
                "status": "Available"
            })
        
        columns = [
            {"key": "action", "label": "Action", "sortable": False},
            {"key": "description", "label": "Description", "sortable": False},
            status_column("status", "Status", {
                "Available": "success",
                "Needs Attention": "warning"
            })
        ]
        
        rows = []
        action_mapping = {
            "View All Classes": "list all classes",
            "Show Empty Classes": "show empty classes",
            "Create New Class": "create new class",
            "View Grades": "list grades"
        }
        
        for action_data in actions_data:
            rows.append(
                action_row(action_data, "query", {
                    "message": action_mapping.get(action_data["action"], action_data["action"].lower())
                })
            )
        
        return table(
            "Quick Actions",
            columns,
            rows
        )
    
    def _get_overview_suggestions(self, stats):
        """Get contextual suggestions for overview"""
        suggestions = []
        
        if stats['total_grades'] == 0:
            suggestions.extend(["Create new grade", "Setup CBC grades"])
        else:
            suggestions.append("List grades")
            
        if stats['total_classes'] == 0:
            suggestions.append("Create new class")
        else:
            suggestions.extend(["List classes", "Create new class"])
        
        if stats['empty_classes'] > 0:
            suggestions.insert(-1, "Show empty classes")
            
        suggestions.extend(["Show class statistics", "School overview"])
        
        return suggestions