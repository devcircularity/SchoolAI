# app/api/routers/chat/handlers/flows/class_creation.py - Enhanced with blocks support
import uuid
from typing import Dict, List
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from ....base import ChatResponse
from ....blocks import (
    text as text_block, kpis, count_kpi, table, status_column, 
    action_row, error_block, empty_state, button_group, button_item
)

class ClassCreationFlow:
    """Enhanced class creation flow with blocks support and robust context management"""
    
    def __init__(self, db, school_id: str, user_id: str):
        self.db = db
        self.school_id = school_id
        self.user_id = user_id
    
    def initiate_creation(self) -> ChatResponse:
        """Start the class creation process with blocks"""
        grades = self._get_available_grades()
        
        if not grades:
            return ChatResponse(
                response="No grades found. You need to create grades first before creating classes.",
                intent="no_grades_for_class",
                blocks=[
                    empty_state("No Grades Found", "Create academic grades first to organize your classes by level"),
                    text_block("**Getting Started:**\n\n1. Create grades (PP1, Grade 1, Form 1, etc.)\n2. Create classes within each grade\n3. Assign students to classes\n\nGrades help organize fee structures and academic progression.")
                ],
                suggestions=["Create new grade", "Setup CBC grades", "Cancel"]
            )
        
        grade_options = [f"{grade['label']} ({grade['group_name']})" for grade in grades]
        grade_options.append("Create new grade")
        
        # Build blocks for grade selection
        blocks = []
        
        # Header
        blocks.append(text_block("**Create New Class**\n\nLet's create a new class for your students. First, select which grade this class will belong to."))
        
        # Grades summary
        grades_by_group = {}
        for grade in grades:
            group = grade['group_name']
            if group not in grades_by_group:
                grades_by_group[group] = []
            grades_by_group[group].append(grade)
        
        # Grade selection table
        columns = [
            {"key": "option_number", "label": "#", "width": 60, "align": "center"},
            {"key": "grade_name", "label": "Grade", "sortable": True},
            {"key": "group_name", "label": "Group", "sortable": True},
            {"key": "existing_classes", "label": "Existing Classes", "align": "center"}
        ]
        
        rows = []
        for i, grade in enumerate(grades, 1):
            # Get existing class count for this grade
            existing_classes = self._get_class_count_for_grade(grade['label'])
            
            row_data = {
                "option_number": str(i),
                "grade_name": grade['label'],
                "group_name": grade['group_name'],
                "existing_classes": existing_classes
            }
            
            # Add action to select this grade
            rows.append(
                action_row(row_data, "query", {"message": str(i)})
            )
        
        # Add "Create new grade" option
        rows.append(
            action_row({
                "option_number": str(len(grades) + 1),
                "grade_name": "Create new grade",
                "group_name": "Setup",
                "existing_classes": "-"
            }, "query", {"message": "create new grade"})
        )
        
        blocks.append(
            table(
                "Available Grades",
                columns,
                rows,
                actions=[
                    {"label": "Create New Grade", "type": "query", "payload": {"message": "create new grade"}},
                    {"label": "Cancel", "type": "query", "payload": {"message": "cancel"}}
                ]
            )
        )
        
        # Instructions
        blocks.append(text_block("**Instructions:**\n• Click on a grade option or type the number\n• Type the grade name directly (e.g., 'Grade 1')\n• Choose 'Create new grade' to add a new academic level"))
        
        # Set up initial context
        context = {
            "handler": "class",
            "flow": "create_class",
            "step": "select_grade",
            "grades": grades,
            "grade_options": grade_options
        }
        
        return ChatResponse(
            response="Select a grade for the new class",
            intent="class_creation_select_grade",
            data={"context": context},
            blocks=blocks,
            suggestions=grade_options[:5] + ["Cancel"]
        )
    
    def handle_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle the class creation flow steps with blocks support"""
        try:
            step = context.get('step')
            print(f"Processing step: {step} with message: '{message}'")
            
            # Handle cancellation at any step
            if self._is_cancellation(message):
                return self._handle_cancellation()
            
            if step == 'select_grade':
                return self._process_grade_selection(message, context)
            elif step == 'enter_class_name':
                return self._process_class_name(message, context)
            elif step == 'confirm_creation':
                return self._process_creation_confirmation(message, context)
            else:
                print(f"Unknown step: {step}, restarting flow")
                return self.initiate_creation()
                
        except Exception as e:
            print(f"Flow error: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response_with_context(context, str(e))
    
    def _is_cancellation(self, message: str) -> bool:
        """Check if user wants to cancel"""
        message_lower = message.lower().strip()
        return message_lower in ['cancel', 'exit', 'stop', 'quit', 'abort', 'nevermind']
    
    def _handle_cancellation(self) -> ChatResponse:
        """Handle flow cancellation with blocks"""
        return ChatResponse(
            response="Class creation cancelled.",
            intent="class_creation_cancelled",
            data={"context": {}},  # Clear context
            blocks=[
                text_block("**Class Creation Cancelled**\n\nThe class creation process has been cancelled. You can start again anytime or explore other options.")
            ],
            suggestions=["List classes", "Create new grade", "Show grades", "School overview"]
        )
    
    def _process_grade_selection(self, message: str, context: Dict) -> ChatResponse:
        """Process grade selection with blocks"""
        try:
            message_lower = message.lower().strip()
            grades = context.get('grades', [])
            grade_options = context.get('grade_options', [])
            
            selected_grade = None
            
            # Check if user selected "Create new grade"
            if self._is_create_new_grade(message_lower, len(grade_options)):
                from .grade_creation import GradeCreationFlow
                grade_flow = GradeCreationFlow(self.db, self.school_id, self.user_id)
                return grade_flow.initiate_for_class_creation(context)
            
            # Try to match by number
            try:
                option_num = int(message_lower)
                if 1 <= option_num <= len(grades):
                    selected_grade = grades[option_num - 1]
            except ValueError:
                pass
            
            # Try to match by grade label
            if not selected_grade:
                for grade in grades:
                    if (grade['label'].lower() in message_lower or 
                        message_lower in grade['label'].lower() or
                        grade['label'].lower() == message_lower):
                        selected_grade = grade
                        break
            
            if not selected_grade:
                blocks = [
                    error_block("Invalid Selection", f"I couldn't find the grade '{message}'. Please select from the available options."),
                    text_block("**Available Options:**\n" + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(grade_options)]))
                ]
                
                return ChatResponse(
                    response="Please select a valid grade option.",
                    intent="invalid_grade_selection",
                    data={"context": context},
                    blocks=blocks,
                    suggestions=grade_options[:3] + ["Cancel"]
                )
            
            # Move to next step with blocks
            new_context = context.copy()
            new_context['step'] = 'enter_class_name'
            new_context['selected_grade'] = selected_grade
            
            # Build name suggestion blocks
            blocks = []
            blocks.append(text_block(f"**Selected Grade: {selected_grade['label']}** ({selected_grade['group_name']})\n\nNow, what would you like to name this class?"))
            
            # Show existing classes for this grade if any
            existing_classes = self._get_existing_classes_for_grade(selected_grade['label'])
            if existing_classes:
                blocks.append(text_block(f"**Existing {selected_grade['label']} classes:** {', '.join(existing_classes)}"))
            
            # Naming suggestions
            suggestions_text = f"**Naming Suggestions:**\n"
            suggestions_text += f"• **By Direction:** {selected_grade['label']} East, {selected_grade['label']} West\n"
            suggestions_text += f"• **By Letter:** {selected_grade['label']} A, {selected_grade['label']} B\n"
            suggestions_text += f"• **By Theme:** {selected_grade['label']} Blue, {selected_grade['label']} Red\n"
            suggestions_text += f"• **By Number:** {selected_grade['label']} 1, {selected_grade['label']} 2"
            
            blocks.append(text_block(suggestions_text))
            
            name_suggestions = [
                f"{selected_grade['label']} East",
                f"{selected_grade['label']} West", 
                f"{selected_grade['label']} A",
                f"{selected_grade['label']} Blue"
            ]
            
            return ChatResponse(
                response=f"Enter a name for the {selected_grade['label']} class",
                intent="class_creation_enter_name",
                data={"context": new_context},
                blocks=blocks,
                suggestions=name_suggestions + ["Cancel"]
            )
            
        except Exception as e:
            print(f"Error in grade selection: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response_with_context(context, f"Error processing grade selection: {str(e)}")
    
    def _process_class_name(self, message: str, context: Dict) -> ChatResponse:
        """Process class name input with blocks"""
        try:
            class_name = message.strip()
            selected_grade = context.get('selected_grade')
            
            if not class_name or len(class_name) < 2:
                blocks = [
                    error_block("Invalid Name", "Please enter a valid class name (at least 2 characters)."),
                    text_block(f"**Suggested names for {selected_grade['label']}:**\n• {selected_grade['label']} East\n• {selected_grade['label']} West\n• {selected_grade['label']} A")
                ]
                
                return ChatResponse(
                    response="Class name is too short. Please enter at least 2 characters.",
                    intent="invalid_class_name",
                    data={"context": context},
                    blocks=blocks,
                    suggestions=[
                        f"{selected_grade['label']} East",
                        f"{selected_grade['label']} West",
                        "Cancel"
                    ]
                )
            
            # Check if class name already exists
            existing_class = self._safe_execute_db_query(
                "SELECT id FROM classes WHERE school_id = :school_id AND name = :name",
                {"school_id": str(self.school_id), "name": class_name}
            )
            
            if existing_class:
                blocks = [
                    error_block("Duplicate Name", f"A class named '{class_name}' already exists in your school."),
                    text_block(f"**Try these alternatives:**\n• {class_name} A\n• {class_name} 1\n• {selected_grade['label']} {class_name}")
                ]
                
                return ChatResponse(
                    response=f"Class name '{class_name}' is already taken.",
                    intent="duplicate_class_name",
                    data={"context": context},
                    blocks=blocks,
                    suggestions=[
                        f"{class_name} A",
                        f"{class_name} 1",
                        f"{selected_grade['label']} {class_name}",
                        "Cancel"
                    ]
                )
            
            # Check fee structures
            existing_fee_structures = self._check_fee_structures_exist(selected_grade['label'])
            
            # Move to confirmation step with blocks
            new_context = context.copy()
            new_context['step'] = 'confirm_creation'
            new_context['class_name'] = class_name
            new_context['will_create_fee_structures'] = not existing_fee_structures
            
            # Build confirmation blocks
            blocks = []
            blocks.append(text_block(f"**Ready to Create Class**\n\nPlease review the details below and confirm:"))
            
            # Class details table
            detail_columns = [
                {"key": "field", "label": "Field", "width": 150},
                {"key": "value", "label": "Value"}
            ]
            
            detail_rows = [
                {"field": "Class Name", "value": class_name},
                {"field": "Grade Level", "value": selected_grade['label']},
                {"field": "Grade Group", "value": selected_grade['group_name']},
                {"field": "Academic Year", "value": str(self._get_current_academic_year())},
            ]
            
            if not existing_fee_structures:
                detail_rows.append({
                    "field": "Fee Structures", 
                    "value": f"Will create new fee structures for {selected_grade['label']} (3 terms)"
                })
                blocks.append(text_block(f"**Note:** This will be the first class for {selected_grade['label']}, so I'll automatically create fee structures for this grade across all terms with default amounts of KES 0 (you can update them later)."))
            else:
                detail_rows.append({
                    "field": "Fee Structure", 
                    "value": f"Will link to existing {selected_grade['label']} fee structures"
                })
            
            blocks.append(
                table("Class Details", detail_columns, detail_rows)
            )
            
            # Add confirmation button group
            confirmation_buttons = [
                button_item("Yes, create it", "query", {"message": "yes"}, "success", "md", "check"),
                button_item("Change name", "query", {"message": "change name"}, "outline", "md", "edit"),
                button_item("Change grade", "query", {"message": "change grade"}, "outline", "md", "arrow-left"),
                button_item("Cancel", "query", {"message": "cancel"}, "secondary", "md", "x")
            ]
            
            blocks.append(
                button_group(confirmation_buttons, "horizontal", "center")
            )
            
            return ChatResponse(
                response="Confirm class creation",
                intent="class_creation_confirm",
                data={"context": new_context},
                blocks=blocks,
                suggestions=["Yes, create it", "No", "Change name", "Change grade"]
            )
            
        except Exception as e:
            print(f"Error in class name processing: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response_with_context(context, f"Error processing class name: {str(e)}")
    
    def _process_creation_confirmation(self, message: str, context: Dict) -> ChatResponse:
        """Process final confirmation and create the class with success blocks"""
        try:
            message_lower = message.lower().strip()
            print(f"Processing confirmation with message: '{message_lower}'")
            
            # Handle explicit cancellation
            if message_lower in ['no', 'no, cancel', 'cancel']:
                return self._handle_cancellation()
            
            # Handle modification requests
            if message_lower in ['change name', 'edit name']:
                new_context = context.copy()
                new_context['step'] = 'enter_class_name'
                return ChatResponse(
                    response="Enter a new name for the class",
                    intent="class_creation_change_name",
                    data={"context": new_context},
                    blocks=[text_block("**Change Class Name**\n\nEnter a new name for the class:")],
                    suggestions=[
                        f"{context['selected_grade']['label']} East",
                        f"{context['selected_grade']['label']} West",
                        "Cancel"
                    ]
                )
            
            if message_lower in ['change grade', 'edit grade']:
                return self.initiate_creation()
            
            # Positive response handling
            positive_responses = [
                'yes', 'y', 'create', 'confirm', 'yes, create it', 'ok', 'okay', 
                'proceed', 'go ahead', 'do it', 'continue', 'sure', 'yep', 'yeah'
            ]
            
            # Default to creation for positive responses
            if (message_lower in positive_responses or 
                not message_lower or
                any(word in message_lower for word in ['yes', 'create', 'go', 'ok'])):
                
                return self._create_class_with_blocks(context)
            
            # Handle negative responses
            if any(word in message_lower for word in ['no', 'cancel', 'stop', 'abort', 'quit', 'exit']):
                return self._handle_cancellation()
            
            # Ambiguous response
            return ChatResponse(
                response="Please confirm: Should I create this class?",
                intent="class_creation_clarify",
                data={"context": context},
                blocks=[text_block("**Confirm Creation**\n\nPlease confirm whether you want to create this class.")],
                suggestions=["Yes", "No"]
            )
            
        except Exception as e:
            print(f"Error in creation confirmation: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response_with_context(context, f"Error processing confirmation: {str(e)}")
    
    def _create_class_with_blocks(self, context: Dict) -> ChatResponse:
        """Create the class with success blocks"""
        try:
            class_name = context.get('class_name')
            selected_grade = context.get('selected_grade')
            will_create_fee_structures = context.get('will_create_fee_structures', False)
            
            print(f"Creating class: {class_name} for grade: {selected_grade['label']}")
            
            # Get current academic year
            current_year = self._get_current_academic_year()
            
            # Create the class with explicit transaction management
            class_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            try:
                # Step 1: Create fee structures if needed
                fee_structure_ids = []
                if will_create_fee_structures:
                    print(f"Creating fee structures for grade: {selected_grade['label']}")
                    fee_structure_ids = self._create_fee_structures_for_grade(selected_grade['label'], current_year)
                    print(f"Created {len(fee_structure_ids)} fee structures")
                
                # Step 2: Create the class
                rows_affected = self._safe_execute_db_non_select("""
                    INSERT INTO classes (id, school_id, name, level, academic_year, stream, created_at, updated_at)
                    VALUES (:id, :school_id, :name, :level, :academic_year, :stream, :created_at, :updated_at)
                """, {
                    "id": class_id,
                    "school_id": str(self.school_id),
                    "name": class_name,
                    "level": selected_grade['label'],
                    "academic_year": current_year,
                    "stream": None,
                    "created_at": now,
                    "updated_at": now
                })
                
                print(f"Class insert affected {rows_affected} rows")
                
                if rows_affected > 0:
                    self.db.commit()
                    print("Transaction committed successfully")
                    
                    # Build success blocks
                    blocks = []
                    
                    # Success header
                    blocks.append(text_block(f"**Class Created Successfully! ✅**\n\nYour new class '{class_name}' has been created and is ready for students."))
                    
                    # Class details KPIs
                    kpi_items = [
                        {"label": "Class Created", "value": class_name, "variant": "success"},
                        {"label": "Grade Level", "value": selected_grade['label'], "variant": "primary"},
                        {"label": "Academic Year", "value": str(current_year), "variant": "info"}
                    ]
                    
                    if will_create_fee_structures:
                        kpi_items.append({
                            "label": "Fee Structures", 
                            "value": f"{len(fee_structure_ids)} Created", 
                            "variant": "warning"
                        })
                    
                    blocks.append(kpis(kpi_items))
                    
                    # Next steps
                    next_steps = []
                    if will_create_fee_structures:
                        next_steps.extend([
                            "**Update Fee Amounts** - Fee structures were created with KES 0 amounts",
                            "**Assign Students** - Add students to this class",
                            "**Generate Invoices** - Once fees are set and students assigned"
                        ])
                    else:
                        next_steps.extend([
                            "**Assign Students** - Add students to this class",
                            "**Enroll in Current Term** - If you have an active academic term",
                            "**Generate Invoices** - Once students are assigned and enrolled"
                        ])
                    
                    blocks.append(text_block("**Next Steps:**\n" + "\n".join([f"• {step}" for step in next_steps])))
                    
                    # Quick actions table
                    action_columns = [
                        {"key": "action", "label": "Quick Action"},
                        {"key": "description", "label": "Description"}
                    ]
                    
                    action_rows = []
                    if will_create_fee_structures:
                        action_rows.append(
                            action_row({
                                "action": f"Update {selected_grade['label']} fees",
                                "description": "Set fee amounts for the grade"
                            }, "query", {"message": f"update fees for {selected_grade['label']}"})
                        )
                    
                    action_rows.extend([
                        action_row({
                            "action": f"Assign students to {class_name}",
                            "description": "Add students to this class"
                        }, "query", {"message": f"assign students to {class_name}"}),
                        
                        action_row({
                            "action": "List all classes",
                            "description": "View all classes in school"
                        }, "query", {"message": "list all classes"}),
                        
                        action_row({
                            "action": "Create another class",
                            "description": "Add more classes"
                        }, "query", {"message": "create new class"})
                    ])
                    
                    blocks.append(
                        table("Quick Actions", action_columns, action_rows)
                    )
                    
                    suggestions = []
                    if will_create_fee_structures:
                        suggestions.append(f"Update fees for {selected_grade['label']}")
                    
                    suggestions.extend([
                        f"Assign students to {class_name}",
                        "List all classes",
                        "Create another class"
                    ])
                    
                    # Success response with EMPTY context to terminate flow
                    return ChatResponse(
                        response=f"Class '{class_name}' created successfully!",
                        intent="class_created_success",
                        data={
                            "class_id": class_id,
                            "class_name": class_name,
                            "grade": selected_grade,
                            "academic_year": current_year,
                            "fee_structures_created": will_create_fee_structures,
                            "fee_structure_count": len(fee_structure_ids),
                            "context": {}  # EMPTY CONTEXT = FLOW COMPLETE
                        },
                        blocks=blocks,
                        suggestions=suggestions
                    )
                else:
                    # Creation failed
                    print("Class creation failed - no rows affected")
                    self.db.rollback()
                    
                    return ChatResponse(
                        response="Failed to create class. Please try again.",
                        intent="class_creation_failed",
                        data={"context": context},
                        blocks=[error_block("Creation Failed", "The class could not be created. Please try again or contact support.")],
                        suggestions=["Try again", "Change details", "Cancel"]
                    )
                    
            except Exception as db_error:
                print(f"Database error during class creation: {db_error}")
                import traceback
                traceback.print_exc()
                
                try:
                    self.db.rollback()
                except:
                    pass
                
                return ChatResponse(
                    response="Error creating class. Please try again.",
                    intent="class_creation_db_error",
                    data={"context": context},
                    blocks=[error_block("Database Error", f"Error creating class: {str(db_error)}")],
                    suggestions=["Try again", "Change details", "Cancel"]
                )
                
        except Exception as e:
            print(f"Unexpected error in _create_class_with_blocks: {e}")
            import traceback
            traceback.print_exc()
            
            return ChatResponse(
                response="Unexpected error creating class.",
                intent="class_creation_unexpected_error", 
                data={"context": context},
                blocks=[error_block("Unexpected Error", f"Unexpected error: {str(e)}")],
                suggestions=["Try again", "Start over", "Cancel"]
            )
    
    # Helper methods (keeping existing functionality)
    def _get_class_count_for_grade(self, grade_label: str) -> int:
        """Get number of existing classes for a grade"""
        try:
            result = self._safe_execute_db_query(
                "SELECT COUNT(*) FROM classes WHERE school_id = :school_id AND level = :level",
                {"school_id": str(self.school_id), "level": grade_label}
            )
            return result[0][0] if result else 0
        except:
            return 0
    
    def _get_existing_classes_for_grade(self, grade_label: str) -> List[str]:
        """Get names of existing classes for a grade"""
        try:
            result = self._safe_execute_db_query(
                "SELECT name FROM classes WHERE school_id = :school_id AND level = :level ORDER BY name",
                {"school_id": str(self.school_id), "level": grade_label}
            )
            return [row[0] for row in result] if result else []
        except:
            return []
    
    def _create_fee_structures_for_grade(self, grade_label: str, academic_year: int) -> list:
        """Create fee structures for a grade when first class is created"""
        try:
            fee_structure_ids = []
            now = datetime.utcnow()
            
            # Create fee structures for 3 terms
            for term in [1, 2, 3]:
                fs_id = str(uuid.uuid4())
                
                rows_affected = self._safe_execute_db_non_select("""
                    INSERT INTO fee_structures (id, school_id, name, level, term, year, is_default, is_published, created_at, updated_at)
                    VALUES (:id, :school_id, :name, :level, :term, :year, false, false, :created_at, :updated_at)
                """, {
                    "id": fs_id,
                    "school_id": str(self.school_id),
                    "name": f"{grade_label} — Term {term} {academic_year}",
                    "level": grade_label,
                    "term": term,
                    "year": academic_year,
                    "created_at": now,
                    "updated_at": now
                })
                
                if rows_affected > 0:
                    fee_structure_ids.append(fs_id)
                    # Create basic fee items for this structure
                    self._create_basic_fee_items(fs_id)
                
            return fee_structure_ids
            
        except Exception as e:
            print(f"Error creating fee structures: {e}")
            return []
    
    def _create_basic_fee_items(self, fee_structure_id: str):
        """Create basic fee items for a fee structure"""
        try:
            now = datetime.utcnow()
            
            # Basic fee items
            fee_items = [
                ("Tuition", "TUITION", False, "TERM"),
                ("Sports & Games", "COCURRICULAR", True, "TERM"),
                ("Computer Club", "COCURRICULAR", True, "TERM"),
                ("Workbooks", "OTHER", False, "ANNUAL"),
            ]
            
            for item_name, category, is_optional, billing_cycle in fee_items:
                item_id = str(uuid.uuid4())
                
                self._safe_execute_db_non_select("""
                    INSERT INTO fee_items (id, school_id, fee_structure_id, class_id, item_name, amount, is_optional, category, billing_cycle, created_at, updated_at)
                    VALUES (:id, :school_id, :fee_structure_id, NULL, :item_name, 0, :is_optional, :category, :billing_cycle, :created_at, :updated_at)
                """, {
                    "id": item_id,
                    "school_id": str(self.school_id),
                    "fee_structure_id": fee_structure_id,
                    "item_name": item_name,
                    "is_optional": is_optional,
                    "category": category,
                    "billing_cycle": billing_cycle,
                    "created_at": now,
                    "updated_at": now
                })
                
        except Exception as e:
            print(f"Error creating fee items: {e}")
    
    def _check_fee_structures_exist(self, grade_label: str) -> bool:
        """Check if fee structures already exist for this grade"""
        try:
            result = self._safe_execute_db_query(
                "SELECT COUNT(*) FROM fee_structures WHERE school_id = :school_id AND level = :level",
                {"school_id": str(self.school_id), "level": grade_label}
            )
            return result[0][0] > 0 if result else False
        except:
            return False
    
    def _get_available_grades(self) -> List[Dict]:
        """Get all available grades for the school with proper educational ordering"""
        return self._safe_execute_db_query(
            """SELECT id, label, group_name 
               FROM cbc_level 
               WHERE school_id = :school_id 
               ORDER BY 
                   CASE group_name
                       WHEN 'Early Years Education (EYE)' THEN 1
                       WHEN 'Lower Primary' THEN 2
                       WHEN 'Upper Primary' THEN 3
                       WHEN 'Junior Secondary (JSS)' THEN 4
                       WHEN 'Senior Secondary' THEN 5
                       ELSE 6
                   END,
                   CASE 
                       WHEN label = 'PP1' THEN 1
                       WHEN label = 'PP2' THEN 2
                       WHEN label LIKE 'Grade %' THEN CAST(SUBSTRING(label FROM 7) AS INTEGER)
                       ELSE 999
                   END""",
            {"school_id": str(self.school_id)},
            transform_result=lambda rows: [
                {
                    "id": str(grade[0]),
                    "label": grade[1],
                    "group_name": grade[2]
                }
                for grade in rows
            ]
        )
    
    def _get_current_academic_year(self) -> int:
        """Get the current academic year"""
        try:
            result = self._safe_execute_db_query(
                "SELECT year FROM academic_years WHERE school_id = :school_id ORDER BY year DESC LIMIT 1",
                {"school_id": str(self.school_id)}
            )
            return result[0][0] if result else datetime.now().year
        except:
            return datetime.now().year
    
    def _is_create_new_grade(self, message_lower: str, total_options: int) -> bool:
        """Check if user wants to create a new grade"""
        return (
            'create' in message_lower and 'grade' in message_lower or
            message_lower in ['create new grade', str(total_options)]
        )
    
    def _safe_execute_db_query(self, query: str, params: dict, transform_result=None):
        """Execute database query with error handling"""
        try:
            result = self.db.execute(text(query), params)
            rows = result.fetchall()
            return transform_result(rows) if transform_result else rows
        except SQLAlchemyError as e:
            print(f"Database query error: {e}")
            try:
                self.db.rollback()
            except:
                pass
            return [] if transform_result else []
        except Exception as e:
            print(f"Unexpected error in query: {e}")
            return [] if transform_result else []
    
    def _safe_execute_db_non_select(self, query: str, params: dict) -> int:
        """Execute non-SELECT queries safely"""
        try:
            result = self.db.execute(text(query), params)
            return result.rowcount
        except SQLAlchemyError as e:
            print(f"Database non-select error: {e}")
            try:
                self.db.rollback()
            except:
                pass
            return 0
        except Exception as e:
            print(f"Unexpected error in non-select: {e}")
            return 0
    
    def _create_error_response_with_context(self, context: Dict, error_message: str) -> ChatResponse:
        """Create error response while preserving context for recovery"""
        flow = context.get('flow', 'create_class')
        step = context.get('step', '')
        
        # Generate contextually appropriate suggestions
        suggestions = []
        if step == 'select_grade':
            suggestions = ["Show available grades", "Create new grade", "Try again", "Cancel"]
        elif step == 'enter_class_name':
            suggestions = ["Try different name", "Go back to grade selection", "Cancel"]
        elif step == 'confirm_creation':
            suggestions = ["Yes, create it", "Change details", "Cancel"]
        else:
            suggestions = ["Try again", "Start over", "Cancel"]
        
        return ChatResponse(
            response=f"I encountered an issue during class creation. {error_message[:100]}...",
            intent="flow_error_recovery",
            data={"context": context},  # Preserve context for recovery
            blocks=[
                error_block("Flow Error", f"Error in class creation: {error_message}"),
                text_block("**What would you like to do?**\n\nYou can continue from where we left off or start over.")
            ],
            suggestions=suggestions
        )