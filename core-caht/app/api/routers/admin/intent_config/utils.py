# app/api/routers/admin/intent_config/utils.py
"""Utility endpoints for intent configuration management"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from app.core.db import get_db
from app.api.deps.auth import require_admin
from app.models.intent_config import (
    IntentConfigVersion, IntentPattern, PromptTemplate, RoutingLog,
    ConfigStatus, PatternKind, TemplateType
)
from app.services.config_router import ConfigRouter

router = APIRouter()

@router.get("/stats")
def get_stats(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics"""
    try:
        # Version counts
        active_versions = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.status == ConfigStatus.ACTIVE)\
            .count()
        candidate_versions = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.status == ConfigStatus.CANDIDATE)\
            .count()
        archived_versions = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.status == ConfigStatus.ARCHIVED)\
            .count()
        
        # Pattern counts
        total_patterns = db.query(IntentPattern).count()
        enabled_patterns = db.query(IntentPattern)\
            .filter(IntentPattern.enabled == True)\
            .count()
        
        # Template counts
        total_templates = db.query(PromptTemplate).count()
        enabled_templates = db.query(PromptTemplate)\
            .filter(PromptTemplate.enabled == True)\
            .count()
        
        # Recent logs
        recent_logs = db.query(RoutingLog)\
            .filter(RoutingLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))\
            .count()
        
        # Fallback rate
        fallback_logs = db.query(RoutingLog)\
            .filter(
                RoutingLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                RoutingLog.fallback_used == True
            )\
            .count()
        
        fallback_rate = (fallback_logs / recent_logs * 100) if recent_logs > 0 else 0
        
        # Cache stats
        config_router = ConfigRouter(db)
        cache_stats = config_router.get_cache_stats()
        
        return {
            "versions": {
                "active": active_versions,
                "candidate": candidate_versions,
                "archived": archived_versions
            },
            "patterns": {
                "total": total_patterns,
                "enabled": enabled_patterns
            },
            "templates": {
                "total": total_templates,
                "enabled": enabled_templates
            },
            "routing": {
                "messages_today": recent_logs,
                "fallback_rate": round(fallback_rate, 2)
            },
            "cache": cache_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/handlers")
def get_available_handlers(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get list of available handlers from existing patterns"""
    handlers = db.query(IntentPattern.handler)\
        .distinct()\
        .order_by(IntentPattern.handler)\
        .all()
    
    return {"handlers": [handler[0] for handler in handlers]}

@router.get("/intents")
def get_available_intents(
    handler: Optional[str] = Query(None, description="Filter by handler"),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get list of available intents, optionally filtered by handler"""
    query = db.query(IntentPattern.intent).distinct()
    
    if handler:
        query = query.filter(IntentPattern.handler == handler)
    
    intents = query.order_by(IntentPattern.intent).all()
    
    return {"intents": [intent[0] for intent in intents]}

@router.get("/pattern-kinds")
def get_pattern_kinds(ctx = Depends(require_admin)):
    """Get available pattern kinds"""
    return {
        "kinds": [
            {"value": kind.value, "label": kind.value.title()}
            for kind in PatternKind
        ]
    }

@router.get("/template-types") 
def get_template_types(ctx = Depends(require_admin)):
    """Get available template types"""
    return {
        "types": [
            {"value": type.value, "label": type.value.title()}
            for type in TemplateType
        ]
    }

@router.get("/health")
def get_health(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Health check for intent configuration system"""
    try:
        # Check if we have an active configuration
        active_version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.status == ConfigStatus.ACTIVE)\
            .first()
        
        # Check cache status
        config_router = ConfigRouter(db)
        cache_stats = config_router.get_cache_stats()
        
        # Count patterns and templates in active version
        active_patterns = 0
        active_templates = 0
        if active_version:
            active_patterns = db.query(IntentPattern)\
                .filter(
                    IntentPattern.version_id == active_version.id,
                    IntentPattern.enabled == True
                )\
                .count()
            active_templates = db.query(PromptTemplate)\
                .filter(
                    PromptTemplate.version_id == active_version.id,
                    PromptTemplate.enabled == True
                )\
                .count()
        
        is_healthy = (
            active_version is not None and
            cache_stats["status"] == "loaded" and
            active_patterns > 0
        )
        
        return {
            "healthy": is_healthy,
            "active_version": {
                "id": active_version.id if active_version else None,
                "name": active_version.name if active_version else None,
                "patterns": active_patterns,
                "templates": active_templates
            },
            "cache": cache_stats,
            "issues": [] if is_healthy else [
                "No active configuration version" if not active_version else None,
                "Configuration cache not loaded" if cache_stats["status"] != "loaded" else None,
                "No active patterns found" if active_patterns == 0 else None
            ]
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "active_version": None,
            "cache": {"status": "error"},
            "issues": [f"Health check failed: {str(e)}"]
        }

@router.get("/backup/{version_id}")
def backup_version(
    version_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a backup export of a configuration version"""
    from fastapi.responses import Response
    import json
    
    # Get version
    version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.id == version_id)\
        .first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get patterns
    patterns = db.query(IntentPattern)\
        .filter(IntentPattern.version_id == version_id)\
        .all()
    
    # Get templates
    templates = db.query(PromptTemplate)\
        .filter(PromptTemplate.version_id == version_id)\
        .all()
    
    # Build export data
    export_data = {
        "version": {
            "id": version.id,
            "name": version.name,
            "status": version.status.value if hasattr(version.status, 'value') else str(version.status),
            "notes": version.notes,
            "created_at": version.created_at.isoformat(),
            "updated_at": version.updated_at.isoformat()
        },
        "patterns": [
            {
                "id": p.id,
                "handler": p.handler,
                "intent": p.intent,
                "kind": p.kind.value if hasattr(p.kind, 'value') else str(p.kind),
                "pattern": p.pattern,
                "priority": p.priority,
                "enabled": p.enabled,
                "scope_school_id": p.scope_school_id
            } for p in patterns
        ],
        "templates": [
            {
                "id": t.id,
                "handler": t.handler,
                "intent": t.intent,
                "template_type": t.template_type.value if hasattr(t.template_type, 'value') else str(t.template_type),
                "template_text": t.template_text,
                "enabled": t.enabled
            } for t in templates
        ],
        "exported_at": datetime.utcnow().isoformat(),
        "export_version": "1.0"
    }
    
    content = json.dumps(export_data, indent=2)
    
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=intent_config_{version.name.replace(' ', '_')}_{version_id[:8]}.json"
        }
    )