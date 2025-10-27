# app/api/routers/admin/configuration.py
"""Unified configuration management endpoints for admin"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.system_settings import SystemSetting
from pydantic import BaseModel

from app.core.db import get_db
from app.api.deps.auth import require_admin
from app.models.intent_config import (
    IntentConfigVersion, IntentPattern, PromptTemplate,
    ConfigStatus, PatternKind, TemplateType
)
from app.services.config_router import ConfigRouter
from .intent_config.shared import (
    VersionResponse, PatternResponse, TemplateResponse, safe_enum_value
)

router = APIRouter(prefix="/admin/configuration", tags=["Admin - Configuration Management"])

class ConfigOverviewResponse:
    def __init__(self, 
                 active_version: Optional[IntentConfigVersion],
                 candidate_version: Optional[IntentConfigVersion],
                 total_patterns: int,
                 total_templates: int,
                 enabled_patterns: int,
                 enabled_templates: int,
                 system_health: str,
                 cache_status: str):
        self.active_version = active_version
        self.candidate_version = candidate_version
        self.total_patterns = total_patterns
        self.total_templates = total_templates
        self.enabled_patterns = enabled_patterns
        self.enabled_templates = enabled_templates
        self.system_health = system_health
        self.cache_status = cache_status

@router.get("/overview")
def get_configuration_overview(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive configuration overview"""
    
    # Get versions
    active_version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.status == ConfigStatus.ACTIVE)\
        .first()
    
    candidate_version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.status == ConfigStatus.CANDIDATE)\
        .first()
    
    # Get pattern counts
    total_patterns = db.query(IntentPattern).count()
    enabled_patterns = db.query(IntentPattern)\
        .filter(IntentPattern.enabled == True)\
        .count()
    
    # Get template counts
    total_templates = db.query(PromptTemplate).count()
    enabled_templates = db.query(PromptTemplate)\
        .filter(PromptTemplate.enabled == True)\
        .count()
    
    # Check system health
    config_router = ConfigRouter(db)
    try:
        cache_stats = config_router.get_cache_stats()
        cache_status = cache_stats.get("status", "unknown")
        system_health = "healthy" if (active_version and cache_status == "loaded") else "warning"
    except Exception:
        cache_status = "error"
        system_health = "error"
    
    return {
        "active_version": {
            "id": active_version.id,
            "name": active_version.name,
            "status": safe_enum_value(active_version.status),
            "pattern_count": active_version.pattern_count if hasattr(active_version, 'pattern_count') else 0,
            "template_count": active_version.template_count if hasattr(active_version, 'template_count') else 0,
            "activated_at": active_version.activated_at.isoformat() if active_version.activated_at else None,
            "created_at": active_version.created_at.isoformat(),
            "updated_at": active_version.updated_at.isoformat()
        } if active_version else None,
        
        "candidate_version": {
            "id": candidate_version.id,
            "name": candidate_version.name,
            "status": safe_enum_value(candidate_version.status),
            "pattern_count": candidate_version.pattern_count if hasattr(candidate_version, 'pattern_count') else 0,
            "template_count": candidate_version.template_count if hasattr(candidate_version, 'template_count') else 0,
            "created_at": candidate_version.created_at.isoformat(),
            "updated_at": candidate_version.updated_at.isoformat()
        } if candidate_version else None,
        
        "total_patterns": total_patterns,
        "total_templates": total_templates,
        "enabled_patterns": enabled_patterns,
        "enabled_templates": enabled_templates,
        "system_health": system_health,
        "cache_status": cache_status
    }

