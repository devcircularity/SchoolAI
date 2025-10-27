# app/api/routers/admin/intent_config/patterns.py
"""Pattern management for intent configurations with phrase-to-regex conversion"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel

from app.core.db import get_db
from app.api.deps.auth import require_admin
from app.models.intent_config import (
    IntentConfigVersion, IntentPattern, PatternKind, ConfigStatus
)
from app.services.config_router import ConfigRouter
from .shared import (
    PatternResponse, CreatePatternRequest, UpdatePatternRequest, safe_enum_value
)

router = APIRouter()

# NEW: Pydantic models for regex generation
class GenerateRegexRequest(BaseModel):
    phrases: List[str]
    intent: str
    pattern_kind: str = "positive"

class GenerateRegexResponse(BaseModel):
    phrases: List[str]
    intent: str
    pattern_kind: str
    generated_regex: str
    confidence: float
    explanation: str
    test_matches: List[str]
    errors: List[str]

# Enhanced Pydantic schemas
class EnhancedPatternResponse(PatternResponse):
    """Extended pattern response with phrase support"""
    phrases: Optional[List[str]] = None
    regex_confidence: Optional[float] = None
    regex_explanation: Optional[str] = None

class CreatePatternWithPhrasesRequest(CreatePatternRequest):
    """Create pattern request that supports both phrases and direct regex"""
    phrases: Optional[List[str]] = None  # If provided, will generate regex
    # pattern field becomes optional when phrases are provided
    pattern: Optional[str] = None

class UpdatePatternWithPhrasesRequest(UpdatePatternRequest):
    """Update pattern request with phrase support"""
    phrases: Optional[List[str]] = None
    regenerate_regex: bool = False  # Force regeneration even if pattern exists

class TestPatternWithPhrasesRequest(BaseModel):
    """Request for testing pattern against messages"""
    test_messages: List[str]

class ImprovePatternRequest(BaseModel):
    """Request for improving a pattern"""
    missed_phrases: List[str]
    false_positives: Optional[List[str]] = None

@router.get("/versions/{version_id}/patterns", response_model=List[EnhancedPatternResponse])
def list_patterns(
    version_id: str,
    handler: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List patterns for a version with optional filtering - now includes phrases"""
    query = db.query(IntentPattern).filter(IntentPattern.version_id == version_id)
    
    if handler:
        query = query.filter(IntentPattern.handler == handler)
    if intent:
        query = query.filter(IntentPattern.intent == intent)
    if kind:
        try:
            kind_enum = PatternKind(kind)
            query = query.filter(IntentPattern.kind == kind_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid pattern kind")
    
    patterns = query.order_by(IntentPattern.priority.desc()).all()
    
    return [
        EnhancedPatternResponse(
            id=pattern.id,
            handler=pattern.handler,
            intent=pattern.intent,
            kind=safe_enum_value(pattern.kind),
            pattern=pattern.pattern,
            priority=pattern.priority,
            enabled=pattern.enabled,
            scope_school_id=pattern.scope_school_id,
            created_at=pattern.created_at,
            updated_at=pattern.updated_at,
            phrases=getattr(pattern, 'phrases', None),
            regex_confidence=getattr(pattern, 'regex_confidence', None),
            regex_explanation=getattr(pattern, 'regex_explanation', None)
        ) for pattern in patterns
    ]

@router.post("/versions/{version_id}/patterns", response_model=EnhancedPatternResponse)
async def create_pattern(
    version_id: str,
    request: CreatePatternWithPhrasesRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Add a new pattern to a version - supports both phrases and direct regex"""
    try:
        # Validate version exists and is not archived
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == version_id)\
            .first()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        if version.status == ConfigStatus.ARCHIVED:
            raise HTTPException(status_code=400, detail="Cannot modify archived version")
        
        # Validate pattern kind
        try:
            kind = PatternKind(request.kind)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid pattern kind")
        
        # Determine regex pattern
        regex_pattern = request.pattern
        phrases = request.phrases or []
        regex_confidence = None
        regex_explanation = None
        
        if phrases and not request.pattern:
            # Generate regex from phrases using OllamaService
            try:
                from app.services.ollama_service import OllamaService
                ollama_service = OllamaService()
                result = await ollama_service.generate_regex_from_phrases(
                    phrases=phrases,
                    intent=request.intent,
                    pattern_kind=request.kind
                )
                
                if result.get("errors"):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Failed to generate regex from phrases: {', '.join(result['errors'])}"
                    )
                
                regex_pattern = result.get("regex", "")
                regex_confidence = result.get("confidence", 0.0)
                regex_explanation = result.get("explanation", "")
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate regex from phrases: {str(e)}"
                )
            
        elif not request.pattern and not phrases:
            raise HTTPException(
                status_code=400, 
                detail="Either 'pattern' or 'phrases' must be provided"
            )
        
        # Test compile the regex pattern
        import re
        try:
            re.compile(regex_pattern, re.IGNORECASE)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {str(e)}")
        
        pattern = IntentPattern(
            id=str(uuid.uuid4()),
            version_id=version_id,
            handler=request.handler,
            intent=request.intent,
            kind=kind,
            pattern=regex_pattern,
            priority=request.priority,
            enabled=request.enabled,
            scope_school_id=request.scope_school_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store additional phrase data if your schema supports it
        if hasattr(pattern, 'phrases'):
            pattern.phrases = phrases
        if hasattr(pattern, 'regex_confidence'):
            pattern.regex_confidence = regex_confidence
        if hasattr(pattern, 'regex_explanation'):
            pattern.regex_explanation = regex_explanation
        
        db.add(pattern)
        version.updated_at = datetime.utcnow()
        db.commit()
        
        # Reload config if this is the active version
        if version.status == ConfigStatus.ACTIVE:
            config_router = ConfigRouter(db)
            config_router.reload_config()
        
        return EnhancedPatternResponse(
            id=pattern.id,
            handler=pattern.handler,
            intent=pattern.intent,
            kind=safe_enum_value(pattern.kind),
            pattern=pattern.pattern,
            priority=pattern.priority,
            enabled=pattern.enabled,
            scope_school_id=pattern.scope_school_id,
            created_at=pattern.created_at,
            updated_at=pattern.updated_at,
            phrases=phrases,
            regex_confidence=regex_confidence,
            regex_explanation=regex_explanation
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create pattern: {str(e)}")

@router.put("/patterns/{pattern_id}", response_model=EnhancedPatternResponse)
async def update_pattern(
    pattern_id: str,
    request: UpdatePatternWithPhrasesRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a pattern - supports phrase updates and regex regeneration"""
    try:
        pattern = db.query(IntentPattern).filter(IntentPattern.id == pattern_id).first()
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Check version status
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == pattern.version_id)\
            .first()
        
        if version.status == ConfigStatus.ARCHIVED:
            raise HTTPException(status_code=400, detail="Cannot modify pattern in archived version")
        
        # Handle phrase updates and regex regeneration
        regex_confidence = getattr(pattern, 'regex_confidence', None)
        regex_explanation = getattr(pattern, 'regex_explanation', None)
        phrases = getattr(pattern, 'phrases', None)
        
        if request.phrases is not None:
            phrases = request.phrases
            
            # Regenerate regex if phrases changed or explicitly requested
            if request.regenerate_regex or not pattern.pattern:
                try:
                    from app.services.ollama_service import OllamaService
                    ollama_service = OllamaService()
                    result = await ollama_service.generate_regex_from_phrases(
                        phrases=phrases,
                        intent=pattern.intent,
                        pattern_kind=safe_enum_value(pattern.kind)
                    )
                    
                    if result.get("errors"):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Failed to regenerate regex: {', '.join(result['errors'])}"
                        )
                    
                    pattern.pattern = result.get("regex", "")
                    regex_confidence = result.get("confidence", 0.0)
                    regex_explanation = result.get("explanation", "")
                    
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to regenerate regex: {str(e)}"
                    )
        
        # Update other fields
        if request.handler is not None:
            pattern.handler = request.handler
        if request.intent is not None:
            pattern.intent = request.intent
        if request.kind is not None:
            try:
                pattern.kind = PatternKind(request.kind)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid pattern kind")
        if request.pattern is not None:
            # Test compile the regex pattern
            import re
            try:
                re.compile(request.pattern, re.IGNORECASE)
            except re.error as e:
                raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {str(e)}")
            pattern.pattern = request.pattern
        if request.priority is not None:
            pattern.priority = request.priority
        if request.enabled is not None:
            pattern.enabled = request.enabled
        if request.scope_school_id is not None:
            pattern.scope_school_id = request.scope_school_id
        
        # Update additional fields if schema supports them
        if hasattr(pattern, 'phrases'):
            pattern.phrases = phrases
        if hasattr(pattern, 'regex_confidence'):
            pattern.regex_confidence = regex_confidence
        if hasattr(pattern, 'regex_explanation'):
            pattern.regex_explanation = regex_explanation
        
        pattern.updated_at = datetime.utcnow()
        version.updated_at = datetime.utcnow()
        db.commit()
        
        # Reload config if this is the active version
        if version.status == ConfigStatus.ACTIVE:
            config_router = ConfigRouter(db)
            config_router.reload_config()
        
        return EnhancedPatternResponse(
            id=pattern.id,
            handler=pattern.handler,
            intent=pattern.intent,
            kind=safe_enum_value(pattern.kind),
            pattern=pattern.pattern,
            priority=pattern.priority,
            enabled=pattern.enabled,
            scope_school_id=pattern.scope_school_id,
            created_at=pattern.created_at,
            updated_at=pattern.updated_at,
            phrases=phrases,
            regex_confidence=regex_confidence,
            regex_explanation=regex_explanation
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update pattern: {str(e)}")

@router.delete("/patterns/{pattern_id}")
def delete_pattern(
    pattern_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete/disable a pattern"""
    try:
        pattern = db.query(IntentPattern).filter(IntentPattern.id == pattern_id).first()
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Check version status
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == pattern.version_id)\
            .first()
        
        if version.status == ConfigStatus.ARCHIVED:
            raise HTTPException(status_code=400, detail="Cannot modify pattern in archived version")
        
        # Disable instead of delete to preserve history
        pattern.enabled = False
        pattern.updated_at = datetime.utcnow()
        version.updated_at = datetime.utcnow()
        db.commit()
        
        # Reload config if this is the active version
        if version.status == ConfigStatus.ACTIVE:
            config_router = ConfigRouter(db)
            config_router.reload_config()
        
        return {"message": "Pattern disabled"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete pattern: {str(e)}")

@router.post("/patterns/{pattern_id}/enable")
def enable_pattern(
    pattern_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Re-enable a disabled pattern"""
    try:
        pattern = db.query(IntentPattern).filter(IntentPattern.id == pattern_id).first()
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Check version status
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == pattern.version_id)\
            .first()
        
        if version.status == ConfigStatus.ARCHIVED:
            raise HTTPException(status_code=400, detail="Cannot modify pattern in archived version")
        
        pattern.enabled = True
        pattern.updated_at = datetime.utcnow()
        version.updated_at = datetime.utcnow()
        db.commit()
        
        # Reload config if this is the active version
        if version.status == ConfigStatus.ACTIVE:
            config_router = ConfigRouter(db)
            config_router.reload_config()
        
        return {"message": "Pattern enabled"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to enable pattern: {str(e)}")

@router.post("/patterns/{pattern_id}/test-phrases")
async def test_pattern_with_phrases(
    pattern_id: str,
    request: TestPatternWithPhrasesRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Test if a pattern matches specific messages and get detailed results"""
    pattern = db.query(IntentPattern).filter(IntentPattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    try:
        from app.services.ollama_service import OllamaService
        ollama_service = OllamaService()
        results = await ollama_service.test_regex_against_phrases(pattern.pattern, request.test_messages)
        
        return {
            "pattern_id": pattern_id,
            "pattern": pattern.pattern,
            "phrases": getattr(pattern, 'phrases', None),
            "test_results": results,
            "summary": {
                "total_tested": len(request.test_messages),
                "matches": len(results["matches"]),
                "non_matches": len(results["non_matches"]),
                "match_rate": len(results["matches"]) / len(request.test_messages) if request.test_messages else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test pattern: {str(e)}")

@router.post("/patterns/{pattern_id}/improve")
async def improve_pattern(
    pattern_id: str,
    request: ImprovePatternRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Improve a pattern to handle missed phrases or false positives"""
    pattern = db.query(IntentPattern).filter(IntentPattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.id == pattern.version_id)\
        .first()
    
    if version.status == ConfigStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="Cannot modify pattern in archived version")
    
    try:
        from app.services.ollama_service import OllamaService
        ollama_service = OllamaService()
        result = await ollama_service.improve_regex(
            current_regex=pattern.pattern,
            missed_phrases=request.missed_phrases,
            false_positives=request.false_positives or []
        )
        
        if result.get("errors"):
            raise HTTPException(
                status_code=400,
                detail=f"Failed to improve pattern: {', '.join(result['errors'])}"
            )
        
        # Return the suggested improvement without automatically applying it
        return {
            "pattern_id": pattern_id,
            "current_regex": pattern.pattern,
            "suggested_regex": result.get("regex", ""),
            "confidence": result.get("confidence", 0.0),
            "explanation": result.get("explanation", ""),
            "improvements": {
                "missed_phrases": request.missed_phrases,
                "false_positives": request.false_positives or []
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to improve pattern: {str(e)}")

# NEW: Fixed regex generation endpoint with proper Pydantic model
# In your app/api/routers/admin/intent_config/patterns.py file
# Update the generate_regex_from_phrases endpoint

@router.post("/generate-regex", response_model=GenerateRegexResponse)
async def generate_regex_from_phrases(
    request: GenerateRegexRequest,
    ctx = Depends(require_admin)
):
    """Generate regex from phrases without creating a pattern (for testing)"""
    try:
        if not request.phrases:
            raise HTTPException(status_code=400, detail="No phrases provided")
        
        from app.services.ollama_service import OllamaService
        ollama_service = OllamaService()
        result = await ollama_service.generate_regex_from_phrases(
            phrases=request.phrases,
            intent=request.intent,
            pattern_kind=request.pattern_kind
        )
        
        # FIX: Make sure the response matches the Pydantic model
        return GenerateRegexResponse(
            phrases=request.phrases,
            intent=request.intent,
            pattern_kind=request.pattern_kind,
            generated_regex=result.get("regex", ""),  # Use "regex" from service response
            confidence=result.get("confidence", 0.0),
            explanation=result.get("explanation", ""),
            test_matches=result.get("test_matches", []),
            errors=result.get("errors", [])
        )
        
    except Exception as e:
        print(f"Regex generation error: {str(e)}")  # For debugging
        raise HTTPException(status_code=500, detail=f"Failed to generate regex: {str(e)}")

# Also make sure your Pydantic model is correct:
class GenerateRegexResponse(BaseModel):
    phrases: List[str]
    intent: str
    pattern_kind: str
    generated_regex: str  # This should match what frontend expects
    confidence: float
    explanation: str
    test_matches: List[str]
    errors: List[str]

# Legacy endpoint for backward compatibility
@router.post("/patterns/{pattern_id}/test")
def test_pattern(
    pattern_id: str,
    test_message: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Test if a pattern matches a specific message (legacy endpoint)"""
    pattern = db.query(IntentPattern).filter(IntentPattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    import re
    try:
        compiled_pattern = re.compile(pattern.pattern, re.IGNORECASE)
        match = compiled_pattern.search(test_message.lower())
        
        result = {
            "pattern_id": pattern_id,
            "pattern": pattern.pattern,
            "test_message": test_message,
            "matches": match is not None
        }
        
        if match:
            result["match_text"] = match.group(0)
            result["match_start"] = match.start()
            result["match_end"] = match.end()
            if match.groups():
                result["groups"] = match.groups()
            if match.groupdict():
                result["named_groups"] = match.groupdict()
        
        return result
        
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {str(e)}")