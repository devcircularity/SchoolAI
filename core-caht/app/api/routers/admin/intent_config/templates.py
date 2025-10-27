# app/api/routers/admin/intent_config/templates.py
"""Template management for intent configurations"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.db import get_db
from app.api.deps.auth import require_admin
from app.models.intent_config import (
    IntentConfigVersion, PromptTemplate, TemplateType, ConfigStatus
)
from .shared import (
    TemplateResponse, CreateTemplateRequest, UpdateTemplateRequest, safe_enum_value
)

router = APIRouter()

@router.get("/versions/{version_id}/templates", response_model=List[TemplateResponse])
def list_templates(
    version_id: str,
    handler: Optional[str] = Query(None),
    template_type: Optional[str] = Query(None),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List templates for a version with optional filtering"""
    query = db.query(PromptTemplate).filter(PromptTemplate.version_id == version_id)
    
    if handler:
        query = query.filter(PromptTemplate.handler == handler)
    if template_type:
        try:
            type_enum = TemplateType(template_type)
            query = query.filter(PromptTemplate.template_type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid template type")
    
    templates = query.order_by(PromptTemplate.created_at).all()
    
    return [
        TemplateResponse(
            id=template.id,
            handler=template.handler,
            intent=template.intent,
            template_type=safe_enum_value(template.template_type),
            template_text=template.template_text,
            enabled=template.enabled,
            created_at=template.created_at,
            updated_at=template.updated_at
        ) for template in templates
    ]

@router.post("/versions/{version_id}/templates", response_model=TemplateResponse)
def create_template(
    version_id: str,
    request: CreateTemplateRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Add a new template to a version"""
    try:
        # Validate version exists and is not archived
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == version_id)\
            .first()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        if version.status == ConfigStatus.ARCHIVED:
            raise HTTPException(status_code=400, detail="Cannot modify archived version")
        
        # Validate template type
        try:
            template_type = TemplateType(request.template_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid template type")
        
        template = PromptTemplate(
            id=str(uuid.uuid4()),
            version_id=version_id,
            handler=request.handler,
            intent=request.intent,
            template_type=template_type,
            template_text=request.template_text,
            enabled=request.enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(template)
        version.updated_at = datetime.utcnow()
        db.commit()
        
        return TemplateResponse(
            id=template.id,
            handler=template.handler,
            intent=template.intent,
            template_type=safe_enum_value(template.template_type),
            template_text=template.template_text,
            enabled=template.enabled,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed template information"""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateResponse(
        id=template.id,
        handler=template.handler,
        intent=template.intent,
        template_type=safe_enum_value(template.template_type),
        template_text=template.template_text,
        enabled=template.enabled,
        created_at=template.created_at,
        updated_at=template.updated_at
    )

@router.put("/templates/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a template"""
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check version status
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == template.version_id)\
            .first()
        
        if version.status == ConfigStatus.ARCHIVED:
            raise HTTPException(status_code=400, detail="Cannot modify template in archived version")
        
        # Update fields
        if request.handler is not None:
            template.handler = request.handler
        if request.intent is not None:
            template.intent = request.intent
        if request.template_type is not None:
            try:
                template.template_type = TemplateType(request.template_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid template type")
        if request.template_text is not None:
            template.template_text = request.template_text
        if request.enabled is not None:
            template.enabled = request.enabled
        
        template.updated_at = datetime.utcnow()
        version.updated_at = datetime.utcnow()
        db.commit()
        
        return TemplateResponse(
            id=template.id,
            handler=template.handler,
            intent=template.intent,
            template_type=safe_enum_value(template.template_type),
            template_text=template.template_text,
            enabled=template.enabled,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")

@router.delete("/templates/{template_id}")
def delete_template(
    template_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete/disable a template"""
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check version status
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == template.version_id)\
            .first()
        
        if version.status == ConfigStatus.ARCHIVED:
            raise HTTPException(status_code=400, detail="Cannot modify template in archived version")
        
        # Disable instead of delete to preserve history
        template.enabled = False
        template.updated_at = datetime.utcnow()
        version.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Template disabled"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")

@router.post("/templates/{template_id}/enable")
def enable_template(
    template_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Re-enable a disabled template"""
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check version status
        version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.id == template.version_id)\
            .first()
        
        if version.status == ConfigStatus.ARCHIVED:
            raise HTTPException(status_code=400, detail="Cannot modify template in archived version")
        
        template.enabled = True
        template.updated_at = datetime.utcnow()
        version.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Template enabled"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to enable template: {str(e)}")