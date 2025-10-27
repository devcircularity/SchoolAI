# handlers/overview/views.py
from app.services.blocks_renderer import (
    text, kpis, table, timeline, status, chart_pie, chart_xy,
    currency_kpi, count_kpi, percentage_kpi, 
    currency_column, date_column, status_column, action_row
)
from ...base import ChatResponse
from .dataclasses import OverviewData, CurrentTerm, StudentStats, ClassStats, AcademicStats

class OverviewViews:
    """Pure presentation layer for overview responses"""
    
    def __init__(self, school_name_fn):
        self.get_school_name = school_name_fn
    
    def school_overview(self, data: OverviewData):
        """Display comprehensive school overview"""
        blocks = []
        
        # Header with school info
        blocks.append(text(f"**{data.school_name}** - Complete School Overview\n\nHere's your school's current status and key metrics:"))
        
        # Core KPIs
        kpi_items = [
            count_kpi("Total Students", data.student_stats.total, "primary", 
                     action={"type": "query", "payload": {"message": "list all students"}}),
            count_kpi("Active Classes", data.class_stats.total, "info",
                     action={"type": "query", "payload": {"message": "list all classes"}}),
            count_kpi("Academic Years", data.academic_stats.years, "success"),
        ]
        
        # Add enrollment info if there's an active term
        if data.current_term:
            kpi_items.append(
                count_kpi("Enrolled This Term", data.student_stats.enrolled_current_term, "success")
            )
        
        # Add warning KPIs for unassigned students
        if data.student_stats.unassigned > 0:
            kpi_items.append(
                count_kpi("Unassigned Students", data.student_stats.unassigned, "warning",
                         action={"type": "query", "payload": {"message": "show unassigned students"}})
            )
        
        blocks.append(kpis(kpi_items))
        
        # Current term status
        if data.current_term:
            blocks.append(text(f"**Current Academic Term:** {data.current_term.title} ({data.current_term.year})"))
            
            # Add enrollment breakdown chart if we have data
            if data.student_stats.enrolled_current_term > 0:
                enrollment_data = [
                    {"status": "Enrolled", "count": data.student_stats.enrolled_current_term},
                    {"status": "Not Enrolled", "count": data.student_stats.active - data.student_stats.enrolled_current_term},
                ]
                
                if enrollment_data[1]["count"] > 0:  # Only show chart if there are mixed statuses
                    blocks.append(
                        chart_pie(
                            "Student Enrollment Status", 
                            "status", 
                            "count", 
                            enrollment_data,
                            donut=True,
                            options={"height": 200, "legend": True}
                        )
                    )
        else:
            blocks.append(text("⚠️ **No Active Academic Term** - Please activate a term to enable enrollments"))
        
        # Class breakdown table if we have classes
        if data.class_stats.total > 0 and data.class_breakdown:
            class_columns = [
                {"key": "class_name", "label": "Class", "sortable": True},
                {"key": "level", "label": "Grade Level"},
                {"key": "student_count", "label": "Students", "align": "center"},
                {"key": "status", "label": "Status", "badge": {"map": {"Active": "success", "Empty": "warning"}}},
            ]
            
            # Add actions to view class details
            class_rows = [
                action_row({
                    "class_name": cls.class_name,
                    "level": cls.level,
                    "student_count": cls.student_count,
                    "status": cls.status
                }, "query", {"message": f"show class {cls.class_name} details"})
                for cls in data.class_breakdown[:5]  # Show top 5 classes
            ]
            
            blocks.append(
                table(
                    "Class Overview",
                    class_columns,
                    class_rows,
                    pagination={"mode": "client", "pageSize": 5} if len(data.class_breakdown) > 5 else None,
                    actions=[
                        {"label": "View All Classes", "type": "query", "payload": {"message": "list all classes"}},
                        {"label": "Create New Class", "type": "query", "payload": {"message": "create new class"}}
                    ]
                )
            )
        
        # System status
        status_items = []
        if data.current_term:
            status_items.append({"label": "Academic Term", "state": "ok", "detail": f"Active: {data.current_term.title}"})
        else:
            status_items.append({"label": "Academic Term", "state": "error", "detail": "No active term"})
        
        if data.student_stats.unassigned == 0:
            status_items.append({"label": "Student Assignments", "state": "ok", "detail": "All students assigned"})
        else:
            status_items.append({"label": "Student Assignments", "state": "warning", "detail": f"{data.student_stats.unassigned} unassigned"})
        
        blocks.append(status(status_items))
        
        # Recent activity timeline
        if data.recent_activity:
            timeline_items = [
                {
                    "time": item.time,
                    "icon": item.icon,
                    "title": item.title,
                    "subtitle": item.subtitle
                }
                for item in data.recent_activity
            ]
            blocks.append(timeline(timeline_items))
        
        # Build suggestions based on current state
        suggestions = self._get_contextual_suggestions(data)
        
        return ChatResponse(
            response=f"School Overview - {data.school_name}",
            intent="school_overview",
            data={
                "school_name": data.school_name,
                "statistics": {
                    "students": {
                        "total": data.student_stats.total,
                        "active": data.student_stats.active,
                        "unassigned": data.student_stats.unassigned,
                        "enrolled_current_term": data.student_stats.enrolled_current_term
                    },
                    "classes": {
                        "total": data.class_stats.total,
                        "with_students": data.class_stats.with_students
                    },
                    "academic": {
                        "years": data.academic_stats.years,
                        "terms": data.academic_stats.terms,
                        "active_terms": data.academic_stats.active_terms
                    }
                },
                "academic_context": {
                    "current_term": {
                        "id": data.current_term.id,
                        "title": data.current_term.title,
                        "state": data.current_term.state,
                        "year": data.current_term.year,
                        "year_title": data.current_term.year_title
                    } if data.current_term else None
                }
            },
            blocks=blocks,
            suggestions=suggestions
        )
    
    def _get_contextual_suggestions(self, data: OverviewData) -> list:
        """Get contextual suggestions based on current state"""
        suggestions = []
        
        # Priority-based suggestions
        if data.academic_stats.years == 0:
            suggestions.extend([
                "Bootstrap school setup",
                "Create academic year",
                "Setup academic calendar"
            ])
        elif not data.current_term:
            suggestions.extend([
                "Activate academic term", 
                "Show academic calendar",
                "Setup current term"
            ])
        elif data.student_stats.unassigned > 0:
            suggestions.extend([
                "Show unassigned students",
                "Assign students to classes",
                "Create more classes"
            ])
        elif (data.current_term and 
              data.student_stats.enrolled_current_term < data.student_stats.active):
            suggestions.extend([
                "Enroll students in current term",
                "Show enrollment status",
                "Bulk enroll students"
            ])
        else:
            # Everything looks good
            suggestions.extend([
                "Show current term details",
                "List students",
                "Show class enrollments"
            ])
        
        # Always useful suggestions
        suggestions.extend([
            "List all students",
            "Show academic calendar"
        ])
        
        # Return first 4-5 suggestions to avoid overwhelming
        return suggestions[:5]
    
    def error(self, operation, error_msg):
        """Error response"""
        return ChatResponse(
            response=f"Error getting school overview: {error_msg}",
            intent="error",
            blocks=[text(f"Error getting school overview: {error_msg}")]
        )