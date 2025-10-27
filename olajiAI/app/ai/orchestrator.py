# app/ai/orchestrator.py - Enhanced with better fee price handling

from typing import Dict, Any, List
from app.ai.intents import detect_intent, extract_slots, missing_slots
from app.ai.llm import OllamaClient
from app.ai import prompt_templates as T
from app.state.memory import get_state, set_state, clear_state
from app.core.http import CoreHTTP
from app.ai.tools.base import ToolContext
from app.ai.tools import create_class as tool_create_class
from app.ai.tools import class_query as tool_class_query
from app.ai.tools import student_query as tool_student_query
from app.ai.tools import class_student_analytics as tool_class_student_analytics
from app.ai.tools import enroll_student as tool_enroll_student
from app.ai.tools import send_notification as tool_send_notification
from app.ai.tools import school_facts as tool_school_facts
from app.ai.tools import fee_operations as tool_fee_ops

class Orchestrator:
    def __init__(self):
        self.llm = OllamaClient()
        self.http = CoreHTTP()

    async def run_chat_turn(
        self, 
        *, 
        session_id: str, 
        message: str, 
        bearer: str, 
        school_id: str, 
        message_id: str | None
    ) -> Dict[str, Any]:
        """
        Main orchestrator method - GUARANTEED to return a valid Dict[str, Any]
        """
        try:
            return await self._run_chat_turn_internal(
                session_id=session_id,
                message=message, 
                bearer=bearer,
                school_id=school_id,
                message_id=message_id
            )
        except Exception as e:
            print(f"🔍 CRITICAL ERROR in orchestrator: {e}")
            import traceback
            traceback.print_exc()
            return {
                "content": "I encountered an unexpected error. Please try again or contact support.",
                "error": str(e)
            }

    async def _run_chat_turn_internal(
        self, 
        *, 
        session_id: str, 
        message: str, 
        bearer: str, 
        school_id: str, 
        message_id: str | None
    ) -> Dict[str, Any]:
        state = await get_state(session_id) or {}
        facts = state.get("facts") or {}
        
        # Recover pending intent from state (for multi-turn workflows)
        pending = await get_state(session_id)
        if pending and pending.get("tool_name"):
            intent = pending.get("tool_name")
            slots = dict(pending.get("slots", {}))
            slots.update(extract_slots(intent, message))
        else:
            intent = detect_intent(message)
            slots = extract_slots(intent, message) if intent else {}
        
        # Debug logging
        from app.core.logging import log
        log.info(
            "orchestrator_processing",
            message=message,
            detected_intent=intent,
            existing_slots=slots,
            session_id=session_id,
        )

        # Fee management intents with table support
        if intent == "view_fee_structure":
            return await self._handle_view_fee_structure(session_id, bearer, school_id, slots, message_id)

        if intent == "set_fee_prices":
            return await self._handle_set_prices(session_id, bearer, school_id, slots, message_id)

        if intent == "publish_fee_structure":
            return await self._handle_publish(session_id, bearer, school_id, slots, message_id)

        if intent == "generate_invoices":
            return await self._handle_generate_invoices(session_id, bearer, school_id, slots, message_id)

        # Handle no intent detected
        if not intent:
            log.warning(
                "no_intent_detected_fallback_to_llm",
                message=message,
                available_intents=[
                    "create_class", "class_query", "student_query", "enroll_student", 
                    "send_notification", "school_facts",
                    "view_fee_structure", "set_fee_prices", "publish_fee_structure", "generate_invoices"
                ]
            )
            context_msgs = []
            if facts:
                context_msgs.append({
                    "role": "system", 
                    "content": f"School context: id={facts.get('school_id')}, name={facts.get('school_name')}"
                })
            context_msgs.append({"role": "user", "content": message})
            content = await self.llm.generate(T.SYSTEM_PROMPT, context_msgs)
            return {"content": content}

        # Existing tools remain unchanged
        if intent == "school_facts":
            ctx = ToolContext(self.http, school_id, bearer, message_id)
            res = await tool_school_facts.run(ctx)
            if res.get("status") == 200 and res.get("body"):
                name = res["body"].get("school_name") or facts.get("school_name") or "(unknown)"
                return {"content": f"The school is {name}.", "tool": intent, "result": res}
            if facts.get("school_name"):
                return {"content": f"The school is {facts['school_name']}.", "tool": intent, "result": res}
            return {"content": "I couldn't fetch the school name right now."}

        if intent == "class_query":
            ctx = ToolContext(self.http, school_id, bearer, message_id)
            query_type = slots.get("query_type", "count")
            res = await tool_class_query.run(ctx, query_type)
            
            if res.get("status") == 200 and res.get("body"):
                count = res["body"].get("count", 0)
                classes = res["body"].get("classes", [])
                
                if query_type == "count":
                    return {"content": f"Your school has **{count}** classes.", "tool": intent, "result": res}
                elif query_type == "list":
                    if count == 0:
                        return {"content": "Your school has no classes yet.", "tool": intent, "result": res}
                    
                    # Format classes as table
                    table_data = {
                        "type": "table",
                        "title": f"School Classes ({count} total)",
                        "headers": ["Class Name", "Level", "Academic Year", "Stream"],
                        "rows": [
                            [
                                cls.get('name', 'Unknown'),
                                cls.get('level', 'No level'),
                                str(cls.get('academic_year', 'N/A')),
                                cls.get('stream', 'N/A') or 'N/A'
                            ]
                            for cls in classes
                        ]
                    }
                    
                    return {
                        "content": f"Your school has **{count}** classes:",
                        "table": table_data,
                        "tool": intent,
                        "result": res
                    }

        if intent == "student_query":
            ctx = ToolContext(self.http, school_id, bearer, message_id)
            query_type = slots.get("query_type", "count")
            res = await tool_student_query.run(ctx, query_type)
            
            if res.get("status") == 200 and res.get("body"):
                count = res["body"].get("count", 0)
                students = res["body"].get("students", [])
                
                if query_type == "count":
                    return {"content": f"Your school has **{count}** students.", "tool": intent, "result": res}
                elif query_type == "list":
                    if count == 0:
                        return {"content": "Your school has no students yet.", "tool": intent, "result": res}
                    
                    # Format students as table
                    table_data = {
                        "type": "table",
                        "title": f"School Students ({count} total)",
                        "headers": ["Name", "Admission No", "Gender", "Class"],
                        "rows": [
                            [
                                f"{student.get('first_name', '')} {student.get('last_name', '')}".strip(),
                                student.get('admission_no', 'N/A'),
                                student.get('gender', 'N/A'),
                                student.get('class_name', 'Unassigned')
                            ]
                            for student in students
                        ]
                    }
                    
                    return {
                        "content": f"Your school has **{count}** students:",
                        "table": table_data,
                        "tool": intent,
                        "result": res
                    }

        if intent == "class_student_analytics":
            ctx = ToolContext(self.http, school_id, bearer, message_id)
            query_type = slots.get("query_type", "class_distribution")
            res = await tool_class_student_analytics.run(ctx, query_type)
            
            if res.get("status") == 200 and res.get("body"):
                body = res["body"]
                report_type = body.get("type", "unknown")
                
                if report_type == "class_distribution":
                    classes = body.get("classes", [])
                    total_students = body.get("total_students", 0)
                    
                    if not classes:
                        return {"content": "No classes found.", "tool": intent, "result": res}
                    
                    # Format as table
                    table_data = {
                        "type": "table",
                        "title": f"Class Distribution ({total_students} total students)",
                        "headers": ["Class Name", "Level", "Student Count"],
                        "rows": [
                            [
                                cls['class_name'],
                                cls['level'],
                                str(cls['student_count'])
                            ]
                            for cls in classes
                        ]
                    }
                    
                    return {
                        "content": f"**Class Distribution** ({total_students} total students):",
                        "table": table_data,
                        "tool": intent,
                        "result": res
                    }
            
            return {"content": "I couldn't fetch the class-student analytics right now.", "tool": intent, "result": res}

        # Check for missing slots
        miss = missing_slots(intent, slots)
        if miss:
            await set_state(session_id, {"intent": intent, "slots": slots})
            numbered = "\n".join([f"{i+1}) {m}" for i, m in enumerate(miss)])
            return {"content": f"I need more information:\n{numbered}"}

        ctx = ToolContext(self.http, school_id, bearer, message_id)

        if intent == "create_class":
            res = await tool_create_class.run(ctx, {
                "name": slots["name"],
                "level": slots["level"],
                "academic_year": slots["academic_year"],
                **({"stream": slots.get("stream")} if slots.get("stream") else {})
            })
            
            await clear_state(session_id)
            
            if res.get("status") in [200, 201]:
                class_info = res.get("body", {})
                return {"content": f"✅ Class created: {class_info.get('name', 'Unknown')}", "tool": intent, "result": res}
            else:
                error_details = res.get("body", {})
                return {"content": f"Failed to create class: {error_details}", "tool": intent, "result": res}

        if intent == "enroll_student":
            res = await tool_enroll_student.run(ctx, slots)
            await clear_state(session_id)
            
            if res.get("status") in [200, 201]:
                student_info = res.get("body", {})
                student_name = f"{student_info.get('first_name', '')} {student_info.get('last_name', '')}".strip()
                return {"content": f"✅ Student enrolled: {student_name}", "tool": intent, "result": res}
            else:
                error_details = res.get("body", {})
                return {"content": f"Failed to enroll student: {error_details}", "tool": intent, "result": res}

        # Fallback to LLM
        try:
            content = await self.llm.generate(T.SYSTEM_PROMPT, [{"role": "user", "content": message}])
            return {"content": content}
        except Exception as e:
            print(f"🔍 ERROR in LLM fallback: {e}")
            return {"content": "I encountered an error processing your request. Please try again."}

    async def _handle_view_fee_structure(self, session_id: str, bearer: str, school_id: str, slots: Dict[str, Any], message_id: str) -> Dict[str, Any]:
        """Handle viewing CBC fee structure with overview support"""
        ctx = ToolContext(self.http, school_id, bearer, message_id)
        res = await tool_fee_ops.view_fee_structure(
            ctx, 
            slots.get("level"), 
            slots.get("term"), 
            slots.get("year")
        )
        
        if res.get("status") == 200:
            body = res["body"]
            action = body.get("action", "view")
            
            if action == "overview":
                # Handle comprehensive fee overview
                formatted = body.get("formatted", {})
                
                if isinstance(formatted, dict) and formatted.get("type") == "table_with_text":
                    return {
                        "content": formatted["text"] + "\n\n" + formatted.get("summary", ""),
                        "table": formatted["table"],
                        "tool": "view_fee_structure",
                        "result": res
                    }
                else:
                    return {"content": str(formatted), "tool": "view_fee_structure", "result": res}