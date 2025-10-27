# app/services/intent_classifier.py
import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.services.ollama_service import OllamaService


@dataclass
class ClassificationResult:
    """Structured result from intent classification"""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    error: Optional[str] = None
    latency_ms: Optional[int] = None


class IntentClassifier:
    """LLM-based intent classifier using Ollama"""
    
    def __init__(self):
        self.ollama = OllamaService()
        self.timeout_ms = 800
        
        # Default entity schemas for common handlers
        self.default_schemas = {
            "student": {
                "admission_no": "digits(3-7)",
                "student_name": "string",
                "class_name": "string"
            },
            "class": {
                "class_name": "string",
                "level": "string",
                "academic_year": "string"
            },
            "enrollment": {
                "student_id": "string",
                "class_id": "string",
                "term_name": "string"
            },
            "fees": {
                "amount": "number",
                "student_id": "string",
                "fee_type": "string"
            }
        }
    
    async def classify(self, 
                      message: str, 
                      allowed_intents: List[str],
                      recent_context: Optional[str] = None,
                      entity_schema: Optional[Dict[str, str]] = None) -> ClassificationResult:
        """
        Classify intent using LLM with structured output
        
        Args:
            message: User message to classify
            allowed_intents: List of valid intents to choose from
            recent_context: Optional recent conversation context
            entity_schema: Schema for entity extraction
        """
        start_time = time.time()
        
        try:
            # Build the prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(
                message, allowed_intents, recent_context, entity_schema
            )
            
            # Call Ollama with timeout
            response = await asyncio.wait_for(
                self.ollama.generate_with_system(system_prompt, user_prompt),
                timeout=self.timeout_ms / 1000.0
            )
            
            # Parse JSON response
            result = self._parse_classification_response(response, allowed_intents)
            result.latency_ms = int((time.time() - start_time) * 1000)
            
            return result
            
        except asyncio.TimeoutError:
            return ClassificationResult(
                intent="timeout",
                confidence=0.0,
                entities={},
                alternatives=[],
                error="Classification timeout",
                latency_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            return ClassificationResult(
                intent="error",
                confidence=0.0,
                entities={},
                alternatives=[],
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for classification"""
        return """You are an intent classifier for a school management assistant. 
Your job is to classify user messages into specific intents and extract relevant entities.

CRITICAL RULES:
1. Only return valid JSON - no explanations or extra text
2. Choose exactly one intent from the provided allowed list
3. Confidence must be between 0.0 and 1.0
4. Extract entities according to the provided schema
5. Include up to 3 alternative intents with their confidence scores
6. If unsure, be conservative with confidence scores

Response format:
{
  "intent": "selected_intent_name",
  "confidence": 0.75,
  "entities": {"field_name": "extracted_value"},
  "alternatives": [{"intent": "alt_intent", "confidence": 0.45}]
}"""
    
    def _build_user_prompt(self, 
                          message: str, 
                          allowed_intents: List[str],
                          recent_context: Optional[str],
                          entity_schema: Optional[Dict[str, str]]) -> str:
        """Build the user prompt with message and context"""
        prompt = f'Message: "{message}"\n\n'
        
        if recent_context:
            prompt += f'Recent context: "{recent_context}"\n\n'
        
        prompt += f'Allowed intents: {json.dumps(allowed_intents)}\n\n'
        
        if entity_schema:
            prompt += f'Entity schema: {json.dumps(entity_schema)}\n\n'
        else:
            prompt += 'Entity schema: {}\n\n'
        
        prompt += 'Return JSON only:'
        
        return prompt
    
    def _parse_classification_response(self, 
                                     response: str, 
                                     allowed_intents: List[str]) -> ClassificationResult:
        """Parse and validate the LLM response"""
        try:
            # Clean up response - remove markdown if present
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Parse JSON
            data = json.loads(cleaned)
            
            # Validate required fields
            intent = data.get("intent", "unknown")
            confidence = float(data.get("confidence", 0.0))
            entities = data.get("entities", {})
            alternatives = data.get("alternatives", [])
            
            # Validate intent is in allowed list
            if intent not in allowed_intents:
                # Try to find closest match
                intent_lower = intent.lower()
                for allowed in allowed_intents:
                    if allowed.lower() == intent_lower:
                        intent = allowed
                        break
                else:
                    # No match found, use first allowed intent with low confidence
                    intent = allowed_intents[0]
                    confidence = 0.1
            
            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))
            
            # Validate alternatives
            validated_alternatives = []
            for alt in alternatives[:3]:  # Max 3 alternatives
                if isinstance(alt, dict) and "intent" in alt and "confidence" in alt:
                    alt_intent = alt["intent"]
                    alt_confidence = max(0.0, min(1.0, float(alt["confidence"])))
                    if alt_intent in allowed_intents and alt_intent != intent:
                        validated_alternatives.append({
                            "intent": alt_intent,
                            "confidence": alt_confidence
                        })
            
            return ClassificationResult(
                intent=intent,
                confidence=confidence,
                entities=entities,
                alternatives=validated_alternatives
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback parsing - try to extract intent from text
            response_lower = response.lower()
            best_match = None
            best_score = 0
            
            for intent in allowed_intents:
                if intent.lower() in response_lower:
                    # Simple scoring based on position (earlier = better)
                    pos = response_lower.find(intent.lower())
                    score = 1.0 / (pos + 1)
                    if score > best_score:
                        best_score = score
                        best_match = intent
            
            return ClassificationResult(
                intent=best_match or allowed_intents[0],
                confidence=0.3 if best_match else 0.1,
                entities={},
                alternatives=[],
                error=f"JSON parse error: {str(e)}"
            )
    
    def get_handler_intents(self, handler: str) -> List[str]:
        """Get default intents for a specific handler"""
        handler_intents = {
            "student": [
                "student_list", "student_search", "student_details", 
                "student_count", "unassigned_students", "student_create"
            ],
            "class": [
                "class_list", "class_details", "class_create", 
                "class_enrollment", "class_overview"
            ],
            "enrollment": [
                "enrollment_list", "enrollment_create", "enrollment_bulk",
                "enrollment_status", "term_enrollment"
            ],
            "fees": [
                "fee_structure", "generate_invoice", "payment_status",
                "fee_summary", "payment_history"
            ],
            "academic": [
                "term_overview", "academic_calendar", "term_status"
            ],
            "general": [
                "school_overview", "help", "unknown"
            ]
        }
        return handler_intents.get(handler, ["unknown"])
    
    def get_entity_schema(self, handler: str, intent: str = None) -> Dict[str, str]:
        """Get entity extraction schema for handler/intent"""
        # Handler-specific schemas
        schema = self.default_schemas.get(handler, {})
        
        # Intent-specific overrides could be added here
        if intent and handler == "student":
            if intent in ["student_search", "student_details"]:
                schema.update({
                    "admission_no": "digits(3-7)",
                    "student_name": "string"
                })
            elif intent == "student_create":
                schema.update({
                    "student_name": "string",
                    "guardian_name": "string",
                    "guardian_phone": "string",
                    "guardian_email": "email"
                })
        
        return schema