@router.get("/stats")
def get_configuration_stats(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed configuration statistics"""
    
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
    
    # Pattern statistics
    pattern_stats = {
        "total": db.query(IntentPattern).count(),
        "enabled": db.query(IntentPattern).filter(IntentPattern.enabled == True).count(),
        "by_kind": {}
    }
    
    for kind in PatternKind:
        count = db.query(IntentPattern)\
            .filter(IntentPattern.kind == kind)\
            .count()
        pattern_stats["by_kind"][kind.value] = count
    
    # Template statistics
    template_stats = {
        "total": db.query(PromptTemplate).count(),
        "enabled": db.query(PromptTemplate).filter(PromptTemplate.enabled == True).count(),
        "by_type": {}
    }
    
    for template_type in TemplateType:
        count = db.query(PromptTemplate)\
            .filter(PromptTemplate.template_type == template_type)\
            .count()
        template_stats["by_type"][template_type.value] = count
    
    # Handler distribution
    handler_stats = db.query(
        IntentPattern.handler,
        func.count(IntentPattern.id).label('pattern_count')
    ).group_by(IntentPattern.handler)\
     .order_by(func.count(IntentPattern.id).desc())\
     .limit(10)\
     .all()
    
    # Intent distribution
    intent_stats = db.query(
        IntentPattern.intent,
        func.count(IntentPattern.id).label('pattern_count')
    ).group_by(IntentPattern.intent)\
     .order_by(func.count(IntentPattern.id).desc())\
     .limit(10)\
     .all()
    
    return {
        "versions": {
            "active": active_versions,
            "candidate": candidate_versions,
            "archived": archived_versions
        },
        "patterns": pattern_stats,
        "templates": template_stats,
        "top_handlers": [
            {"handler": handler, "count": count}
            for handler, count in handler_stats
        ],
        "top_intents": [
            {"intent": intent, "count": count}
            for intent, count in intent_stats
        ]
    }

@router.get("/health")
def get_system_health(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Comprehensive system health check"""
    
    issues = []
    
    # Check for active configuration
    active_version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.status == ConfigStatus.ACTIVE)\
        .first()
    
    if not active_version:
        issues.append({
            "severity": "critical",
            "component": "configuration",
            "message": "No active configuration version found"
        })
    
    # Check cache status
    try:
        config_router = ConfigRouter(db)
        cache_stats = config_router.get_cache_stats()
        cache_status = cache_stats.get("status", "unknown")
        
        if cache_status != "loaded":
            issues.append({
                "severity": "warning",
                "component": "cache",
                "message": f"Configuration cache status: {cache_status}"
            })
    except Exception as e:
        issues.append({
            "severity": "error",
            "component": "cache",
            "message": f"Cache health check failed: {str(e)}"
        })
    
    # Check for enabled patterns
    if active_version:
        enabled_patterns = db.query(IntentPattern)\
            .filter(
                IntentPattern.version_id == active_version.id,
                IntentPattern.enabled == True
            )\
            .count()
        
        if enabled_patterns == 0:
            issues.append({
                "severity": "critical",
                "component": "patterns",
                "message": "No enabled patterns found in active configuration"
            })
    
    # Check for pattern conflicts or issues
    if active_version:
        patterns = db.query(IntentPattern)\
            .filter(
                IntentPattern.version_id == active_version.id,
                IntentPattern.enabled == True
            )\
            .all()
        
        # Test pattern compilation
        import re
        for pattern in patterns:
            try:
                re.compile(pattern.pattern, re.IGNORECASE)
            except re.error as e:
                issues.append({
                    "severity": "error",
                    "component": "patterns",
                    "message": f"Invalid regex in pattern {pattern.id}: {str(e)}"
                })
    
    # Determine overall health
    if any(issue["severity"] == "critical" for issue in issues):
        overall_health = "critical"
    elif any(issue["severity"] == "error" for issue in issues):
        overall_health = "error"
    elif any(issue["severity"] == "warning" for issue in issues):
        overall_health = "warning"
    else:
        overall_health = "healthy"
    
    return {
        "overall_health": overall_health,
        "issues": issues,
        "last_checked": datetime.utcnow().isoformat(),
        "active_version": {
            "id": active_version.id,
            "name": active_version.name
        } if active_version else None
    }

