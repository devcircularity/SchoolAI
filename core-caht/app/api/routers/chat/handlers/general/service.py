# handlers/general/service.py
from ...base import ChatResponse
from .repo import GeneralRepo
from .views import GeneralViews

class GeneralService:
    """Business logic layer for general system operations"""
    
    def __init__(self, db, school_id, get_school_name):
        self.repo = GeneralRepo(db, school_id)
        self.views = GeneralViews(get_school_name)
    
    def handle_greeting(self, message: str):
        """Handle greeting messages"""
        try:
            return self.views.greeting_response(message)
        except Exception as e:
            return self.views.error("processing greeting", str(e))
    
    def handle_school_registration_query(self, message: str):
        """Handle school registration/information queries"""
        try:
            school_name = self.repo.get_school_name()
            system_status = self.repo.get_system_status()
            return self.views.school_registration_complete(school_name, system_status)
        except Exception as e:
            return self.views.error("getting school information", str(e))
    
    def handle_getting_started(self):
        """Handle getting started guide"""
        try:
            system_status = self.repo.get_system_status()
            return self.views.getting_started_guide(system_status)
        except Exception as e:
            return self.views.error("loading getting started guide", str(e))
    
    def handle_system_capabilities(self):
        """Handle system capabilities overview"""
        try:
            usage_stats = self.repo.get_system_usage_stats()
            return self.views.system_capabilities(usage_stats)
        except Exception as e:
            return self.views.error("loading system capabilities", str(e))
    
    def handle_help_request(self, message: str):
        """Handle help requests"""
        try:
            # Detect topic from message
            detected_topic = self._detect_help_topic(message)
            return self.views.help_request(detected_topic)
        except Exception as e:
            return self.views.error("processing help request", str(e))
    
    def handle_next_steps_guidance(self):
        """Handle what to do next guidance"""
        try:
            system_status = self.repo.get_system_status()
            critical_issues, recommended_actions = self._analyze_next_steps(system_status)
            return self.views.next_steps_guidance(system_status, critical_issues, recommended_actions)
        except Exception as e:
            return self.views.error("analyzing next steps", str(e))
    
    def handle_general_intent(self, message: str):
        """Handle general intents"""
        try:
            return self.views.general_assistance()
        except Exception as e:
            return self.views.error("processing general intent", str(e))
    
    def _detect_help_topic(self, message: str):
        """Detect what topic user needs help with"""
        message_lower = message.lower()
        
        help_topics = {
            "student": ["student", "pupil", "learner", "register", "admission"],
            "class": ["class", "grade", "level", "assign", "classroom"],
            "payment": ["payment", "fee", "invoice", "money", "pay", "mpesa", "cash"],
            "academic": ["term", "year", "calendar", "academic", "semester"],
            "enrollment": ["enroll", "registration", "admission", "assign"],
            "setup": ["setup", "configure", "install", "begin", "start", "initialize"]
        }
        
        for topic, keywords in help_topics.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic
        
        return None
    
    def _analyze_next_steps(self, system_status):
        """Analyze system status and determine next steps"""
        critical_issues = []
        recommended_actions = []
        
        # Critical setup issues (must be resolved first)
        if system_status['academic_years'] == 0:
            critical_issues.append({
                "title": "Set Up Academic Calendar",
                "description": "Create academic years and terms - this is the foundation for all other operations",
                "action": "Create Academic Year",
                "message": "create academic year",
                "impact": "High - Required for student enrollment",
                "estimated_time": "10-15 minutes"
            })
        elif system_status['active_terms'] == 0:
            critical_issues.append({
                "title": "Activate Academic Term", 
                "description": "Activate a term to enable student enrollments and invoice generation",
                "action": "Activate Term",
                "message": "show academic calendar",
                "impact": "High - Required for current operations",
                "estimated_time": "2-3 minutes"
            })
        
        if system_status['grades'] == 0:
            critical_issues.append({
                "title": "Create Grade Levels",
                "description": "Set up CBC grade levels to organize your school structure",
                "action": "Create Grades",
                "message": "create new grade",
                "impact": "High - Required for class creation",
                "estimated_time": "15-20 minutes"
            })
        
        if system_status['classes'] == 0 and system_status['grades'] > 0:
            critical_issues.append({
                "title": "Create Classes",
                "description": "Set up classes within your grade levels to organize students",
                "action": "Create Classes",
                "message": "create new class",
                "impact": "High - Required for student assignment",
                "estimated_time": "10-15 minutes per class"
            })
        
        # Recommended actions (important but not blocking)
        if system_status['students'] == 0 and system_status['classes'] > 0:
            recommended_actions.append({
                "title": "Register Students",
                "description": "Add your first students with complete guardian information",
                "action": "Add Students",
                "message": "create new student", 
                "impact": "High - Core purpose of the system",
                "estimated_time": "5-10 minutes per student"
            })
        elif system_status['unassigned_students'] > 0:
            recommended_actions.append({
                "title": "Assign Students to Classes",
                "description": f"{system_status['unassigned_students']} students need class assignments",
                "action": "Show Unassigned",
                "message": "show unassigned students",
                "impact": "Medium - Required for enrollment",
                "estimated_time": "2-3 minutes per student"
            })
        elif system_status['unenrolled_students'] > 0:
            recommended_actions.append({
                "title": "Enroll Students in Current Term",
                "description": f"{system_status['unenrolled_students']} students ready for term enrollment", 
                "action": "Enroll Students",
                "message": "enroll students in current term",
                "impact": "Medium - Required for invoicing",
                "estimated_time": "5-10 minutes for bulk enrollment"
            })
        elif system_status['students_without_invoices'] > 0:
            recommended_actions.append({
                "title": "Generate Student Invoices",
                "description": f"{system_status['students_without_invoices']} students need invoices for payment tracking",
                "action": "Generate Invoices", 
                "message": "generate invoices for all students",
                "impact": "Medium - Required for payment collection",
                "estimated_time": "5-10 minutes for bulk generation"
            })
        
        return critical_issues, recommended_actions