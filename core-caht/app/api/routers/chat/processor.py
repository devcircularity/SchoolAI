# app/api/routers/chat/processor.py - Complete version with all fixes

import os
import time
import asyncio
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from datetime import datetime

from .base import ChatResponse, db_execute_non_select
from .handlers.overview.handler import OverviewHandler
from .handlers.academic.handler import AcademicHandler
from .handlers.student.handler import StudentHandler
from .handlers.classes.handler import ClassHandler
from .handlers.enrollment.handler import EnrollmentHandler
from .handlers.invoice.handler import InvoiceHandler
from .handlers.fee.handler import FeeHandler
from .handlers.payment.handler import PaymentHandler
from .handlers.general.handler import GeneralHandler
from .blocks import text

from app.services.config_router import ConfigRouter
from app.services.intent_classifier import IntentClassifier
from app.models.intent_config import RoutingLog


class IntentProcessor:
    """Intent-first processor using ConfigRouter + IntentClassifier pipeline"""
    
    def __init__(self, db: Session, user_id: str, school_id: str):
        self.db = db
        self.user_id = user_id
        self.school_id = school_id
        
        # Initialize routing services
        self.config_router = ConfigRouter(db)
        self.config_router.reload_config()  # Force initial load
        self.intent_classifier = IntentClassifier()
        
        # Feature flag for legacy fallback
        self.use_legacy_routing = os.getenv('USE_LEGACY_ROUTING', 'false').lower() == 'true'
        
        # Debug flag for verbose output
        self.debug_mode = os.getenv('DEBUG_ROUTING', 'false').lower() == 'true'
        
        # Initialize handlers by key for direct lookup
        self.handlers_by_key = {
            "overview": OverviewHandler(db, school_id, user_id),
            "academic": AcademicHandler(db, school_id, user_id),
            "student": StudentHandler(db, school_id, user_id),
            "class": ClassHandler(db, school_id, user_id),
            "enrollment": EnrollmentHandler(db, school_id, user_id),
            "invoice": InvoiceHandler(db, school_id, user_id),
            "fee": FeeHandler(db, school_id, user_id),
            "payment": PaymentHandler(db, school_id, user_id),
            "general": GeneralHandler(db, school_id, user_id),
        }
        
        # Intent → Handler mapping - COMPLETE VERSION WITH ALL MIGRATED INTENTS
        self.intent_handler_map = {
            # Student intents
            "student_create": "student",
            "student_search": "student", 
            "student_list": "student",
            "student_details": "student",
            "student_count": "student",
            "unassigned_students": "student",
            
            # Payment intents
            "payment_record": "payment",
            "payment_summary": "payment", 
            "payment_history": "payment",
            "payment_pending": "payment",
            "payment_status": "payment",
            
            # Invoice intents
            "invoice_generate_student": "invoice",
            "invoice_generate_bulk": "invoice",
            "invoice_pending": "invoice", 
            "invoice_show_student": "invoice",
            "invoice_list": "invoice",
            "invoice_overview": "invoice",
            
            # Overview intents
            "school_overview": "overview",
            "dashboard": "overview",
            "school_summary": "overview",
            
            # General intents
            "greeting": "general",
            "casual_conversation": "general",
            "school_registration": "general",
            "getting_started": "general", 
            "system_capabilities": "general",
            "help": "general",
            "next_steps": "general",
            "school_management": "general",
            "system_introduction": "general",
            "unknown": "general",
            
            # Fee intents
            "fee_structure": "fee",
            "fee_overview": "fee", 
            "fee_grade_specific": "fee",
            "fee_update": "fee",
            "fee_items": "fee",
            "fee_student_invoice": "fee",
            
            # Class intents
            "class_create": "class",
            "grade_create": "class",
            "class_details": "class", 
            "grade_list": "class",
            "class_list": "class",
            "class_count": "class",
            "class_empty": "class",
            
            # Enrollment intents
            "enrollment_single": "enrollment",
            "enrollment_bulk": "enrollment", 
            "enrollment_status": "enrollment",
            "enrollment_list": "enrollment",
            
            # Academic intents
            "academic_current_term": "academic",
            "academic_activate_term": "academic",
            "academic_calendar": "academic", 
            "academic_setup": "academic",
            "academic_overview": "academic",
        }
        
        # Legacy handlers for fallback
        self.legacy_handlers = [
            self.handlers_by_key["overview"],
            self.handlers_by_key["academic"], 
            self.handlers_by_key["enrollment"],
            self.handlers_by_key["invoice"],
            self.handlers_by_key["payment"],
            self.handlers_by_key["fee"],
            self.handlers_by_key["student"],
            self.handlers_by_key["class"],
            self.handlers_by_key["general"],
        ]
        
        if self.debug_mode:
            print(f"IntentProcessor initialized for school_id: {school_id}, user_id: {user_id}")
            print(f"ConfigRouter cache stats: {self.config_router.get_cache_stats()}")
    
    def process_message(self, message: str, context: Optional[Dict] = None) -> ChatResponse:
        """Process message using intent-first pipeline"""
        
        print(f"\n{'='*60}")
        print(f"Processing message: '{message}'")
        if context:
            print(f"Context keys: {list(context.keys())}")
        print(f"{'='*60}")
        
        # Build enhanced context
        enhanced_context = self._build_enhanced_context(message, context)
        
        # Check for context flows first (multi-step processes)
        if enhanced_context and enhanced_context.get('handler') and enhanced_context.get('flow'):
            handler_name = enhanced_context.get('handler')
            print(f"Context flow detected for handler: {handler_name}")
            
            if handler_name in self.handlers_by_key:
                handler = self.handlers_by_key[handler_name]
                # For flows, use handle_intent if available, otherwise fall back to handle
                if hasattr(handler, 'handle_intent'):
                    return handler.handle_intent("context_flow", message, {}, enhanced_context)
                else:
                    return handler.handle(message, enhanced_context)
        
        # Use legacy routing if feature flag is enabled
        if self.use_legacy_routing:
            print("Using legacy routing (feature flag enabled)")
            return self._process_message_legacy(message, enhanced_context)
        
        # NEW: Intent-first pipeline
        return self._process_message_intent_first(message, enhanced_context)
    
    def _process_message_intent_first(self, message: str, context: Dict) -> ChatResponse:
        """Process using ConfigRouter → IntentClassifier → Handler pipeline"""
        start_time = time.time()
        routing_data = {
            "message": message,
            "llm_intent": None,
            "llm_confidence": None,
            "llm_entities": None,
            "router_intent": None,
            "router_reason": None,
            "final_intent": None,
            "final_handler": None,
            "fallback_used": False
        }
        
        try:
            # Step 1: Try ConfigRouter first
            print("\n--- Step 1: ConfigRouter ---")
            router_result = self.config_router.route(message, self.school_id)
            
            if router_result:
                routing_data["router_intent"] = router_result.intent
                routing_data["router_reason"] = router_result.reason
                print(f"✓ ConfigRouter found: {router_result.intent} (confidence: {router_result.confidence:.3f})")
                if router_result.entities:
                    print(f"  Entities: {router_result.entities}")
            else:
                print("✗ ConfigRouter returned None - no pattern matched")
            
            # Step 2: Decide if we need LLM classifier
            router_confidence_threshold = 0.15
            llm_confidence_threshold = 0.30
            
            should_use_llm = (
                not router_result or 
                router_result.confidence < router_confidence_threshold
            )
            
            llm_result = None
            
            if should_use_llm:
                print(f"\n--- Step 2: IntentClassifier (router confidence too low: {router_result.confidence if router_result else 0:.3f}) ---")
                
                # Get allowed intents for LLM classifier
                allowed_intents = self._get_allowed_intents()
                recent_context = self._build_recent_context(context)
                entity_schema = self._get_entity_schema_for_message(message)
                
                # Use synchronous wrapper for intent classification
                llm_result = self._classify_intent_sync(
                    message, allowed_intents, recent_context, entity_schema
                )
                
                if llm_result:
                    routing_data["llm_intent"] = llm_result.intent
                    routing_data["llm_confidence"] = llm_result.confidence
                    routing_data["llm_entities"] = llm_result.entities
                    print(f"✓ IntentClassifier found: {llm_result.intent} (confidence: {llm_result.confidence:.3f})")
                    if llm_result.entities:
                        print(f"  Entities: {llm_result.entities}")
                else:
                    print("✗ IntentClassifier failed or timed out")
            else:
                print(f"\n--- Step 2: Skipping IntentClassifier (router confidence sufficient: {router_result.confidence:.3f}) ---")
            
            # Step 3: Fuse decision - prefer router if confidence is good
            print("\n--- Step 3: Decision Fusion ---")
            final_intent = None
            final_entities = {}
            
            if router_result and router_result.confidence >= router_confidence_threshold:
                final_intent = router_result.intent
                final_entities = router_result.entities
                print(f"→ Using ConfigRouter result: {final_intent} (confidence: {router_result.confidence:.3f})")
            elif llm_result and llm_result.confidence >= llm_confidence_threshold:
                final_intent = llm_result.intent
                final_entities = llm_result.entities
                print(f"→ Using IntentClassifier result: {final_intent} (confidence: {llm_result.confidence:.3f})")
            else:
                # Both failed or have low confidence
                print("→ Both router and classifier failed/low confidence - using fallback")
                routing_data["fallback_used"] = True
                return self._handle_unhandled_query(message, context, routing_data, start_time)
            
            # Step 4: Map intent to handler
            handler_key = self._map_intent_to_handler(final_intent)
            routing_data["final_intent"] = final_intent
            routing_data["final_handler"] = handler_key
            
            print(f"\n--- Step 4: Handler Dispatch ---")
            print(f"Intent '{final_intent}' → Handler '{handler_key}'")
            
            # Step 5: Dispatch to handler
            if handler_key in self.handlers_by_key:
                handler = self.handlers_by_key[handler_key]
                
                # Use handle_intent if available (new intent-first handlers)
                if hasattr(handler, 'handle_intent'):
                    print(f"→ Calling {handler_key}.handle_intent()")
                    response = handler.handle_intent(final_intent, message, final_entities, context)
                else:
                    # Legacy handler - use old handle method
                    print(f"→ Calling {handler_key}.handle() [legacy]")
                    response = handler.handle(message, context)
                
                # Step 6: Log routing decision
                self._log_routing_decision(routing_data, start_time)
                
                print(f"\n✓ Response generated with intent: {response.intent}")
                return response
            else:
                print(f"✗ Handler '{handler_key}' not found - using general handler")
                routing_data["final_handler"] = "general"
                response = self.handlers_by_key["general"].handle(message, context)
                self._log_routing_decision(routing_data, start_time)
                return response
        
        except Exception as e:
            print(f"\n✗ Error in intent-first processing: {e}")
            import traceback
            traceback.print_exc()
            
            # Fall back to legacy routing on error
            routing_data["fallback_used"] = True
            routing_data["final_handler"] = "legacy_fallback"
            self._log_routing_decision(routing_data, start_time, error=str(e))
            
            return self._process_message_legacy(message, context)
    
    def _classify_intent_sync(self, message: str, allowed_intents: List[str], 
                             recent_context: str, entity_schema: Dict) -> Optional[object]:
        """Synchronous wrapper for intent classification"""
        try:
            # Try to use nest_asyncio if available
            try:
                import nest_asyncio
                nest_asyncio.apply()
                
                # Now we can safely run async code even from within an existing loop
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    self.intent_classifier.classify(
                        message, allowed_intents, recent_context, entity_schema
                    )
                )
                return result
                
            except ImportError:
                print("nest_asyncio not available, using threading approach")
                
                # Fall back to threading approach
                import concurrent.futures
                import threading
                
                result_container = {'result': None, 'error': None}
                
                def run_in_thread():
                    try:
                        # Create new event loop for this thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        
                        # Run the async function
                        result = new_loop.run_until_complete(
                            self.intent_classifier.classify(
                                message, allowed_intents, recent_context, entity_schema
                            )
                        )
                        result_container['result'] = result
                        
                    except Exception as e:
                        result_container['error'] = e
                    finally:
                        new_loop.close()
                
                # Run in thread with timeout
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join(timeout=1.0)  # 1 second timeout
                
                if thread.is_alive():
                    print("IntentClassifier: Thread timeout")
                    return None
                
                if result_container['error']:
                    print(f"IntentClassifier error: {result_container['error']}")
                    return None
                    
                return result_container['result']
                
        except Exception as e:
            print(f"Error in synchronous intent classification: {e}")
            return None
    
    def _get_allowed_intents(self) -> List[str]:
        """Get list of all supported intents"""
        return list(self.intent_handler_map.keys())
    
    def _build_recent_context(self, context: Dict) -> str:
        """Build recent context string for LLM classifier"""
        if not context or not context.get('recent_messages'):
            return ""
        
        recent_messages = context['recent_messages'][-3:]  # Last 3 messages
        context_parts = []
        
        for msg in recent_messages:
            msg_type = msg.get('type', 'USER')
            content = msg.get('content', '')[:100]  # Truncate
            intent = msg.get('intent', '')
            if intent:
                context_parts.append(f"{msg_type}({intent}): {content}")
            else:
                context_parts.append(f"{msg_type}: {content}")
        
        return " | ".join(context_parts)
    
    def _get_entity_schema_for_message(self, message: str) -> Dict[str, str]:
        """Get appropriate entity schema based on message content"""
        message_lower = message.lower()
        
        # Simple heuristic-based schema selection
        if any(word in message_lower for word in ['student', 'pupil', 'learner']):
            return self.intent_classifier.get_entity_schema("student")
        elif any(word in message_lower for word in ['class', 'grade', 'form']):
            return self.intent_classifier.get_entity_schema("class")
        elif any(word in message_lower for word in ['enroll', 'enrollment']):
            return self.intent_classifier.get_entity_schema("enrollment")
        elif any(word in message_lower for word in ['fee', 'payment', 'invoice']):
            return self.intent_classifier.get_entity_schema("fees")
        else:
            return {}
    
    def _map_intent_to_handler(self, intent: str) -> str:
        """Map intent to handler key"""
        # Direct mapping
        if intent in self.intent_handler_map:
            return self.intent_handler_map[intent]
        
        # Fuzzy matching for intent prefixes
        for intent_prefix, handler_key in [
            ("student_", "student"),
            ("class_", "class"),
            ("enrollment_", "enrollment"),
            ("fee_", "fee"),
            ("payment_", "payment"),
            ("invoice_", "invoice"),
            ("academic_", "academic"),
            ("school_", "overview"),
        ]:
            if intent.startswith(intent_prefix):
                return handler_key
        
        # Default fallback
        return "general"
    
    def _log_routing_decision(self, routing_data: Dict, start_time: float, error: str = None):
        """Log routing decision to database for training"""
        try:
            # Get active config version
            from app.models.intent_config import IntentConfigVersion
            active_version = self.db.query(IntentConfigVersion)\
                .filter(IntentConfigVersion.status == 'active')\
                .first()
            
            # If no active version, create a temporary one or skip logging
            if not active_version:
                print("→ No active config version found, skipping routing log")
                return
            
            version_id = active_version.id
            latency_ms = int((time.time() - start_time) * 1000)
            
            log_data = {
                "id": f"log_{int(time.time() * 1000)}_{hash(routing_data['message']) % 10000}",
                "conversation_id": f"conv_{self.user_id}_{int(time.time() / 3600)}",  # Hourly conversation grouping
                "message_id": f"msg_{int(time.time() * 1000)}",
                "message": routing_data["message"][:1000],  # Truncate long messages
                "llm_intent": routing_data.get("llm_intent"),
                "llm_confidence": routing_data.get("llm_confidence"),
                "llm_entities": routing_data.get("llm_entities"),
                "router_intent": routing_data.get("router_intent"),
                "router_reason": routing_data.get("router_reason"),
                "final_intent": routing_data.get("final_intent", "unknown"),
                "final_handler": routing_data.get("final_handler", "unknown"),
                "fallback_used": routing_data.get("fallback_used", False),
                "latency_ms": latency_ms,
                "version_id": version_id,  # Use actual version ID
                "school_id": self.school_id,
                "user_id": self.user_id,
                "created_at": datetime.utcnow()
            }
            
            # Add error if present
            if error:
                log_data["router_reason"] = f"error: {error[:200]}"
            
            # Insert log record
            db_execute_non_select(self.db, """
                INSERT INTO routing_logs (
                    id, conversation_id, message_id, message,
                    llm_intent, llm_confidence, llm_entities,
                    router_intent, router_reason,
                    final_intent, final_handler, fallback_used,
                    latency_ms, version_id, school_id, user_id, created_at
                ) VALUES (
                    :id, :conversation_id, :message_id, :message,
                    :llm_intent, :llm_confidence, :llm_entities,
                    :router_intent, :router_reason,
                    :final_intent, :final_handler, :fallback_used,
                    :latency_ms, :version_id, :school_id, :user_id, :created_at
                )
            """, log_data)
            
            self.db.commit()
            print(f"→ Logged routing: {routing_data.get('final_intent')} → {routing_data.get('final_handler')} ({latency_ms}ms)")
            
        except Exception as e:
            print(f"✗ Error logging routing decision: {e}")
            # Don't let logging errors break the main flow
            try:
                self.db.rollback()
            except:
                pass
    
    def _handle_unhandled_query(self, message: str, context: Dict, routing_data: Dict, start_time: float) -> ChatResponse:
        """Handle queries that couldn't be routed"""
        print("\n--- Fallback: Unhandled Query ---")
        
        # Log the failure
        routing_data["final_intent"] = "unhandled"
        routing_data["final_handler"] = "ollama_fallback"
        self._log_routing_decision(routing_data, start_time)
        
        # Try Ollama as last resort, then fall back to generic response
        try:
            from app.services.ollama_service import OllamaService
            ollama_service = OllamaService()
            
            print(f"Attempting Ollama fallback for: '{message}'")
            school_context_prompt = self._build_school_context_prompt(message, context)
            ollama_result = ollama_service.generate_response_sync(school_context_prompt)
            
            if ollama_result.get("response") and ollama_result.get("success", True):
                print(f"✓ Ollama fallback successful")
                ollama_response = ollama_result["response"].strip()
                
                if len(ollama_response) > 1500:
                    ollama_response = ollama_response[:1497] + "..."
                
                return ChatResponse(
                    response=ollama_response,
                    intent="ollama_fallback",
                    data={"model_used": ollama_service.model, "fallback": True},
                    suggestions=[
                        "What can you help me with?",
                        "Show school overview",
                        "List all students",
                        "Show academic calendar"
                    ]
                )
        except Exception as e:
            print(f"✗ Ollama fallback failed: {e}")
        
        # Final fallback
        print("→ Using generic fallback response")
        return ChatResponse(
            response="I'm not sure how to help with that specific request. Could you try rephrasing or let me know what you'd like to do?",
            intent="unhandled",
            suggestions=[
                "What can you help me with?",
                "Show school overview", 
                "List all students",
                "Show academic calendar"
            ],
            blocks=[
                text("**💡 Try asking:**\n\n• 'What can you do?' for a full overview\n• Specific requests like 'show all students' or 'create a class'")
            ]
        )
    
    def _build_school_context_prompt(self, message: str, context: Dict) -> str:
        """Build school context prompt for Ollama fallback"""
        try:
            school_name = "the school"
            if self.handlers_by_key.get("overview") and hasattr(self.handlers_by_key["overview"], 'get_school_name'):
                school_name = self.handlers_by_key["overview"].get_school_name()
        except:
            school_name = "the school"
        
        conversation_context = ""
        if context and context.get('recent_messages'):
            recent_messages = context['recent_messages'][-3:]
            conversation_context = "\n\nRecent conversation:\n"
            for msg in recent_messages:
                msg_type = msg.get('type', 'USER')
                content = msg.get('content', '')[:150]
                conversation_context += f"{msg_type}: {content}\n"
        
        return f"""You are a helpful assistant for a school management system serving {school_name}. The user is asking about school operations or general topics.

User's question: "{message}"{conversation_context}

Context about this school management system:
- Helps with student registration, enrollment, and class assignments
- Manages academic calendar, terms, and grade levels  
- Handles fee structures, invoice generation, and payment processing
- Provides parent communication and school analytics
- Supports CBC curriculum grade levels (PP1, PP2, Grade 1-9, Form 1-4)

Guidelines for your response:
1. Answer the user's question directly and helpfully
2. If it's school-related, provide specific guidance or suggestions
3. Keep responses under 200 words and be natural and engaging
4. Don't mention that you're a fallback system - just be helpful

Response:"""
    
    def _build_enhanced_context(self, current_message: str, context: Optional[Dict]) -> Dict:
        """Build enhanced context with conversation history analysis"""
        enhanced_context = context.copy() if context else {}
        
        # Analyze recent messages for patterns
        if 'recent_messages' in enhanced_context:
            recent_messages = enhanced_context['recent_messages']
            
            # Extract intents from recent assistant messages
            recent_intents = [
                msg.get('intent') for msg in recent_messages 
                if msg.get('type') == 'ASSISTANT' and msg.get('intent')
            ]
            
            # Extract entities mentioned recently
            recent_content = ' '.join([
                msg.get('content', '') for msg in recent_messages[-3:]
            ])
            
            enhanced_context['recent_intents'] = recent_intents
            enhanced_context['recent_content'] = recent_content
        
        return enhanced_context
    
    def _process_message_legacy(self, message: str, context: Dict) -> ChatResponse:
        """Legacy handler-based processing (fallback)"""
        print("\n--- Legacy Handler-Based Routing ---")
        
        # Try each handler in order
        for i, handler in enumerate(self.legacy_handlers):
            handler_name = handler.__class__.__name__
            
            try:
                can_handle = handler.can_handle(message)
                print(f"Handler {i+1}: {handler_name} - can_handle: {can_handle}")
                
                if can_handle:
                    print(f"✓ Handler {handler_name} accepted message")
                    response = handler.handle(message, context)
                    print(f"✓ Handler {handler_name} returned response with intent: {response.intent}")
                    return response
            except Exception as e:
                print(f"✗ Handler {handler_name} failed: {e}")
                continue
        
        # Final fallback
        print("✗ No legacy handler could handle the message")
        return self._handle_unhandled_query(message, context, {"fallback_used": True}, time.time())