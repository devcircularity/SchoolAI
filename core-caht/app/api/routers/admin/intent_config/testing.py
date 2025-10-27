# app/api/routers/admin/intent_config/testing.py
"""Testing and debugging tools for intent configuration"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.deps.auth import require_admin
from app.services.config_router import ConfigRouter
from app.services.intent_classifier import IntentClassifier
from .shared import TestClassifyRequest, TestClassifyResponse

router = APIRouter()

@router.post("/test-classify", response_model=TestClassifyResponse)
def test_classify(
    request: TestClassifyRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Test message classification with full pipeline details"""
    try:
        steps = []
        message = request.message
        school_id = request.school_id
        
        # Step 1: Test ConfigRouter
        steps.append(f"Testing ConfigRouter for message: '{message}'")
        config_router = ConfigRouter(db)
        router_result = config_router.route(message, school_id)
        
        config_result = None
        if router_result:
            config_result = {
                "intent": router_result.intent,
                "confidence": router_result.confidence,
                "entities": router_result.entities,
                "reason": router_result.reason
            }
            steps.append(f"ConfigRouter match: {router_result.intent} (confidence: {router_result.confidence:.3f})")
        else:
            steps.append("ConfigRouter: No match found")
        
        # Step 2: Test IntentClassifier (if available)
        steps.append("Testing IntentClassifier (LLM)")
        llm_result = None
        
        try:
            classifier = IntentClassifier()
            
            # Get allowed intents from config
            allowed_intents = [
                "student_create", "student_search", "student_list", "student_details", "student_count",
                "payment_record", "payment_summary", "payment_history", "payment_pending", "payment_status",
                "invoice_generate_student", "invoice_generate_bulk", "invoice_pending", "invoice_show_student",
                "school_overview", "dashboard", "greeting", "help", "unknown",
                "fee_structure", "fee_overview", "class_create", "class_list", "enrollment_single"
            ]
            
            # Run classifier synchronously (simplified for testing)
            import asyncio
            try:
                result = asyncio.run(classifier.classify(message, allowed_intents, "", {}))
                if result and not getattr(result, 'error', None):
                    llm_result = {
                        "intent": result.intent,
                        "confidence": result.confidence,
                        "entities": result.entities,
                        "alternatives": getattr(result, 'alternatives', [])
                    }
                    steps.append(f"IntentClassifier result: {result.intent} (confidence: {result.confidence:.3f})")
                else:
                    error_msg = getattr(result, 'error', 'Unknown error') if result else 'Unknown error'
                    steps.append(f"IntentClassifier failed: {error_msg}")
            except Exception as e:
                steps.append(f"IntentClassifier error: {str(e)}")
        
        except ImportError:
            steps.append("IntentClassifier not available")
        except Exception as e:
            steps.append(f"IntentClassifier initialization error: {str(e)}")
        
        # Step 3: Final decision logic
        steps.append("Applying decision fusion logic")
        
        router_confidence_threshold = 0.55
        llm_confidence_threshold = 0.45
        
        final_decision = {"source": "fallback", "intent": "unknown", "confidence": 0.0}
        
        if config_result and config_result["confidence"] >= router_confidence_threshold:
            final_decision = {
                "source": "config_router",
                "intent": config_result["intent"],
                "confidence": config_result["confidence"],
                "entities": config_result.get("entities", {})
            }
            steps.append(f"Final: Using ConfigRouter result (confidence sufficient)")
        elif llm_result and llm_result["confidence"] >= llm_confidence_threshold:
            final_decision = {
                "source": "llm_classifier",
                "intent": llm_result["intent"],
                "confidence": llm_result["confidence"],
                "entities": llm_result.get("entities", {})
            }
            steps.append(f"Final: Using IntentClassifier result (router confidence too low)")
        else:
            steps.append("Final: Both router and classifier failed/low confidence - fallback")
        
        return TestClassifyResponse(
            message=message,
            config_router_result=config_result,
            llm_classifier_result=llm_result,
            final_decision=final_decision,
            processing_steps=steps
        )
        
    except Exception as e:
        return TestClassifyResponse(
            message=request.message,
            config_router_result=None,
            llm_classifier_result=None,
            final_decision={"source": "error", "intent": "error", "confidence": 0.0},
            processing_steps=[f"Error during testing: {str(e)}"]
        )

@router.post("/reload")
def reload_config(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Force reload of active configuration cache"""
    try:
        config_router = ConfigRouter(db)
        config_router.reload_config()
        stats = config_router.get_cache_stats()
        return {
            "message": "Configuration cache reloaded",
            "cache_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {str(e)}")

@router.get("/cache/stats")
def get_cache_stats(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get current cache statistics"""
    try:
        config_router = ConfigRouter(db)
        stats = config_router.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/validate-patterns/{version_id}")
def validate_patterns(
    version_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Validate all patterns in a version for regex compilation"""
    from app.models.intent_config import IntentPattern
    import re
    
    patterns = db.query(IntentPattern)\
        .filter(IntentPattern.version_id == version_id)\
        .all()
    
    validation_results = []
    valid_count = 0
    invalid_count = 0
    
    for pattern in patterns:
        try:
            re.compile(pattern.pattern, re.IGNORECASE)
            validation_results.append({
                "pattern_id": pattern.id,
                "intent": pattern.intent,
                "pattern": pattern.pattern,
                "valid": True,
                "error": None
            })
            valid_count += 1
        except re.error as e:
            validation_results.append({
                "pattern_id": pattern.id,
                "intent": pattern.intent,
                "pattern": pattern.pattern,
                "valid": False,
                "error": str(e)
            })
            invalid_count += 1
    
    return {
        "version_id": version_id,
        "total_patterns": len(patterns),
        "valid_patterns": valid_count,
        "invalid_patterns": invalid_count,
        "validation_results": validation_results
    }