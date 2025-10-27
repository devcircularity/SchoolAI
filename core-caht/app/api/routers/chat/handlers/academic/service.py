# handlers/academic/service.py
from ...base import ChatResponse
from .repo import AcademicRepo
from .views import AcademicViews
from .dataclasses import row_to_term, EnrollmentStats, SetupStatus
from ..shared.parsing import extract_admission_number, is_confirmation, is_cancellation
import re
from typing import Optional, Dict, List

class AcademicService:
    """Business logic layer for academic operations"""
    
    def __init__(self, db, school_id, get_school_name):
        self.repo = AcademicRepo(db, school_id)
        self.views = AcademicViews(get_school_name)
        self.db = db
    
    def get_current_term(self):
        """Get current active term with enrollment statistics"""
        try:
            current_term_rows = self.repo.get_current_term()
            
            if not current_term_rows:
                return self.views.no_active_term()
            
            term_row = row_to_term(current_term_rows[0])
            
            # Get enrollment statistics
            enrollment_stats_rows = self.repo.get_enrollment_stats(term_row.id)
            stats = EnrollmentStats(
                total_enrollments=enrollment_stats_rows[0][0] if enrollment_stats_rows else 0,
                unique_students=enrollment_stats_rows[0][1] if enrollment_stats_rows else 0,
                enrolled_classes=enrollment_stats_rows[0][2] if enrollment_stats_rows else 0
            )
            
            return self.views.current_term_details(term_row, stats)
            
        except Exception as e:
            return self.views.error("getting current term", str(e))
    
    def initiate_term_activation(self, message: str = ""):
        """Start the term activation process"""
        try:
            # Check if there's already an active term
            current_active_rows = self.repo.get_active_terms()
            
            if current_active_rows:
                current_term = current_active_rows[0]
                current_term_info = {
                    "id": str(current_term[0]),
                    "title": current_term[1],
                    "year": current_term[2]
                }
                
                return self.views.term_switch_confirmation(current_term_info, message)
            
            return self._show_term_selection(message)
            
        except Exception as e:
            return self.views.error("activating term", str(e))
    
    def handle_switch_confirmation(self, message: str, context: Dict):
        """Handle confirmation to switch terms"""
        if is_cancellation(message) or "keep current" in message.lower():
            return self.views.switch_cancelled()
        
        if is_confirmation(message) or "switch" in message.lower() or "show available" in message.lower():
            original_message = context.get('original_message', '')
            return self._show_term_selection(original_message)
        
        return self._show_term_selection(context.get('original_message', ''))
    
    def _show_term_selection(self, original_message: str = ""):
        """Show available terms for selection"""
        try:
            available_terms = self.repo.get_available_terms()
            
            if not available_terms:
                return self.views.no_terms_to_activate()
            
            # Try to parse specific term from original message
            selected_term = self._parse_term_selection(original_message, available_terms)
            
            if selected_term:
                return self._activate_selected_term(selected_term)
            
            return self.views.term_selection(available_terms)
            
        except Exception as e:
            return self.views.error("showing term selection", str(e))
    
    def handle_term_selection(self, message: str, context: Dict):
        """Process term selection from user"""
        if is_cancellation(message):
            return ChatResponse(
                response="Term activation cancelled.",
                intent="term_activation_cancelled",
                data={"context": {}},
                blocks=[self.views.text("**Term Activation Cancelled**\n\nNo changes were made to your academic terms.")],
                suggestions=["Show current term", "List all terms", "Academic calendar"]
            )
        
        available_terms = context.get('available_terms', [])
        if not available_terms:
            return self.views.error("processing term selection", "No available terms found in context")
        
        # Parse selection
        selected_term = None
        selected_index = self._parse_term_index(message)
        
        # Validate selection
        if selected_index is not None and 0 <= selected_index < len(available_terms):
            selected_term = available_terms[selected_index]
            return self._activate_selected_term(selected_term)
        else:
            return self.views.invalid_term_selection(available_terms, context)
    
    def _parse_term_selection(self, message: str, available_terms: list) -> Optional[dict]:
        """Parse term selection from original message"""
        if not message:
            return None
        
        message_lower = message.lower()
        
        # Try to match by index
        index = self._parse_term_index(message)
        if index is not None and 0 <= index < len(available_terms):
            term = available_terms[index]
            return {
                "id": str(term[0]),
                "title": term[1],
                "year": term[3],
                "start_date": term[4],
                "end_date": term[5]
            }
        
        # Try to match by term title
        for term in available_terms:
            term_title_lower = term[1].lower()
            if any(phrase in message_lower for phrase in [
                term_title_lower,
                f"activate {term_title_lower}"
            ]):
                return {
                    "id": str(term[0]),
                    "title": term[1],
                    "year": term[3],
                    "start_date": term[4],
                    "end_date": term[5]
                }
        
        return None
    
    def _parse_term_index(self, message: str) -> Optional[int]:
        """Parse term index from message"""
        term_patterns = [
            r'(?:activate|term|select)\s+(?:term\s+)?(\d+)',
            r'(?:term|number)\s+(\d+)',
            r'(?:^|\s)(\d+)(?:\s|$)'
        ]
        
        message_lower = message.lower()
        for pattern in term_patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    return int(match.group(1)) - 1  # Convert to 0-based index
                except (ValueError, IndexError):
                    continue
        return None
    
    def _activate_selected_term(self, term_info: dict):
        """Actually activate the selected term"""
        try:
            term_id = term_info["id"]
            
            # Deactivate current active term first
            self.repo.deactivate_all_terms()
            
            # Activate the selected term
            affected_rows = self.repo.activate_term(term_id)
            
            if affected_rows == 0:
                return self.views.activation_failed()
            
            self.db.commit()
            
            return self.views.term_activated_success(term_info)
            
        except Exception as e:
            try:
                self.db.rollback()
            except:
                pass
            
            return self.views.error("activating term", str(e))
    
    def get_academic_calendar(self):
        """Show all academic years and terms"""
        try:
            academic_data = self.repo.get_academic_calendar()
            
            if not academic_data:
                return self.views.no_academic_setup()
            
            # Organize data by year
            years_data = self._organize_calendar_data(academic_data)
            
            return self.views.academic_calendar(years_data)
            
        except Exception as e:
            return self.views.error("getting academic calendar", str(e))
    
    def _organize_calendar_data(self, academic_data):
        """Organize academic data by year"""
        years_data = {}
        for row in academic_data:
            year = row[0]
            if year not in years_data:
                years_data[year] = {
                    "title": row[1],
                    "state": row[2],
                    "terms": []
                }
            
            if row[3]:  # Term exists
                from .dataclasses import serialize_date
                years_data[year]["terms"].append({
                    "term": row[3],
                    "title": row[4],
                    "state": row[5],
                    "start_date": serialize_date(row[6]),
                    "end_date": serialize_date(row[7]),
                    "term_id": str(row[8]) if row[8] else None
                })
        
        return years_data
    
    def get_setup_status(self):
        """Guide user through academic setup"""
        try:
            stats = self.repo.get_setup_stats()
            
            setup = SetupStatus(
                year_count=stats["year_count"],
                term_count=stats["term_count"],
                active_terms=stats["active_terms"],
                setup_complete=(stats["year_count"] > 0 and 
                              stats["term_count"] > 0 and 
                              stats["active_terms"] == 1)
            )
            
            return self.views.setup_status(setup)
            
        except Exception as e:
            return self.views.error("checking academic setup", str(e))
    
    def get_overview(self):
        """General academic overview"""
        return self.views.overview()