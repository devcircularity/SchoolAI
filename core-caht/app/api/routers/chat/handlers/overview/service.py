# handlers/overview/service.py
from ...base import ChatResponse
from .repo import OverviewRepo
from .views import OverviewViews
from .dataclasses import (
    OverviewData, create_student_stats, create_class_stats, 
    create_academic_stats, create_fee_stats, create_current_term,
    create_class_breakdown, create_activity_item
)

class OverviewService:
    """Business logic layer for overview operations"""
    
    def __init__(self, db, school_id, get_school_name):
        self.repo = OverviewRepo(db, school_id)
        self.views = OverviewViews(get_school_name)
        self.get_school_name = get_school_name
    
    def get_school_overview(self):
        """Get comprehensive school overview"""
        try:
            # Gather all data
            overview_data = self._compile_overview_data()
            
            return self.views.school_overview(overview_data)
            
        except Exception as e:
            return self.views.error("getting school overview", str(e))
    
    def _compile_overview_data(self) -> OverviewData:
        """Compile all overview data from repositories"""
        # Get basic statistics
        student_stats = create_student_stats(self.repo.get_student_statistics())
        class_stats = create_class_stats(self.repo.get_class_statistics())
        academic_stats = create_academic_stats(self.repo.get_academic_statistics())
        
        # Get current term enrollment
        student_stats.enrolled_current_term = self.repo.get_current_term_enrollment()
        
        # Get current term info
        current_term_rows = self.repo.get_current_term_info()
        current_term = create_current_term(current_term_rows)
        
        # Get class breakdown
        class_breakdown_rows = self.repo.get_class_breakdown()
        class_breakdown = create_class_breakdown(class_breakdown_rows)
        
        # Get recent activity
        recent_activity = self._compile_recent_activity()
        
        # Get fee statistics (optional)
        try:
            fee_stats_rows = self.repo.get_fee_statistics()
            fee_stats = create_fee_stats(fee_stats_rows[0]) if fee_stats_rows else None
        except Exception:
            fee_stats = None
        
        return OverviewData(
            school_name=self.get_school_name(),
            student_stats=student_stats,
            class_stats=class_stats,
            academic_stats=academic_stats,
            fee_stats=fee_stats,
            current_term=current_term,
            class_breakdown=class_breakdown,
            recent_activity=recent_activity
        )
    
    def _compile_recent_activity(self):
        """Compile recent activity timeline"""
        recent_items = []
        
        try:
            # Recent enrollments
            recent_enrollments = self.repo.get_recent_enrollments(7)
            if recent_enrollments and recent_enrollments[0][0] > 0:
                count, last_date = recent_enrollments[0]
                if last_date:
                    recent_items.append(create_activity_item(
                        time=last_date.strftime("%Y-%m-%d"),
                        icon="users",
                        title=f"{count} students enrolled",
                        subtitle="In the past 7 days"
                    ))
            
            # Recent classes created
            recent_classes = self.repo.get_recent_classes(7)
            if recent_classes and recent_classes[0][0] > 0:
                count, last_date = recent_classes[0]
                if last_date:
                    recent_items.append(create_activity_item(
                        time=last_date.strftime("%Y-%m-%d"),
                        icon="school",
                        title=f"{count} classes created",
                        subtitle="In the past 7 days"
                    ))
            
            return recent_items[:5]  # Return max 5 items
            
        except Exception as e:
            print(f"Error compiling recent activity: {e}")
            return []