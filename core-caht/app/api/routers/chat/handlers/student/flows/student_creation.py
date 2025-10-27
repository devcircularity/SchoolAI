# app/api/routers/chat/handlers/flows/student_creation.py - FIXED with context cleanup
import uuid
import re
from typing import Dict, List, Optional
from datetime import datetime, date
from ....base import ChatResponse, db_execute_safe, db_execute_non_select

class StudentCreationFlow:
    """Handles the multi-step student creation process with guardian management"""
    
    def __init__(self, db, school_id: str, user_id: str):
        self.db = db
        self.school_id = school_id
        self.user_id = user_id
    
    def initiate_creation(self, message: str = None) -> ChatResponse:
        """Start student creation - attempt smart parsing first"""
        if message:
            # Try to parse complete information from single command
            parsed_data = self._smart_parse_student_info(message)
            
            if parsed_data["completeness"] >= 80:
                return self._handle_parsed_data(parsed_data)
        
        # Fall back to guided conversation
        return self._start_guided_creation()
    
    def _smart_parse_student_info(self, message: str) -> Dict:
        """Attempt to extract all student and guardian info from message"""
        parsed = {
            "student_name": None,
            "admission_no": None,
            "gender": None,
            "dob": None,
            "guardian_name": None,
            "guardian_phone": None,
            "guardian_email": None,
            "relationship": None,
            "class_name": None,
            "completeness": 0
        }
        
        message_lower = message.lower()
        
        # More precise parsing approach
        
        # Extract admission number first (most reliable)
        admission_match = re.search(r'admission\s+(\w+)', message_lower)
        if admission_match:
            parsed["admission_no"] = admission_match.group(1)
        
        # Extract email (most reliable pattern)
        email_match = re.search(r'email\s+([a-zA-Z0-9@.\-_]+)', message_lower)
        if email_match:
            parsed["guardian_email"] = email_match.group(1)
        
        # Extract phone number (look for sequence after "phone")
        phone_match = re.search(r'phone\s+([0-9+\-\s]+?)(?:\s+email|$)', message_lower)
        if phone_match:
            parsed["guardian_phone"] = phone_match.group(1).strip()
        
        # Extract student name (between "student" and "admission")
        if admission_match:
            student_start = message_lower.find('student') + 7  # After "student "
            student_end = admission_match.start()
            student_text = message[student_start:student_end].strip()
            if student_text and len(student_text) >= 3:
                parsed["student_name"] = student_text
        
        # Extract guardian name (between "guardian" and "phone")
        guardian_match = re.search(r'guardian\s+([a-zA-Z\s]+?)\s+phone', message_lower)
        if guardian_match:
            parsed["guardian_name"] = guardian_match.group(1).strip()
        
        # Set default relationship
        parsed["relationship"] = "Parent"
        
        # Look for class assignment in the remaining text
        class_match = re.search(r'(?:class|assign.*to)\s+([a-zA-Z0-9\s]+)', message_lower)
        if class_match:
            parsed["class_name"] = class_match.group(1).strip()
        
        # Calculate completeness
        required_fields = ["student_name", "admission_no", "guardian_name", "guardian_phone", "guardian_email"]
        filled_fields = sum(1 for field in required_fields if parsed[field])
        parsed["completeness"] = (filled_fields / len(required_fields)) * 100
        
        return parsed
    
    def _handle_parsed_data(self, parsed_data: Dict) -> ChatResponse:
        """Handle partially or fully parsed data"""
        missing_fields = []
        required_fields = {
            "student_name": "Student name",
            "admission_no": "Admission number", 
            "guardian_name": "Guardian name",
            "guardian_phone": "Guardian phone",
            "guardian_email": "Guardian email"
        }
        
        for field, label in required_fields.items():
            if not parsed_data[field]:
                missing_fields.append(label)
        
        if not missing_fields:
            # All required fields present - create student
            return self._create_student_with_data(parsed_data)
        
        # Some fields missing - guide user
        found_info = []
        for field, label in required_fields.items():
            if parsed_data[field]:
                found_info.append(f"• {label}: {parsed_data[field]}")
        
        response_text = "I found some information:\n" + "\n".join(found_info)
        response_text += f"\n\nI still need:\n" + "\n".join([f"• {field}" for field in missing_fields])
        response_text += f"\n\nWhat's the {missing_fields[0].lower()}?"
        
        # Determine next step
        next_step = self._get_next_step_from_missing(missing_fields[0])
        
        return ChatResponse(
            response=response_text,
            intent="student_creation_partial_info",
            data={
                "context": {
                    "handler": "student",
                    "flow": "create_student",
                    "step": next_step,
                    "parsed_data": parsed_data,
                    "missing_fields": missing_fields
                }
            },
            suggestions=[missing_fields[0], "Cancel", "Start over"]
        )
    
    def _get_next_step_from_missing(self, missing_field: str) -> str:
        """Map missing field to flow step"""
        field_map = {
            "Student name": "enter_student_name",
            "Admission number": "enter_admission_no",
            "Guardian name": "enter_guardian_name", 
            "Guardian phone": "enter_guardian_phone",
            "Guardian email": "enter_guardian_email"
        }
        return field_map.get(missing_field, "enter_student_name")
    
    def _start_guided_creation(self) -> ChatResponse:
        """Start the guided student creation conversation"""
        return ChatResponse(
            response="I'll help you create a new student with their guardian information.\n\nWhat's the student's full name?",
            intent="student_creation_enter_name",
            data={
                "context": {
                    "handler": "student",
                    "flow": "create_student",
                    "step": "enter_student_name"
                }
            },
            suggestions=["John Doe", "Mary Smith", "Cancel"]
        )
    
    def handle_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle the student creation flow steps"""
        step = context.get('step')
        
        if step == 'enter_student_name':
            return self._process_student_name(message, context)
        elif step == 'enter_admission_no':
            return self._process_admission_number(message, context)
        elif step == 'enter_guardian_name':
            return self._process_guardian_name(message, context)
        elif step == 'enter_guardian_phone':
            return self._process_guardian_phone(message, context)
        elif step == 'enter_guardian_email':
            return self._process_guardian_email(message, context)
        elif step == 'select_relationship':
            return self._process_relationship(message, context)
        elif step == 'select_class':
            return self._process_class_selection(message, context)
        elif step == 'confirm_creation':
            return self._process_creation_confirmation(message, context)
        
        # Fallback
        return self._start_guided_creation()
    
    def _process_student_name(self, message: str, context: Dict) -> ChatResponse:
        """Process student name input"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Student creation cancelled.",
                intent="student_creation_cancelled",
                data={"context": {}},  # FIXED: Clear context on cancellation
                suggestions=["Create new student", "List students"]
            )
        
        student_name = message.strip()
        
        if not student_name or len(student_name) < 3:
            return ChatResponse(
                response="Please enter a valid student name (at least 3 characters).",
                intent="invalid_student_name",
                data={"context": context},
                suggestions=["John Doe", "Mary Smith", "Cancel"]
            )
        
        # Move to next step
        new_context = context.copy()
        new_context['step'] = 'enter_admission_no'
        new_context['student_name'] = student_name
        
        return ChatResponse(
            response=f"Student name: {student_name}\n\nWhat's their admission number?",
            intent="student_creation_enter_admission",
            data={"context": new_context},
            suggestions=["2025001", "2025123", "Cancel"]
        )
    
    def _process_admission_number(self, message: str, context: Dict) -> ChatResponse:
        """Process admission number input"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Student creation cancelled.",
                intent="student_creation_cancelled",
                data={"context": {}},  # FIXED: Clear context on cancellation
                suggestions=["Create new student", "List students"]
            )
        
        admission_no = message.strip()
        
        if not admission_no or len(admission_no) < 3:
            return ChatResponse(
                response="Please enter a valid admission number (at least 3 characters).",
                intent="invalid_admission_number",
                data={"context": context},
                suggestions=["2025001", "2025123", "Cancel"]
            )
        
        # Check if admission number already exists
        try:
            existing_student = db_execute_safe(self.db,
                "SELECT id FROM students WHERE school_id = :school_id AND admission_no = :admission_no",
                {"school_id": self.school_id, "admission_no": admission_no}
            )
            
            if existing_student:
                return ChatResponse(
                    response=f"A student with admission number {admission_no} already exists. Please choose a different number.",
                    intent="duplicate_admission_number",
                    data={"context": context},
                    suggestions=[f"{admission_no}A", f"{admission_no}1", "Cancel"]
                )
        except Exception as e:
            # Log error but continue - don't block creation for database issues
            print(f"Error checking admission number: {e}")
        
        # Move to guardian information
        new_context = context.copy()
        new_context['step'] = 'enter_guardian_name'
        new_context['admission_no'] = admission_no
        
        return ChatResponse(
            response=f"Admission number: {admission_no}\n\nNow I need the guardian information. What's the guardian's full name?",
            intent="student_creation_enter_guardian_name",
            data={"context": new_context},
            suggestions=["Mary Doe", "John Smith", "Cancel"]
        )
    
    def _process_guardian_name(self, message: str, context: Dict) -> ChatResponse:
        """Process guardian name input"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Student creation cancelled.",
                intent="student_creation_cancelled",
                data={"context": {}},  # FIXED: Clear context on cancellation
                suggestions=["Create new student", "List students"]
            )
        
        guardian_name = message.strip()
        
        if not guardian_name or len(guardian_name) < 3:
            return ChatResponse(
                response="Please enter a valid guardian name (at least 3 characters).",
                intent="invalid_guardian_name",
                data={"context": context},
                suggestions=["Mary Doe", "John Smith", "Cancel"]
            )
        
        # Move to phone number
        new_context = context.copy()
        new_context['step'] = 'enter_guardian_phone'
        new_context['guardian_name'] = guardian_name
        
        return ChatResponse(
            response=f"Guardian name: {guardian_name}\n\nWhat's their phone number?",
            intent="student_creation_enter_guardian_phone",
            data={"context": new_context},
            suggestions=["0701234567", "254701234567", "Cancel"]
        )
    
    def _process_guardian_phone(self, message: str, context: Dict) -> ChatResponse:
        """Process guardian phone input"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Student creation cancelled.",
                intent="student_creation_cancelled",
                data={"context": {}},  # FIXED: Clear context on cancellation
                suggestions=["Create new student", "List students"]
            )
        
        phone = message.strip()
        
        # Basic phone validation
        phone_digits = re.sub(r'[^\d]', '', phone)
        if len(phone_digits) < 9 or len(phone_digits) > 15:
            return ChatResponse(
                response="Please enter a valid phone number (9-15 digits).",
                intent="invalid_guardian_phone",
                data={"context": context},
                suggestions=["0701234567", "254701234567", "Cancel"]
            )
        
        # Move to email
        new_context = context.copy()
        new_context['step'] = 'enter_guardian_email'
        new_context['guardian_phone'] = phone
        
        return ChatResponse(
            response=f"Guardian phone: {phone}\n\nWhat's their email address?",
            intent="student_creation_enter_guardian_email",
            data={"context": new_context},
            suggestions=["guardian@gmail.com", "parent@email.com", "Cancel"]
        )
    
    def _process_guardian_email(self, message: str, context: Dict) -> ChatResponse:
        """Process guardian email input"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Student creation cancelled.",
                intent="student_creation_cancelled",
                data={"context": {}},  # FIXED: Clear context on cancellation
                suggestions=["Create new student", "List students"]
            )
        
        email = message.strip().lower()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        if not re.match(email_pattern, email):
            return ChatResponse(
                response="Please enter a valid email address.",
                intent="invalid_guardian_email",
                data={"context": context},
                suggestions=["guardian@gmail.com", "parent@email.com", "Cancel"]
            )
        
        # Move to relationship
        new_context = context.copy()
        new_context['step'] = 'select_relationship'
        new_context['guardian_email'] = email
        
        relationships = ["Parent", "Guardian", "Relative", "Other"]
        
        response_text = f"Guardian email: {email}\n\nWhat's their relationship to the student?\n\n"
        for i, rel in enumerate(relationships, 1):
            response_text += f"{i}. {rel}\n"
        
        return ChatResponse(
            response=response_text,
            intent="student_creation_select_relationship",
            data={"context": new_context},
            suggestions=relationships + ["Cancel"]
        )
    
    def _process_relationship(self, message: str, context: Dict) -> ChatResponse:
        """Process relationship selection"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Student creation cancelled.",
                intent="student_creation_cancelled",
                data={"context": {}},  # FIXED: Clear context on cancellation
                suggestions=["Create new student", "List students"]
            )
        
        relationships = ["Parent", "Guardian", "Relative", "Other"]
        selected_relationship = None
        
        # Try to match by number
        try:
            option_num = int(message_lower)
            if 1 <= option_num <= len(relationships):
                selected_relationship = relationships[option_num - 1]
        except ValueError:
            pass
        
        # Try to match by name
        if not selected_relationship:
            for rel in relationships:
                if rel.lower() in message_lower:
                    selected_relationship = rel
                    break
        
        if not selected_relationship:
            selected_relationship = "Parent"  # Default
        
        # Get available classes for assignment
        available_classes = self._get_available_classes()
        
        if not available_classes:
            # No classes - create student without class assignment
            new_context = context.copy()
            new_context['step'] = 'confirm_creation'
            new_context['relationship'] = selected_relationship
            new_context['class_assignment'] = None
            
            return self._show_creation_confirmation(new_context)
        
        # Show class selection
        new_context = context.copy()
        new_context['step'] = 'select_class'
        new_context['relationship'] = selected_relationship
        new_context['available_classes'] = available_classes
        
        response_text = f"Relationship: {selected_relationship}\n\nWhich class should I assign the student to?\n\n"
        for i, cls in enumerate(available_classes[:10], 1):
            response_text += f"{i}. {cls['name']} ({cls['level']})\n"
        response_text += f"{len(available_classes[:10]) + 1}. Skip class assignment for now\n"
        
        return ChatResponse(
            response=response_text,
            intent="student_creation_select_class",
            data={"context": new_context},
            suggestions=[cls['name'] for cls in available_classes[:3]] + ["Skip assignment", "Cancel"]
        )
    
    def _process_class_selection(self, message: str, context: Dict) -> ChatResponse:
        """Process class selection"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Student creation cancelled.",
                intent="student_creation_cancelled",
                data={"context": {}},  # FIXED: Clear context on cancellation
                suggestions=["Create new student", "List students"]
            )
        
        available_classes = context.get('available_classes', [])
        selected_class = None
        
        # Check for skip option
        if 'skip' in message_lower or 'no class' in message_lower:
            selected_class = None
        else:
            # Try to match by number
            try:
                option_num = int(message_lower)
                if 1 <= option_num <= len(available_classes):
                    selected_class = available_classes[option_num - 1]
                elif option_num == len(available_classes) + 1:  # Skip option
                    selected_class = None
            except ValueError:
                pass
            
            # Try to match by class name
            if not selected_class and 'skip' not in message_lower:
                for cls in available_classes:
                    if cls['name'].lower() in message_lower or message_lower in cls['name'].lower():
                        selected_class = cls
                        break
        
        # Move to confirmation
        new_context = context.copy()
        new_context['step'] = 'confirm_creation'
        new_context['class_assignment'] = selected_class
        
        return self._show_creation_confirmation(new_context)
    
    def _show_creation_confirmation(self, context: Dict) -> ChatResponse:
        """Show creation confirmation"""
        response_text = "Please confirm the student details:\n\n"
        response_text += f"Student Information:\n"
        response_text += f"• Name: {context.get('student_name')}\n"
        response_text += f"• Admission No: {context.get('admission_no')}\n\n"
        
        response_text += f"Guardian Information:\n"
        response_text += f"• Name: {context.get('guardian_name')}\n"
        response_text += f"• Phone: {context.get('guardian_phone')}\n"
        response_text += f"• Email: {context.get('guardian_email')}\n"
        response_text += f"• Relationship: {context.get('relationship')}\n\n"
        
        class_assignment = context.get('class_assignment')
        if class_assignment:
            response_text += f"Class Assignment: {class_assignment['name']} ({class_assignment['level']})\n\n"
        else:
            response_text += f"Class Assignment: Will be assigned later\n\n"
        
        response_text += "Should I create this student?"
        
        return ChatResponse(
            response=response_text,
            intent="student_creation_confirm",
            data={"context": context},
            suggestions=["Yes, create student", "No, cancel", "Change details"]
        )
    
    def _process_creation_confirmation(self, message: str, context: Dict) -> ChatResponse:
        """Process creation confirmation"""
        message_lower = message.lower().strip()
        
        if message_lower in ['no', 'cancel', 'exit', 'stop', 'no, cancel']:
            return ChatResponse(
                response="Student creation cancelled.",
                intent="student_creation_cancelled",
                data={"context": {}},  # FIXED: Clear context on cancellation
                suggestions=["Create new student", "List students"]
            )
        
        if message_lower in ['change', 'edit', 'modify', 'change details']:
            return ChatResponse(
                response="What would you like to change?",
                intent="student_creation_change_request",
                suggestions=["Student name", "Guardian email", "Class assignment", "Cancel"]
            )
        
        if message_lower in ['yes', 'create', 'confirm', 'yes, create student', 'ok', 'proceed']:
            return self._create_student_with_context(context)
        
        # Default to creation
        return self._create_student_with_context(context)
    
    def _create_student_with_data(self, parsed_data: Dict) -> ChatResponse:
        """Create student from parsed data"""
        context = {
            "student_name": parsed_data["student_name"],
            "admission_no": parsed_data["admission_no"],
            "guardian_name": parsed_data["guardian_name"],
            "guardian_phone": parsed_data["guardian_phone"],
            "guardian_email": parsed_data["guardian_email"],
            "relationship": parsed_data.get("relationship", "Parent"),
            "class_assignment": None
        }
        
        # Try to find class if specified
        if parsed_data.get("class_name"):
            available_classes = self._get_available_classes()
            for cls in available_classes:
                if cls['name'].lower() in parsed_data["class_name"].lower():
                    context["class_assignment"] = cls
                    break
        
        return self._create_student_with_context(context)
    
    def _create_student_with_context(self, context: Dict) -> ChatResponse:
        """Actually create the student and guardian in database"""
        try:
            # Start transaction
            guardian_id = str(uuid.uuid4())
            student_id = str(uuid.uuid4())
            relationship_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Split guardian name
            guardian_name_parts = context['guardian_name'].split()
            guardian_first = guardian_name_parts[0] if guardian_name_parts else "Unknown"
            guardian_last = ' '.join(guardian_name_parts[1:]) if len(guardian_name_parts) > 1 else ""
            
            # Split student name
            student_name_parts = context['student_name'].split()
            student_first = student_name_parts[0] if student_name_parts else "Unknown"
            student_last = ' '.join(student_name_parts[1:]) if len(student_name_parts) > 1 else ""
            
            # Create guardian first
            print(f"Creating guardian with ID: {guardian_id}")
            guardian_rows = db_execute_non_select(self.db, """
                INSERT INTO guardians (id, school_id, first_name, last_name, email, phone, relationship, created_at, updated_at)
                VALUES (:id, :school_id, :first_name, :last_name, :email, :phone, :relationship, :created_at, :updated_at)
            """, {
                "id": guardian_id,
                "school_id": self.school_id,
                "first_name": guardian_first,
                "last_name": guardian_last,
                "email": context['guardian_email'],
                "phone": context['guardian_phone'],
                "relationship": context.get('relationship', 'Parent'),
                "created_at": now,
                "updated_at": now
            })
            
            print(f"Guardian creation result: {guardian_rows} rows affected")
            
            if guardian_rows == 0:
                raise Exception("Failed to create guardian record - no rows affected")
            
            # Create student
            class_assignment = context.get('class_assignment')
            print(f"Creating student with ID: {student_id}, class_id: {class_assignment['id'] if class_assignment else None}")
            
            student_rows = db_execute_non_select(self.db, """
                INSERT INTO students (id, school_id, admission_no, first_name, last_name, primary_guardian_id, class_id, status, created_at, updated_at)
                VALUES (:id, :school_id, :admission_no, :first_name, :last_name, :primary_guardian_id, :class_id, 'ACTIVE', :created_at, :updated_at)
            """, {
                "id": student_id,
                "school_id": self.school_id,
                "admission_no": context['admission_no'],
                "first_name": student_first,
                "last_name": student_last,
                "primary_guardian_id": guardian_id,
                "class_id": class_assignment['id'] if class_assignment else None,
                "created_at": now,
                "updated_at": now
            })
            
            print(f"Student creation result: {student_rows} rows affected")
            
            if student_rows == 0:
                raise Exception("Failed to create student record - no rows affected")
            
            # Create student-guardian relationship
            print(f"Creating relationship with ID: {relationship_id}")
            relationship_rows = db_execute_non_select(self.db, """
                INSERT INTO student_guardians (id, school_id, student_id, guardian_id, created_at, updated_at)
                VALUES (:id, :school_id, :student_id, :guardian_id, :created_at, :updated_at)
            """, {
                "id": relationship_id,
                "school_id": self.school_id,
                "student_id": student_id,
                "guardian_id": guardian_id,
                "created_at": now,
                "updated_at": now
            })
            
            print(f"Relationship creation result: {relationship_rows} rows affected")
            
            # Commit transaction
            self.db.commit()
            print("Transaction committed successfully")
            
            # Build success response
            response_text = f"✅ Student created successfully!\n\n"
            response_text += f"Student Details:\n"
            response_text += f"• Name: {context['student_name']}\n"
            response_text += f"• Admission No: {context['admission_no']}\n"
            response_text += f"• Guardian: {context['guardian_name']} ({context['guardian_email']})\n"
            
            if class_assignment:
                response_text += f"• Class: {class_assignment['name']} ({class_assignment['level']})\n\n"
                response_text += f"Next steps:\n"
                response_text += f"• Enroll student in current term\n"
                response_text += f"• Generate invoice for fees"
            else:
                response_text += f"• Class: Not assigned yet\n\n"
                response_text += f"Next steps:\n"
                response_text += f"• Assign student to a class\n"
                response_text += f"• Enroll in current term"
            
            suggestions = []
            if class_assignment:
                suggestions.extend([
                    f"Enroll {context['student_name']} in current term",
                    f"Generate invoice for {context['admission_no']}"
                ])
            else:
                suggestions.extend([
                    f"Assign {context['student_name']} to a class",
                    "Show available classes"
                ])
            suggestions.extend(["Create another student", "List all students"])
            
            return ChatResponse(
                response=response_text,
                intent="student_created_successfully",
                data={
                    "student_id": student_id,
                    "guardian_id": guardian_id,
                    "student_name": context['student_name'],
                    "admission_no": context['admission_no'],
                    "has_class_assignment": bool(class_assignment),
                    "context": {}  # CRITICAL FIX: Clear context to end flow
                },
                suggestions=suggestions
            )
            
        except Exception as e:
            # Rollback transaction
            try:
                self.db.rollback()
            except:
                pass
            
            error_msg = str(e)
            print(f"Error creating student: {error_msg}")
            
            return ChatResponse(
                response=f"❌ Error creating student: {error_msg}\n\nPlease try again or contact support if the issue persists.",
                intent="student_creation_error",
                data={
                    "error": error_msg,
                    "context": context  # KEEP context for retry attempts
                },
                suggestions=["Try again", "List students", "Contact support"]
            )
    
    def _get_available_classes(self) -> List[Dict]:
        """Get available classes for assignment"""
        try:
            classes = db_execute_safe(self.db,
                """SELECT id, name, level, academic_year
                   FROM classes 
                   WHERE school_id = :school_id 
                   ORDER BY academic_year DESC, level, name""",
                {"school_id": self.school_id}
            )
            
            return [
                {
                    "id": str(cls[0]),
                    "name": cls[1],
                    "level": cls[2],
                    "academic_year": cls[3]
                }
                for cls in classes
            ]
        except Exception as e:
            print(f"Error getting classes: {e}")
            return []