@router.get("/cache/stats")
def get_cache_stats(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get configuration cache statistics"""
    try:
        config_router = ConfigRouter(db)
        return config_router.get_cache_stats()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "last_updated": None
        }

@router.post("/cache/reload")
def reload_cache(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Force reload of configuration cache"""
    try:
        config_router = ConfigRouter(db)
        config_router.reload_config()
        stats = config_router.get_cache_stats()
        return {
            "message": "Configuration cache reloaded successfully",
            "cache_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload cache: {str(e)}")

@router.get("/export/{version_id}")
def export_configuration(
    version_id: str,
    format: str = Query("json", description="Export format: json or yaml"),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export configuration version for backup or migration"""
    from fastapi.responses import Response
    import json
    import yaml
    
    # Get version
    version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.id == version_id)\
        .first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get patterns and templates
    patterns = db.query(IntentPattern)\
        .filter(IntentPattern.version_id == version_id)\
        .all()
    
    templates = db.query(PromptTemplate)\
        .filter(PromptTemplate.version_id == version_id)\
        .all()
    
    # Build export data
    export_data = {
        "metadata": {
            "version_id": version.id,
            "version_name": version.name,
            "status": safe_enum_value(version.status),
            "notes": version.notes,
            "exported_at": datetime.utcnow().isoformat(),
            "export_format_version": "1.0"
        },
        "patterns": [
            {
                "id": p.id,
                "handler": p.handler,
                "intent": p.intent,
                "kind": safe_enum_value(p.kind),
                "pattern": p.pattern,
                "priority": p.priority,
                "enabled": p.enabled,
                "scope_school_id": p.scope_school_id,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            } for p in patterns
        ],
        "templates": [
            {
                "id": t.id,
                "handler": t.handler,
                "intent": t.intent,
                "template_type": safe_enum_value(t.template_type),
                "template_text": t.template_text,
                "enabled": t.enabled,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat()
            } for t in templates
        ]
    }
    
    # Format output
    if format.lower() == "yaml":
        content = yaml.dump(export_data, default_flow_style=False, sort_keys=False)
        media_type = "application/x-yaml"
        file_extension = "yaml"
    else:
        content = json.dumps(export_data, indent=2, ensure_ascii=False)
        media_type = "application/json"
        file_extension = "json"
    
    filename = f"config_{version.name.replace(' ', '_')}_{version_id[:8]}.{file_extension}"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/validate/{version_id}")
def validate_configuration(
    version_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Validate all patterns and templates in a configuration version"""
    import re
    
    version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.id == version_id)\
        .first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    patterns = db.query(IntentPattern)\
        .filter(IntentPattern.version_id == version_id)\
        .all()
    
    templates = db.query(PromptTemplate)\
        .filter(PromptTemplate.version_id == version_id)\
        .all()
    
    validation_results = {
        "version_id": version_id,
        "version_name": version.name,
        "patterns": {
            "total": len(patterns),
            "valid": 0,
            "invalid": 0,
            "errors": []
        },
        "templates": {
            "total": len(templates),
            "valid": len(templates),  # Templates don't have regex validation
            "invalid": 0,
            "errors": []
        },
        "overall_valid": True
    }
    
    # Validate patterns
    for pattern in patterns:
        try:
            re.compile(pattern.pattern, re.IGNORECASE)
            validation_results["patterns"]["valid"] += 1
        except re.error as e:
            validation_results["patterns"]["invalid"] += 1
            validation_results["patterns"]["errors"].append({
                "pattern_id": pattern.id,
                "intent": pattern.intent,
                "pattern": pattern.pattern,
                "error": str(e)
            })
            validation_results["overall_valid"] = False
    
    # Templates are generally valid (no regex compilation needed)
    # Could add template variable validation here if needed
    
    return validation_results


# --- Hide Tester Queue Setting Endpoints ---

class HideTesterQueueRequest(BaseModel):
    hidden: bool

@router.get("/settings/hide-tester-queue")
def get_hide_tester_queue_setting(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get the hide tester queue setting"""
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "hide_tester_queue"
    ).first()
    
    return {
        "hidden": setting.value.get("hidden", False) if setting else False,
        "updated_at": setting.updated_at.isoformat() if setting else None,
        "updated_by": setting.updated_by if setting else None
    }

@router.post("/settings/hide-tester-queue")
def set_hide_tester_queue_setting(
    request: HideTesterQueueRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle the hide tester queue setting - Admin only"""
    
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "hide_tester_queue"
    ).first()
    
    if setting:
        setting.value = {"hidden": request.hidden}
        setting.updated_by = str(ctx["user"].id)
        setting.updated_at = datetime.utcnow()
    else:
        setting = SystemSetting(
            key="hide_tester_queue",
            value={"hidden": request.hidden},
            description="Hide problem queue from all testers (admins can still access)",
            updated_by=str(ctx["user"].id)
        )
        db.add(setting)
    
    db.commit()
    
    action = "hidden from" if request.hidden else "visible to"
    
    return {
        "message": f"Tester queue is now {action} testers",
        "hidden": request.hidden,
        "updated_at": setting.updated_at.isoformat(),
        "updated_by": str(ctx["user"].id)
    }