# handlers/class/service.py
from ...base import ChatResponse
from .repo import ClassRepo
from .views import ClassViews
from .dataclasses import row_to_class, row_to_class_detail, row_to_grade
from datetime import datetime

class ClassService:
    """Business logic layer for class operations"""
    
    def __init__(self, db, school_id, get_school_name):
        self.repo = ClassRepo(db, school_id)
        self.views = ClassViews(get_school_name)
    
    def list_classes(self):
        """List all classes with rich display"""
        try:
            class_rows = self.repo.list_all_classes()
            if not class_rows:
                return self.views.no_classes_found()
            
            classes = [row_to_class(row) for row in class_rows]
            return self.views.list_classes_table(classes)
        except Exception as e:
            return self.views.error("listing classes", str(e))
    
    def show_class_details(self, class_name):
        """Show detailed information for a specific class"""
        try:
            class_results = self.repo.get_class_by_name(class_name)
            
            if not class_results:
                return self.views.class_not_found(class_name)
            
            # If multiple matches, take the first one but mention it
            class_info = class_results[0]
            multiple_matches = len(class_results) > 1
            
            class_detail = row_to_class_detail(class_info)
            return self.views.class_details(
                class_detail, 
                multiple_matches, 
                len(class_results), 
                class_name
            )
        except Exception as e:
            return self.views.error("getting class details", str(e))
    
    def show_empty_classes(self):
        """Show classes without any students"""
        try:
            empty_class_rows = self.repo.get_empty_classes()
            empty_classes = [row_to_class((*row, 0, 0)) for row in empty_class_rows]  # Add student counts as 0
            return self.views.empty_classes_list(empty_classes)
        except Exception as e:
            return self.views.error("getting empty classes", str(e))
    
    def list_grades(self):
        """List all available grades with class counts"""
        try:
            grade_rows = self.repo.get_available_grades()
            if not grade_rows:
                return self.views.no_grades_found()
            
            grades = [row_to_grade(row) for row in grade_rows]
            grade_class_counts = self.repo.get_grade_class_counts(grades)
            
            return self.views.list_grades_table(grades, grade_class_counts)
        except Exception as e:
            return self.views.error("listing grades", str(e))
    
    def show_class_statistics(self):
        """Show comprehensive class statistics"""
        try:
            stats = self.repo.get_class_counts()
            return self.views.class_statistics(stats)
        except Exception as e:
            return self.views.error("getting class statistics", str(e))
    
    def show_overview(self):
        """Show general class system overview"""
        try:
            stats = self._get_overview_statistics()
            return self.views.overview(stats)
        except Exception as e:
            return self.views.error("loading overview", str(e))
    
    def _get_overview_statistics(self):
        """Get overview statistics for class system"""
        stats = {
            'total_classes': 0,
            'total_grades': 0,
            'total_students': 0,
            'empty_classes': 0,
            'active_classes': 0
        }
        
        try:
            # Get class counts
            class_stats = self.repo.get_class_counts()
            stats.update({
                'total_classes': class_stats['total'],
                'empty_classes': class_stats['empty'],
                'active_classes': class_stats['active']
            })
            
            # Get grade count
            grade_rows = self.repo.get_available_grades()
            stats['total_grades'] = len(grade_rows)
            
            # Get total students if we have classes
            if stats['total_classes'] > 0:
                from ...base import db_execute_safe
                result = db_execute_safe(self.repo.db,
                    """SELECT COUNT(s.id) FROM students s 
                       JOIN classes c ON s.class_id = c.id 
                       WHERE c.school_id = :school_id AND s.status = 'ACTIVE'""",
                    {"school_id": self.repo.school_id}
                )
                stats['total_students'] = result[0][0] if result else 0
        
        except Exception as e:
            print(f"Error getting overview statistics: {e}")
        
        return stats