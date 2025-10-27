# app/api/routers/chat/handlers/flows/fee_update.py - Fee amount update flow with context management
import re
from typing import Dict, List, Optional
from ....base import ChatResponse, db_execute_safe, db_execute_non_select

class FeeUpdateFlow:
    """Handles multi-step fee amount updates with proper context management"""
    
    def __init__(self, db, school_id: str, user_id: str):
        self.db = db
        self.school_id = school_id
        self.user_id = user_id
    
    def initiate_update(self, message: str = None) -> ChatResponse:
        """Start fee update process - attempt smart parsing first"""
        if message:
            # Try to parse complete information from single command
            parsed_data = self._smart_parse_fee_update(message)
            
            if parsed_data["completeness"] >= 80:
                return self._handle_parsed_update(parsed_data)
        
        # Fall back to guided conversation
        return self._start_guided_update()
    
    def _smart_parse_fee_update(self, message: str) -> Dict:
        """Attempt to extract fee update info from message"""
        parsed = {
            "fee_item": None,
            "grade_level": None,
            "amount": None,
            "scope": None,
            "completeness": 0
        }
        
        message_lower = message.lower()
        
        # Extract amount (most reliable)
        amount_match = re.search(r'(?:to|=)\s*(\d+(?:\.\d{1,2})?)', message_lower)
        if amount_match:
            parsed["amount"] = float(amount_match.group(1))
        
        # Extract grade level if present
        grade_patterns = [
            r'for\s+(grade\s*\d+|pp\s*\d+|class\s*\d+)',
            r'(grade\s+\d+|pp\s*\d+)',
        ]
        
        for pattern in grade_patterns:
            grade_match = re.search(pattern, message_lower)
            if grade_match:
                parsed["grade_level"] = grade_match.group(1).strip().replace(' ', ' ')
                parsed["scope"] = "grade_specific"
                break
        
        if not parsed["grade_level"]:
            parsed["scope"] = "all_grades"
        
        # Extract fee item name
        fee_patterns = [
            r'(?:set|update|change)\s+(.+?)\s+(?:for|to)',
            r'(?:set|update|change)\s+(.+?)$',
        ]
        
        for pattern in fee_patterns:
            fee_match = re.search(pattern, message_lower)
            if fee_match:
                fee_item = fee_match.group(1).strip()
                # Clean up common words
                fee_item = re.sub(r'\b(fee|fees|amount)\b', '', fee_item).strip()
                if fee_item and len(fee_item) >= 3:
                    parsed["fee_item"] = fee_item
                break
        
        # Calculate completeness
        required_fields = ["fee_item", "amount"]
        filled_fields = sum(1 for field in required_fields if parsed[field])
        parsed["completeness"] = (filled_fields / len(required_fields)) * 100
        
        return parsed
    
    def _handle_parsed_update(self, parsed_data: Dict) -> ChatResponse:
        """Handle partially or fully parsed fee update data"""
        missing_fields = []
        
        if not parsed_data["fee_item"]:
            missing_fields.append("fee item name")
        if not parsed_data["amount"]:
            missing_fields.append("amount")
        
        if not missing_fields:
            # All required fields present - execute update
            return self._execute_fee_update_from_data(parsed_data)
        
        # Some fields missing - guide user
        found_info = []
        if parsed_data["fee_item"]:
            found_info.append(f"• Fee item: {parsed_data['fee_item']}")
        if parsed_data["amount"]:
            found_info.append(f"• Amount: KES {parsed_data['amount']:,.2f}")
        if parsed_data["grade_level"]:
            found_info.append(f"• Grade: {parsed_data['grade_level']}")
        else:
            found_info.append("• Scope: All active grades")
        
        response_text = "I found some information:\n" + "\n".join(found_info)
        response_text += f"\n\nI still need: {missing_fields[0]}"
        response_text += f"\n\nWhat's the {missing_fields[0]}?"
        
        # Determine next step
        next_step = "enter_fee_item" if "fee item" in missing_fields[0] else "enter_amount"
        
        return ChatResponse(
            response=response_text,
            intent="fee_update_partial_info",
            data={
                "context": {
                    "handler": "fee",
                    "flow": "update_fee",
                    "step": next_step,
                    "parsed_data": parsed_data,
                    "missing_fields": missing_fields
                }
            },
            suggestions=["Tuition", "Lunch", "Transport", "Cancel"]
        )
    
    def _start_guided_update(self) -> ChatResponse:
        """Start the guided fee update conversation"""
        return ChatResponse(
            response="I'll help you update fee amounts.\n\nWhich fee item would you like to update? (e.g., Tuition, Lunch, Transport, etc.)",
            intent="fee_update_enter_item",
            data={
                "context": {
                    "handler": "fee",
                    "flow": "update_fee",
                    "step": "enter_fee_item"
                }
            },
            suggestions=["Tuition", "Lunch", "Transport", "Sports & Games", "Cancel"]
        )
    
    def handle_flow(self, message: str, context: Dict) -> ChatResponse:
        """Handle the fee update flow steps"""
        step = context.get('step')
        
        if step == 'enter_fee_item':
            return self._process_fee_item(message, context)
        elif step == 'select_scope':
            return self._process_scope_selection(message, context)
        elif step == 'select_grade':
            return self._process_grade_selection(message, context)
        elif step == 'enter_amount':
            return self._process_amount(message, context)
        elif step == 'confirm_update':
            return self._process_update_confirmation(message, context)
        
        # Fallback
        return self._start_guided_update()
    
    def _process_fee_item(self, message: str, context: Dict) -> ChatResponse:
        """Process fee item input"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Fee update cancelled.",
                intent="fee_update_cancelled",
                data={"context": {}},  # Clear context
                suggestions=["Show fee structures", "Update different fee"]
            )
        
        fee_item = message.strip()
        
        if not fee_item or len(fee_item) < 3:
            return ChatResponse(
                response="Please enter a valid fee item name (at least 3 characters).",
                intent="invalid_fee_item",
                data={"context": context},
                suggestions=["Tuition", "Lunch", "Transport", "Cancel"]
            )
        
        # Normalize and check if fee item exists in active structures
        fee_item_normalized = self._normalize_fee_item_name(fee_item)
        existing_items = self._find_existing_fee_items(fee_item_normalized)
        
        if not existing_items:
            return ChatResponse(
                response=f"No fee items found matching '{fee_item}' in active grades.\n\nPlease choose from available fee items or check the spelling.",
                intent="fee_item_not_found",
                data={"context": context},
                suggestions=self._get_available_fee_items() + ["Cancel"]
            )
        
        # Move to scope selection
        new_context = context.copy()
        new_context['step'] = 'select_scope'
        new_context['fee_item'] = fee_item_normalized
        new_context['existing_items'] = existing_items
        
        # Show which grades have this fee item
        grades_with_item = list(set(item['level'] for item in existing_items))
        
        response_text = f"Fee item: {fee_item_normalized}\n\n"
        response_text += f"This fee exists in {len(grades_with_item)} active grades:\n"
        for grade in sorted(grades_with_item)[:5]:
            response_text += f"• {grade}\n"
        if len(grades_with_item) > 5:
            response_text += f"... and {len(grades_with_item) - 5} more\n"
        
        response_text += f"\nUpdate scope:\n"
        response_text += f"1. All active grades ({len(grades_with_item)} grades)\n"
        response_text += f"2. Specific grade only\n"
        
        return ChatResponse(
            response=response_text,
            intent="fee_update_select_scope",
            data={"context": new_context},
            suggestions=["All grades", "Specific grade", "Cancel"]
        )
    
    def _process_scope_selection(self, message: str, context: Dict) -> ChatResponse:
        """Process update scope selection"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Fee update cancelled.",
                intent="fee_update_cancelled",
                data={"context": {}},  # Clear context
                suggestions=["Show fee structures", "Update different fee"]
            )
        
        # Determine scope
        if any(word in message_lower for word in ['all', 'all grades', '1', 'everywhere']):
            scope = "all_grades"
            grade_level = None
        elif any(word in message_lower for word in ['specific', '2', 'one grade', 'single']):
            scope = "grade_specific"
            grade_level = None
        else:
            scope = "all_grades"  # Default
            grade_level = None
        
        if scope == "grade_specific":
            # Move to grade selection
            new_context = context.copy()
            new_context['step'] = 'select_grade'
            new_context['scope'] = scope
            
            existing_items = context.get('existing_items', [])
            grades_with_item = list(set(item['level'] for item in existing_items))
            
            response_text = f"Which grade would you like to update?\n\n"
            for i, grade in enumerate(sorted(grades_with_item), 1):
                amounts = [item['amount'] for item in existing_items if item['level'] == grade]
                current_amount = amounts[0] if amounts else 0
                response_text += f"{i}. {grade} (currently KES {current_amount:,.2f})\n"
            
            new_context['available_grades'] = sorted(grades_with_item)
            
            return ChatResponse(
                response=response_text,
                intent="fee_update_select_grade",
                data={"context": new_context},
                suggestions=sorted(grades_with_item)[:3] + ["Cancel"]
            )
        else:
            # Move to amount entry
            new_context = context.copy()
            new_context['step'] = 'enter_amount'
            new_context['scope'] = scope
            new_context['grade_level'] = grade_level
            
            existing_items = context.get('existing_items', [])
            amounts = [item['amount'] for item in existing_items]
            min_amount = min(amounts) if amounts else 0
            max_amount = max(amounts) if amounts else 0
            
            response_text = f"Current amounts for {context['fee_item']}:\n"
            if min_amount == max_amount:
                response_text += f"All grades: KES {min_amount:,.2f}\n"
            else:
                response_text += f"Range: KES {min_amount:,.2f} - {max_amount:,.2f}\n"
            
            response_text += f"\nWhat should be the new amount for all grades?"
            
            return ChatResponse(
                response=response_text,
                intent="fee_update_enter_amount_all",
                data={"context": new_context},
                suggestions=["25000", "15000", "5000", "Cancel"]
            )
    
    def _process_grade_selection(self, message: str, context: Dict) -> ChatResponse:
        """Process grade selection for specific updates"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Fee update cancelled.",
                intent="fee_update_cancelled",
                data={"context": {}},  # Clear context
                suggestions=["Show fee structures", "Update different fee"]
            )
        
        available_grades = context.get('available_grades', [])
        selected_grade = None
        
        # Try to match by number
        try:
            option_num = int(message_lower)
            if 1 <= option_num <= len(available_grades):
                selected_grade = available_grades[option_num - 1]
        except ValueError:
            pass
        
        # Try to match by grade name
        if not selected_grade:
            for grade in available_grades:
                if grade.lower() in message_lower or message_lower in grade.lower():
                    selected_grade = grade
                    break
        
        if not selected_grade:
            return ChatResponse(
                response="I couldn't find that grade. Please select from the available options:",
                intent="invalid_grade_selection",
                data={"context": context},
                suggestions=available_grades[:3] + ["Cancel"]
            )
        
        # Move to amount entry
        new_context = context.copy()
        new_context['step'] = 'enter_amount'
        new_context['grade_level'] = selected_grade
        
        # Get current amount for this grade
        existing_items = context.get('existing_items', [])
        current_amount = next(
            (item['amount'] for item in existing_items if item['level'] == selected_grade),
            0
        )
        
        response_text = f"Grade: {selected_grade}\n"
        response_text += f"Fee: {context['fee_item']}\n"
        response_text += f"Current amount: KES {current_amount:,.2f}\n\n"
        response_text += f"What should be the new amount?"
        
        return ChatResponse(
            response=response_text,
            intent="fee_update_enter_amount_specific",
            data={"context": new_context},
            suggestions=["25000", "15000", "5000", "Cancel"]
        )
    
    def _process_amount(self, message: str, context: Dict) -> ChatResponse:
        """Process amount input"""
        message_lower = message.lower().strip()
        
        if message_lower in ['cancel', 'exit', 'stop']:
            return ChatResponse(
                response="Fee update cancelled.",
                intent="fee_update_cancelled",
                data={"context": {}},  # Clear context
                suggestions=["Show fee structures", "Update different fee"]
            )
        
        # Parse amount
        try:
            # Extract numeric value
            amount_match = re.search(r'(\d+(?:\.\d{1,2})?)', message)
            if amount_match:
                amount = float(amount_match.group(1))
            else:
                raise ValueError("No numeric amount found")
            
            if amount < 0:
                raise ValueError("Amount cannot be negative")
            
        except (ValueError, AttributeError):
            return ChatResponse(
                response="Please enter a valid amount (numbers only, e.g., 25000 or 15000.50).",
                intent="invalid_amount",
                data={"context": context},
                suggestions=["25000", "15000", "5000", "Cancel"]
            )
        
        # Move to confirmation
        new_context = context.copy()
        new_context['step'] = 'confirm_update'
        new_context['amount'] = amount
        
        return self._show_update_confirmation(new_context)
    
    def _show_update_confirmation(self, context: Dict) -> ChatResponse:
        """Show update confirmation"""
        fee_item = context.get('fee_item')
        amount = context.get('amount')
        scope = context.get('scope')
        grade_level = context.get('grade_level')
        
        response_text = "Please confirm the fee update:\n\n"
        response_text += f"Fee Item: {fee_item}\n"
        response_text += f"New Amount: KES {amount:,.2f}\n"
        
        if scope == "grade_specific" and grade_level:
            response_text += f"Scope: {grade_level} only\n"
        else:
            response_text += f"Scope: All active grades\n"
        
        # Show what will be affected
        existing_items = context.get('existing_items', [])
        if scope == "grade_specific" and grade_level:
            affected_items = [item for item in existing_items if item['level'] == grade_level]
        else:
            affected_items = existing_items
        
        response_text += f"\nThis will update {len(affected_items)} fee items across {len(set(item['level'] for item in affected_items))} grades.\n"
        response_text += f"\nProceed with the update?"
        
        return ChatResponse(
            response=response_text,
            intent="fee_update_confirm",
            data={"context": context},
            suggestions=["Yes, update fees", "No, cancel", "Change amount"]
        )
    
    def _process_update_confirmation(self, message: str, context: Dict) -> ChatResponse:
        """Process update confirmation"""
        message_lower = message.lower().strip()
        
        if message_lower in ['no', 'cancel', 'exit', 'stop', 'no, cancel']:
            return ChatResponse(
                response="Fee update cancelled.",
                intent="fee_update_cancelled",
                data={"context": {}},  # Clear context
                suggestions=["Update different fee", "Show fee structures"]
            )
        
        if message_lower in ['change', 'edit', 'modify', 'change amount']:
            new_context = context.copy()
            new_context['step'] = 'enter_amount'
            return ChatResponse(
                response="What should be the new amount?",
                intent="fee_update_change_amount",
                data={"context": new_context},
                suggestions=["25000", "15000", "5000", "Cancel"]
            )
        
        if message_lower in ['yes', 'update', 'confirm', 'yes, update fees', 'ok', 'proceed']:
            return self._execute_fee_update_from_context(context)
        
        # Default to update
        return self._execute_fee_update_from_context(context)
    
    def _execute_fee_update_from_data(self, parsed_data: Dict) -> ChatResponse:
        """Execute fee update from parsed data"""
        context = {
            "fee_item": parsed_data["fee_item"],
            "amount": parsed_data["amount"],
            "scope": parsed_data.get("scope", "all_grades"),
            "grade_level": parsed_data.get("grade_level"),
            "existing_items": self._find_existing_fee_items(parsed_data["fee_item"])
        }
        
        return self._execute_fee_update_from_context(context)
    
    def _execute_fee_update_from_context(self, context: Dict) -> ChatResponse:
        """Execute the actual fee update"""
        try:
            fee_item = context.get('fee_item')
            amount = context.get('amount')
            scope = context.get('scope')
            grade_level = context.get('grade_level')
            
            # Build query based on scope
            if scope == 'grade_specific' and grade_level:
                # Update fee for specific grade
                affected_rows = db_execute_non_select(self.db,
                    """UPDATE fee_items 
                       SET amount = :amount, updated_at = CURRENT_TIMESTAMP
                       WHERE school_id = :school_id 
                       AND item_name ILIKE :item_name
                       AND fee_structure_id IN (
                           SELECT fs.id FROM fee_structures fs
                           INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
                           WHERE fs.school_id = :school_id AND fs.level ILIKE :level
                       )""",
                    {
                        "amount": amount,
                        "school_id": self.school_id,
                        "item_name": f"%{fee_item}%",
                        "level": f"%{grade_level}%"
                    }
                )
                
                scope_description = f"for {grade_level}"
                
            else:
                # Update fee for all active grades
                affected_rows = db_execute_non_select(self.db,
                    """UPDATE fee_items 
                       SET amount = :amount, updated_at = CURRENT_TIMESTAMP
                       WHERE school_id = :school_id 
                       AND item_name ILIKE :item_name
                       AND fee_structure_id IN (
                           SELECT fs.id FROM fee_structures fs
                           INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
                           WHERE fs.school_id = :school_id
                       )""",
                    {
                        "amount": amount,
                        "school_id": self.school_id,
                        "item_name": f"%{fee_item}%"
                    }
                )
                
                scope_description = "for all active grades"
            
            if affected_rows == 0:
                return ChatResponse(
                    response=f"No fee items were updated. The fee '{fee_item}' might not exist in active grades.",
                    intent="fee_update_no_changes",
                    data={"context": {}},  # Clear context
                    suggestions=[
                        "Show fee structures",
                        "Update different fee",
                        "Check fee item names"
                    ]
                )
            
            # Commit the changes
            self.db.commit()
            
            # Build success response
            response_text = f"Fee update completed successfully!\n\n"
            response_text += f"Updated: {fee_item} to KES {amount:,.2f}\n"
            response_text += f"Scope: {scope_description}\n"
            response_text += f"Items updated: {affected_rows}\n\n"
            response_text += f"The new fee amounts are now active and will be used for future invoices."
            
            return ChatResponse(
                response=response_text,
                intent="fee_update_successful",
                data={
                    "fee_item": fee_item,
                    "amount": amount,
                    "scope": scope_description,
                    "affected_rows": affected_rows,
                    "context": {}  # CRITICAL: Clear context to end flow
                },
                suggestions=[
                    "Show updated fee structure",
                    "Update another fee",
                    "Generate invoices"
                ]
            )
            
        except Exception as e:
            self.db.rollback()
            return ChatResponse(
                response=f"Error updating fees: {str(e)}\n\nPlease try again or contact support.",
                intent="fee_update_error",
                data={"context": context},  # Keep context for retry
                suggestions=["Try again", "Cancel", "Show fee structures"]
            )
    
    # Helper methods
    def _normalize_fee_item_name(self, fee_item: str) -> str:
        """Normalize fee item names to match database values"""
        fee_item_lower = fee_item.lower().strip()
        
        # Common mappings
        mappings = {
            'tuition': 'Tuition',
            'school fees': 'Tuition',
            'lunch': 'Lunch',
            'lunch fee': 'Lunch', 
            'transport': 'Transport',
            'bus': 'Transport',
            'application': 'Application',
            'registration': 'Registration',
            'caution': 'Caution',
            'insurance': 'Annual Student Accident Insurance Cover',
            'accident insurance': 'Annual Student Accident Insurance Cover',
            'workbooks': 'Workbooks',
            'books': 'Workbooks',
            'sports': 'Sports & Games',
            'games': 'Sports & Games',
            'sports & games': 'Sports & Games',
            'music': 'Music & Drama',
            'drama': 'Music & Drama',
            'music & drama': 'Music & Drama',
            'computer': 'Computer Club',
            'computer club': 'Computer Club',
            't-shirt': 'Sports T-Shirt',
            'tshirt': 'Sports T-Shirt',
            'sports t-shirt': 'Sports T-Shirt'
        }
        
        return mappings.get(fee_item_lower, fee_item.title())
    
    def _find_existing_fee_items(self, fee_item: str) -> List[Dict]:
        """Find existing fee items matching the name"""
        try:
            items = db_execute_safe(self.db,
                """SELECT fs.level, fi.item_name, fi.amount, fi.id
                   FROM fee_items fi
                   JOIN fee_structures fs ON fi.fee_structure_id = fs.id
                   INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
                   WHERE fi.school_id = :school_id 
                   AND fi.item_name ILIKE :item_name
                   ORDER BY fs.level, fi.item_name""",
                {
                    "school_id": self.school_id,
                    "item_name": f"%{fee_item}%"
                }
            )
            
            return [
                {
                    "level": item[0],
                    "item_name": item[1],
                    "amount": float(item[2]),
                    "id": str(item[3])
                }
                for item in items
            ]
        except Exception as e:
            print(f"Error finding fee items: {e}")
            return []
    
    def _get_available_fee_items(self) -> List[str]:
        """Get list of available fee items in active structures"""
        try:
            items = db_execute_safe(self.db,
                """SELECT DISTINCT fi.item_name
                   FROM fee_items fi
                   JOIN fee_structures fs ON fi.fee_structure_id = fs.id
                   INNER JOIN classes c ON c.level = fs.level AND c.school_id = fs.school_id
                   WHERE fi.school_id = :school_id
                   ORDER BY fi.item_name
                   LIMIT 10""",
                {"school_id": self.school_id}
            )
            
            return [item[0] for item in items]
        except Exception as e:
            print(f"Error getting available fee items: {e}")
            return ["Tuition", "Lunch", "Transport"]