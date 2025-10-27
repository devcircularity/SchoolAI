# app/api/routers/chat/handlers/flows/grade_creation.py - Enhanced with blocks support
import uuid
from typing import Dict
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from ....base import ChatResponse
from ....blocks import (
    text as text_block, kpis, count_kpi, table, status_column, 
    action_row, error_block, empty_state, button_group, button_item
)

class GradeCreationFlow:
    """Enhanced grade creation flow with blocks support and proper context management"""
    
    def __init__(self, db, school_id: str, user_id: str):
        self.db = db
        self.school_id = school_id
        self.user_id = user_id
    
    def initiate_creation(self) -> ChatResponse:
        """Start grade creation process with blocks"""
        context = {
            "handler": "class",
            "flow": "create_grade", 
            "step": "enter_grade_name"
        }
        
        # Build blocks for grade name input
        blocks = []
        
        # Header
        blocks.append(text_block("**Create New Grade**\n\nLet's create a new academic grade for your school. Grades help organize classes by academic level and fee structures."))
        
        # Examples and suggestions
        examples_text = "**Grade Name Examples:**\n"
        examples_text += "• **Early Years:** Nursery, Pre-Primary 1 (PP1), Pre-Primary 2 (PP2)\n"
        examples_text += "• **Primary:** Grade 1, Grade 2, Grade 3, etc.\n"
        examples_text += "• **Secondary:** Form 1, Form 2, Grade 13, Grade 14\n"
        examples_text += "• **Special:** Advanced Class, Remedial, Pre-K"
        
        blocks.append(text_block(examples_text))
        
        # Instructions
        blocks.append(text_block("**Instructions:**\nEnter the name for your new grade. Choose a name that clearly identifies the academic level."))
        
        return ChatResponse(
            response="Enter the name for the new grade",
            intent="grade_creation_enter_name",
            data={"context": context},
            blocks=blocks,
            suggestions=["Grade 13", "Form 1", "Nursery", "Pre-K", "Cancel"]
        )
    
    def initiate_for_class_creation(self, class_context: Dict) -> ChatResponse:
        """Create grade as part of class creation flow with blocks"""
        context = {
            "handler": "class",
            "flow": "create_grade",
            "step": "enter_grade_name", 
            "return_to_class_creation": True,
            "class_context": class_context
        }
        
        blocks = []
        
        # Header with context
        blocks.append(text_block("**Create Grade for Class**\n\nTo create your class, we first need to set up the grade level. What would you like to call this new grade?"))
        
        # Quick examples for class creation context
        blocks.append(text_block("**Common Grade Names:**\n• Grade 13, Grade 14 (Senior Secondary)\n• Form 1, Form 2 (Secondary)\n• Grade 1, Grade 2 (Primary)\n• PP1, PP2 (Early Years)"))
        
        return ChatResponse(
            response="Create a grade for your new class",
            intent="grade_creation_for_class",
            data={"context": context},
            blocks=blocks,
            suggestions=["Grade 13", "Form 1", "Nursery", "Cancel"]
        )
    
    def handle_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle grade creation steps with blocks support"""
        try:
            step = context.get('step')
            
            # Handle cancellation at any step
            if self._is_cancellation(message):
                return self._handle_cancellation(context)
            
            if step == 'enter_grade_name':
                return self._process_grade_name(message, context)
            elif step == 'select_grade_group':
                return self._process_grade_group(message, context)
            elif step == 'confirm_grade_creation':
                return self._process_creation_confirmation(message, context)
            else:
                return self.initiate_creation()
                
        except Exception as e:
            print(f"Grade flow error: {e}")
            return self._create_error_response_with_context(context, str(e))
    
    def _is_cancellation(self, message: str) -> bool:
        """Check if user wants to cancel"""
        message_lower = message.lower().strip()
        return message_lower in ['cancel', 'exit', 'stop', 'quit', 'abort', 'nevermind']
    
    def _handle_cancellation(self, context: Dict) -> ChatResponse:
        """Handle flow cancellation with blocks"""
        # If we came from class creation, return to that flow
        if context.get('return_to_class_creation'):
            from .class_creation import ClassCreationFlow
            class_flow = ClassCreationFlow(self.db, self.school_id, self.user_id)
            return class_flow.initiate_creation()
        
        # Otherwise, clear context completely
        return ChatResponse(
            response="Grade creation cancelled.",
            intent="grade_creation_cancelled",
            data={"context": {}},  # Clear context
            blocks=[
                text_block("**Grade Creation Cancelled**\n\nThe grade creation process has been cancelled. You can start again anytime or explore other options.")
            ],
            suggestions=["List grades", "Create class", "Show grades", "School overview"]
        )
    
    def _process_grade_name(self, message: str, context: Dict) -> ChatResponse:
        """Process grade name input with blocks"""
        try:
            grade_name = message.strip()
            
            if not grade_name or len(grade_name) < 2:
                blocks = [
                    error_block("Invalid Name", "Please enter a valid grade name with at least 2 characters."),
                    text_block("**Examples:** Grade 13, Form 1, Nursery, Pre-Primary 1")
                ]
                
                return ChatResponse(
                    response="Grade name is too short. Please try again.",
                    intent="invalid_grade_name",
                    data={"context": context},
                    blocks=blocks,
                    suggestions=["Grade 13", "Form 1", "Nursery", "Cancel"]
                )
            
            # Check if grade already exists
            existing_grade = self._safe_execute_db_query(
                "SELECT id FROM cbc_level WHERE school_id = :school_id AND label = :label",
                {"school_id": str(self.school_id), "label": grade_name}
            )
            
            if existing_grade:
                blocks = [
                    error_block("Duplicate Name", f"A grade named '{grade_name}' already exists in your school."),
                    text_block(f"**Try these alternatives:**\n• {grade_name} A\n• {grade_name} Advanced\n• {grade_name} Special")
                ]
                
                return ChatResponse(
                    response=f"Grade '{grade_name}' already exists.",
                    intent="duplicate_grade_name",
                    data={"context": context},
                    blocks=blocks,
                    suggestions=[f"{grade_name} A", f"{grade_name} Advanced", "Try different name", "Cancel"]
                )
            
            # Move to group selection with blocks
            grade_groups = [
                "Early Years Education (EYE)",
                "Lower Primary", 
                "Upper Primary",
                "Junior Secondary (JSS)",
                "Senior Secondary",
                "Special Programs",
                "Other"
            ]
            
            new_context = context.copy()
            new_context['step'] = 'select_grade_group'
            new_context['grade_name'] = grade_name
            new_context['grade_groups'] = grade_groups
            
            # Build blocks for group selection
            blocks = []
            blocks.append(text_block(f"**Grade Name: {grade_name}**\n\nNow, which educational group should this grade belong to? This helps organize your grades by academic level."))
            
            # Group selection table
            columns = [
                {"key": "option_number", "label": "#", "width": 60, "align": "center"},
                {"key": "group_name", "label": "Grade Group", "sortable": True},
                {"key": "description", "label": "Description"}
            ]
            
            group_descriptions = {
                "Early Years Education (EYE)": "Ages 3-6, includes Nursery, PP1, PP2",
                "Lower Primary": "Grade 1, Grade 2, Grade 3",
                "Upper Primary": "Grade 4, Grade 5, Grade 6",
                "Junior Secondary (JSS)": "Grade 7, Grade 8, Grade 9",
                "Senior Secondary": "Grade 10, Grade 11, Grade 12, Form 1-4",
                "Special Programs": "Remedial, Advanced, Special needs",
                "Other": "Custom or unique grade levels"
            }
            
            rows = []
            for i, group in enumerate(grade_groups, 1):
                row_data = {
                    "option_number": str(i),
                    "group_name": group,
                    "description": group_descriptions.get(group, "")
                }
                
                # Add action to select this group
                rows.append(
                    action_row(row_data, "query", {"message": str(i)})
                )
            
            blocks.append(
                table(
                    "Educational Groups",
                    columns,
                    rows,
                    actions=[
                        {"label": "Cancel", "type": "query", "payload": {"message": "cancel"}}
                    ]
                )
            )
            
            blocks.append(text_block("**Instructions:**\n• Click on a group or type the number\n• Type the group name directly\n• Choose the group that best fits your grade level"))
            
            return ChatResponse(
                response="Select the educational group for this grade",
                intent="grade_creation_select_group",
                data={"context": new_context},
                blocks=blocks,
                suggestions=grade_groups[:4] + ["Cancel"]
            )
            
        except Exception as e:
            print(f"Error processing grade name: {e}")
            return self._create_error_response_with_context(context, f"Error processing grade name: {str(e)}")
    
    def _process_grade_group(self, message: str, context: Dict) -> ChatResponse:
        """Process grade group selection with blocks"""
        try:
            message_lower = message.lower().strip()
            grade_groups = context.get('grade_groups', [])
            grade_name = context.get('grade_name')
            
            selected_group = None
            
            # Try to match by number
            try:
                option_num = int(message_lower)
                if 1 <= option_num <= len(grade_groups):
                    selected_group = grade_groups[option_num - 1]
            except ValueError:
                pass
            
            # Try to match by group name
            if not selected_group:
                for group in grade_groups:
                    if group.lower() in message_lower or any(word in group.lower() for word in message_lower.split()):
                        selected_group = group
                        break
            
            if not selected_group:
                blocks = [
                    error_block("Invalid Selection", f"I couldn't find the group '{message}'. Please select from the available options."),
                    text_block("**Available Groups:**\n" + "\n".join([f"{i+1}. {group}" for i, group in enumerate(grade_groups)]))
                ]
                
                return ChatResponse(
                    response="Please select a valid group option.",
                    intent="invalid_group_selection",
                    data={"context": context},
                    blocks=blocks,
                    suggestions=grade_groups[:3] + ["Cancel"]
                )
            
            # Move to confirmation with blocks
            new_context = context.copy()
            new_context['step'] = 'confirm_grade_creation'
            new_context['selected_group'] = selected_group
            
            # Build confirmation blocks
            blocks = []
            blocks.append(text_block(f"**Ready to Create Grade**\n\nPlease review the grade details below and confirm:"))
            
            # Grade details table
            detail_columns = [
                {"key": "field", "label": "Field", "width": 150},
                {"key": "value", "label": "Value"}
            ]
            
            detail_rows = [
                {"field": "Grade Name", "value": grade_name},
                {"field": "Grade Group", "value": selected_group},
                {"field": "Fee Structures", "value": "Will create for all 3 terms"},
                {"field": "Fee Items", "value": "Will create basic fee items (Tuition, etc.)"},
                {"field": "Initial Amount", "value": "KES 0 (update after creation)"}
            ]
            
            blocks.append(
                table("Grade Details", detail_columns, detail_rows)
            )
            
            # Additional info
            blocks.append(text_block("**What will be created:**\n• New grade level in your school\n• Fee structures for Terms 1, 2, and 3\n• Basic fee items (Tuition, Sports, etc.) with KES 0 amounts\n• Ready for class creation and student assignments"))
            
            # Add confirmation button group
            confirmation_buttons = [
                button_item("Yes, create it", "query", {"message": "yes"}, "success", "md", "check"),
                button_item("Change name", "query", {"message": "change name"}, "outline", "md", "edit"),
                button_item("Change group", "query", {"message": "change group"}, "outline", "md", "arrow-left"),
                button_item("Cancel", "query", {"message": "cancel"}, "secondary", "md", "x")
            ]
            
            blocks.append(
                button_group(confirmation_buttons, "horizontal", "center")
            )
            
            return ChatResponse(
                response="Confirm grade creation",
                intent="grade_creation_confirm",
                data={"context": new_context},
                blocks=blocks,
                suggestions=["Yes, create it", "No, cancel", "Change name", "Change group"]
            )
            
        except Exception as e:
            print(f"Error processing grade group: {e}")
            return self._create_error_response_with_context(context, f"Error processing grade group: {str(e)}")
    
    def _process_creation_confirmation(self, message: str, context: Dict) -> ChatResponse:
        """Process grade creation confirmation with blocks"""
        try:
            message_lower = message.lower().strip()
            
            if message_lower in ['no', 'no, cancel']:
                return self._handle_cancellation(context)
            
            if message_lower in ['change name', 'edit name']:
                new_context = context.copy()
                new_context['step'] = 'enter_grade_name'
                new_context.pop('grade_name', None)
                return ChatResponse(
                    response="Enter a new name for the grade",
                    intent="grade_creation_change_name",
                    data={"context": new_context},
                    blocks=[text_block("**Change Grade Name**\n\nWhat would you like to name this grade?")],
                    suggestions=["Grade 13", "Form 1", "Nursery", "Cancel"]
                )
            
            if message_lower in ['change group', 'edit group']:
                new_context = context.copy()
                new_context['step'] = 'select_grade_group'
                new_context.pop('selected_group', None)
                return self._process_grade_name(new_context['grade_name'], new_context)
            
            # Default to creation for positive responses
            if (message_lower in ['yes', 'create', 'confirm', 'yes, create it', 'ok', 'proceed'] or 
                not message_lower or
                any(word in message_lower for word in ['yes', 'create', 'go', 'ok'])):
                return self._create_grade_with_blocks(context)
            
            # Ambiguous response
            return ChatResponse(
                response="Please confirm: Should I create this grade?",
                intent="grade_creation_clarify",
                data={"context": context},
                blocks=[text_block("**Confirm Creation**\n\nPlease confirm whether you want to create this grade.")],
                suggestions=["Yes, create it", "No, cancel"]
            )
            
        except Exception as e:
            print(f"Error in grade creation confirmation: {e}")
            return self._create_error_response_with_context(context, f"Error processing confirmation: {str(e)}")
    
    def _create_grade_with_blocks(self, context: Dict) -> ChatResponse:
        """Create the grade with success blocks"""
        try:
            grade_name = context.get('grade_name')
            selected_group = context.get('selected_group')
            
            grade_id = str(uuid.uuid4())
            
            # Create the grade
            rows_affected = self._safe_execute_db_non_select("""
                INSERT INTO cbc_level (id, school_id, label, group_name)
                VALUES (:id, :school_id, :label, :group_name)
            """, {
                "id": grade_id,
                "school_id": str(self.school_id),
                "label": grade_name,
                "group_name": selected_group
            })
            
            if rows_affected > 0:
                # Create fee structures for this grade
                fee_structure_count = self._create_fee_structures_for_grade(grade_name)
                
                self.db.commit()
                
                # Build success blocks
                blocks = []
                
                # Success header
                blocks.append(text_block(f"**Grade Created Successfully! ✅**\n\nYour new grade '{grade_name}' has been created and is ready for classes."))
                
                # Success KPIs
                kpi_items = [
                    {"label": "Grade Created", "value": grade_name, "variant": "success"},
                    {"label": "Grade Group", "value": selected_group, "variant": "primary"},
                    {"label": "Fee Structures", "value": f"{fee_structure_count} Created", "variant": "info"},
                    {"label": "Ready for Classes", "value": "Yes", "variant": "success"}
                ]
                
                blocks.append(kpis(kpi_items))
                
                # Next steps
                blocks.append(text_block("**Next Steps:**\n• **Create Classes** - Add classes for this grade level\n• **Update Fee Amounts** - Set appropriate fees for each term\n• **Assign Students** - Once classes are created"))
                
                # Quick actions table
                action_columns = [
                    {"key": "action", "label": "Quick Action"},
                    {"key": "description", "label": "Description"}
                ]
                
                action_rows = [
                    action_row({
                        "action": f"Create class for {grade_name}",
                        "description": "Add a class to this grade level"
                    }, "query", {"message": f"create class for {grade_name}"}),
                    
                    action_row({
                        "action": f"Update {grade_name} fees",
                        "description": "Set fee amounts for this grade"
                    }, "query", {"message": f"update fees for {grade_name}"}),
                    
                    action_row({
                        "action": "List all grades",
                        "description": "View all grades in school"
                    }, "query", {"message": "list all grades"}),
                    
                    action_row({
                        "action": "Create another grade",
                        "description": "Add more grade levels"
                    }, "query", {"message": "create new grade"})
                ]
                
                blocks.append(
                    table("Quick Actions", action_columns, action_rows)
                )
                
                # If we came from class creation, continue that flow
                if context.get('return_to_class_creation'):
                    blocks.append(text_block("**Returning to Class Creation...**\n\nNow that the grade is created, let's continue with creating your class."))
                    
                    # Small delay message then redirect
                    from .class_creation import ClassCreationFlow
                    class_flow = ClassCreationFlow(self.db, self.school_id, self.user_id)
                    return class_flow.initiate_creation()
                
                suggestions = [
                    f"Create class for {grade_name}",
                    f"Update {grade_name} fees",
                    "List all grades",
                    "Create another grade"
                ]
                
                # SUCCESS: Clear context to terminate flow
                return ChatResponse(
                    response=f"Grade '{grade_name}' created successfully!",
                    intent="grade_created",
                    data={
                        "grade_id": grade_id,
                        "grade_name": grade_name,
                        "group_name": selected_group,
                        "fee_structure_count": fee_structure_count,
                        "context": {}  # CRITICAL: Clear context to end flow
                    },
                    blocks=blocks,
                    suggestions=suggestions
                )
            else:
                # FAILURE: Keep context for retry
                return ChatResponse(
                    response="Failed to create grade. Please try again.",
                    intent="grade_creation_failed",
                    data={"context": context},
                    blocks=[error_block("Creation Failed", "The grade could not be created. Please try again or contact support.")],
                    suggestions=["Try again", "Change details", "Cancel"]
                )
                
        except Exception as e:
            print(f"Error creating grade: {e}")
            try:
                self.db.rollback()
            except:
                pass
            
            # ERROR: Keep context for retry
            return ChatResponse(
                response="Error creating grade. Please try again.",
                intent="grade_creation_error",
                data={"context": context},
                blocks=[error_block("Database Error", f"Error creating grade: {str(e)}")],
                suggestions=["Try again", "Change details", "Cancel"]
            )
    
    def _create_fee_structures_for_grade(self, grade_label: str) -> int:
        """Create fee structures for a new grade across all terms"""
        try:
            current_year = self._get_current_academic_year()
            now = datetime.utcnow()
            fee_structure_count = 0
            
            # Create fee structures for 3 terms
            for term in [1, 2, 3]:
                fs_id = str(uuid.uuid4())
                
                rows_affected = self._safe_execute_db_non_select("""
                    INSERT INTO fee_structures (id, school_id, name, level, term, year, is_default, is_published, created_at, updated_at)
                    VALUES (:id, :school_id, :name, :level, :term, :year, false, false, :created_at, :updated_at)
                """, {
                    "id": fs_id,
                    "school_id": str(self.school_id),
                    "name": f"{grade_label} — Term {term} {current_year}",
                    "level": grade_label,
                    "term": term,
                    "year": current_year,
                    "created_at": now,
                    "updated_at": now
                })
                
                if rows_affected > 0:
                    fee_structure_count += 1
                    # Create basic fee items for this structure
                    self._create_basic_fee_items(fs_id)
            
            return fee_structure_count
                
        except Exception as e:
            print(f"Error creating fee structures: {e}")
            return 0
    
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
        flow = context.get('flow', 'create_grade')
        step = context.get('step', '')
        
        # Generate contextually appropriate suggestions
        suggestions = []
        if step == 'enter_grade_name':
            suggestions = ["Try again", "Show examples", "Cancel"]
        elif step == 'select_grade_group':
            suggestions = ["Show grade groups", "Try again", "Cancel"]
        elif step == 'confirm_grade_creation':
            suggestions = ["Yes, create it", "Change details", "Cancel"]
        else:
            suggestions = ["Try again", "Start over", "Cancel"]
        
        return ChatResponse(
            response=f"I encountered an issue during grade creation. {error_message[:100]}...",
            intent="flow_error_recovery",
            data={"context": context},  # Preserve context for recovery
            blocks=[
                error_block("Flow Error", f"Error in grade creation: {error_message}"),
                text_block("**What would you like to do?**\n\nYou can continue from where we left off or start over.")
            ],
            suggestions=suggestions
        )