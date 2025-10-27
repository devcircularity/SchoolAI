# app/api/routers/admin/intent_config/versions.py
"""Version management for intent configurations"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from app.core.db import get_db
from app.api.deps.auth import require_admin
from app.models.intent_config import (
    IntentConfigVersion, IntentPattern, PromptTemplate,
    ConfigStatus
)
from app.services.config_router import ConfigRouter
from .shared import (
    VersionResponse, CreateVersionRequest, safe_enum_value
)

router = APIRouter()

@router.get("/versions", response_model=List[VersionResponse])
def list_versions(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all intent configuration versions"""
    versions = db.query(IntentConfigVersion)\
        .order_by(IntentConfigVersion.created_at.desc())\
        .all()
    
    result = []
    for version in versions:
        # Count patterns and templates
        pattern_count = db.query(IntentPattern)\
            .filter(IntentPattern.version_id == version.id)\
            .count()
        template_count = db.query(PromptTemplate)\
            .filter(PromptTemplate.version_id == version.id)\
            .count()
        
        result.append(VersionResponse(
            id=version.id,
            name=version.name,
            status=safe_enum_value(version.status),
            notes=version.notes,
            created_at=version.created_at,
            updated_at=version.updated_at,
            activated_at=version.activated_at,
            pattern_count=pattern_count,
            template_count=template_count
        ))
    
    return result

@router.post("/versions", response_model=VersionResponse)
def create_version(
    request: CreateVersionRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new candidate configuration version"""
    try:
        # Create new version
        new_version = IntentConfigVersion(
            id=str(uuid.uuid4()),
            name=request.name,
            status=ConfigStatus.CANDIDATE,
            notes=request.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_version)
        db.flush()
        
        pattern_count = 0
        template_count = 0
        
        # Copy from existing version if specified
        if request.copy_from:
            source_version = db.query(IntentConfigVersion)\
                .filter(IntentConfigVersion.id == request.copy_from)\
                .first()
            if not source_version:
                raise HTTPException(status_code=404, detail="Source version not found")
            
            # Copy patterns
            source_patterns = db.query(IntentPattern)\
                .filter(IntentPattern.version_id == request.copy_from)\
                .all()
            
            for pattern in source_patterns:
                new_pattern = IntentPattern(
                    id=str(uuid.uuid4()),
                    version_id=new_version.id,
                    handler=pattern.handler,
                    intent=pattern.intent,
                    kind=pattern.kind,
                    pattern=pattern.pattern,
                    priority=pattern.priority,
                    enabled=pattern.enabled,
                    scope_school_id=pattern.scope_school_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_pattern)
            pattern_count = len(source_patterns)
            
            # Copy templates
            source_templates = db.query(PromptTemplate)\
                .filter(PromptTemplate.version_id == request.copy_from)\
                .all()
            
            for template in source_templates:
                new_template = PromptTemplate(
                    id=str(uuid.uuid4()),
                    version_id=new_version.id,
                    handler=template.handler,
                    intent=template.intent,
                    template_type=template.template_type,
                    template_text=template.template_text,
                    enabled=template.enabled,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_template)
            template_count = len(source_templates)
        
        db.commit()
        
        return VersionResponse(
            id=new_version.id,
            name=new_version.name,
            status=safe_enum_value(new_version.status),
            notes=new_version.notes,
            created_at=new_version.created_at,
            updated_at=new_version.updated_at,
            activated_at=new_version.activated_at,
            pattern_count=pattern_count,
            template_count=template_count
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")

@router.post("/versions/{version_id}/promote")
def promote_version(
    version_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Promote a candidate version to active"""
    try:
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == version_id)\
            .first()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        if version.status != ConfigStatus.CANDIDATE:
            raise HTTPException(status_code=400, detail="Can only promote candidate versions")
        
        # Archive current active version
        current_active = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.status == ConfigStatus.ACTIVE)\
            .first()
        
        if current_active:
            current_active.status = ConfigStatus.ARCHIVED
            current_active.updated_at = datetime.utcnow()
        
        # Promote new version
        version.status = ConfigStatus.ACTIVE
        version.activated_at = datetime.utcnow()
        version.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Force reload of configuration cache
        config_router = ConfigRouter(db)
        config_router.reload_config()
        
        return {"message": f"Version '{version.name}' promoted to active"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to promote version: {str(e)}")

@router.post("/versions/{version_id}/archive")
def archive_version(
    version_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Archive a version"""
    try:
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == version_id)\
            .first()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        if version.status == ConfigStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Cannot archive active version")
        
        version.status = ConfigStatus.ARCHIVED
        version.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": f"Version '{version.name}' archived"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to archive version: {str(e)}")

@router.get("/versions/{version_id}", response_model=VersionResponse)
def get_version(
    version_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed version information"""
    version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.id == version_id)\
        .first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Count patterns and templates
    pattern_count = db.query(IntentPattern)\
        .filter(IntentPattern.version_id == version.id)\
        .count()
    template_count = db.query(PromptTemplate)\
        .filter(PromptTemplate.version_id == version.id)\
        .count()
    
    return VersionResponse(
        id=version.id,
        name=version.name,
        status=safe_enum_value(version.status),
        notes=version.notes,
        created_at=version.created_at,
        updated_at=version.updated_at,
        activated_at=version.activated_at,
        pattern_count=pattern_count,
        template_count=template_count
    )