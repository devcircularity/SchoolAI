# app/api/routers/admin/suggestion_management.py - Updated with action items loading
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import uuid
from pydantic import BaseModel

from app.core.db import get_db
from app.models.intent_suggestion import IntentSuggestion, SuggestionStatus, SuggestionType
from app.models.intent_config import IntentConfigVersion, IntentPattern, PromptTemplate, PatternKind, TemplateType, ConfigStatus
from app.models.chat import ChatMessage, MessageType
from app.models.user import User
from app.api.deps.auth import require_admin
from app.services.config_router import ConfigRouter
from app.models.action_item import SuggestionActionItem

router = APIRouter(prefix="/admin/suggestions", tags=["Admin - Suggestion Management"])

# Pydantic schemas
class ActionItemResponse(BaseModel):
    id: str
    suggestion_id: str
    title: str
    description: Optional[str]
    priority: str
    implementation_type: str
    status: str
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    created_by: str
    created_by_name: str
    due_date: Optional[str]
    completed_at: Optional[str]
    created_at: str
    updated_at: str

class SuggestionResponse(BaseModel):
    id: str
    chat_message_id: Optional[str]
    routing_log_id: Optional[str]
    suggestion_type: str
    title: str
    description: str
    handler: str
    intent: str
    pattern: Optional[str]
    template_text: Optional[str]
    priority: str
    tester_note: Optional[str]
    admin_note: Optional[str]
    status: str
    created_by: str
    created_by_name: str
    reviewed_by: Optional[str]
    reviewed_by_name: Optional[str]
    school_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime]
    implemented_at: Optional[datetime]
    
    # Enhanced fields
    admin_analysis: Optional[str] = None
    implementation_notes: Optional[str] = None
    action_items: List[ActionItemResponse] = []
    
    # Context information
    original_message: Optional[str] = None
    assistant_response: Optional[str] = None

class SuggestionListResponse(BaseModel):
    suggestions: List[SuggestionResponse]
    total: int
    page: int
    limit: int
    has_next: bool

class ReviewSuggestionRequest(BaseModel):
    status: str
    admin_note: Optional[str] = None
    auto_implement: bool = False

class ActionItemRequest(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    implementation_type: str = "other"

class EnhancedReviewSuggestionRequest(BaseModel):
    status: str
    admin_note: Optional[str] = None
    admin_analysis: Optional[str] = None
    implementation_notes: Optional[str] = None
    create_action_items: bool = False
    action_items: List[ActionItemRequest] = []

class CreateActionItemRequest(BaseModel):
    suggestion_id: str
    title: str
    description: str
    priority: str = "medium"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    implementation_type: str = "other"

class SuggestionStatsResponse(BaseModel):
    total_suggestions: int
    pending: int
    approved: int
    rejected: int
    implemented: int
    needs_analysis: int = 0
    by_type: dict
    by_priority: dict

class EnhancedSuggestionStatsResponse(BaseModel):
    total_suggestions: int
    pending: int
    approved: int
    rejected: int
    implemented: int
    needs_analysis: int = 0
    by_type: dict
    by_priority: dict
    action_items: dict = {
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "overdue": 0
    }
    suggestions_with_action_items: int = 0
    avg_time_to_resolution: Optional[float] = None

# Helper function to serialize action items
def _serialize_action_items(suggestion: IntentSuggestion, db: Session) -> List[dict]:
    """Serialize action items for a suggestion"""
    action_items_data = []
    
    if hasattr(suggestion, 'action_items_rel') and suggestion.action_items_rel:
        for action_item in suggestion.action_items_rel:
            # Ensure assignee is loaded
            assignee_name = None
            if action_item.assigned_to:
                if action_item.assignee:
                    assignee_name = action_item.assignee.full_name
                else:
                    # Load assignee if not already loaded
                    assignee = db.query(User).filter(User.id == action_item.assigned_to).first()
                    assignee_name = assignee.full_name if assignee else None
            
            action_items_data.append({
                "id": str(action_item.id),
                "suggestion_id": str(action_item.suggestion_id),
                "title": action_item.title,
                "description": action_item.description,
                "priority": action_item.priority,
                "implementation_type": action_item.implementation_type,
                "status": action_item.status,
                "assigned_to": str(action_item.assigned_to) if action_item.assigned_to else None,
                "assigned_to_name": assignee_name,
                "created_by": str(suggestion.created_by),
                "created_by_name": suggestion.creator.full_name if suggestion.creator else "Unknown",
                "due_date": action_item.due_date.isoformat() if action_item.due_date else None,
                "completed_at": action_item.completed_at.isoformat() if action_item.completed_at else None,
                "created_at": action_item.created_at.isoformat(),
                "updated_at": action_item.updated_at.isoformat()
            })
    
    return action_items_data

@router.get("/", response_model=SuggestionListResponse)
def list_suggestions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    suggestion_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    created_by: Optional[str] = Query(None, description="Filter by creator user ID"),
    school_id: Optional[str] = Query(None, description="Filter by school"),
    pending_only: bool = Query(False, description="Show only pending suggestions"),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List suggestions with filtering and pagination"""
    
    # Build query with eager loading - INCLUDING ACTION ITEMS
    query = db.query(IntentSuggestion).options(
        joinedload(IntentSuggestion.creator),
        joinedload(IntentSuggestion.reviewer),
        joinedload(IntentSuggestion.chat_message),
        joinedload(IntentSuggestion.action_items_rel).joinedload(SuggestionActionItem.assignee)
    )
    
    # Apply filters
    filters = []
    
    if status:
        try:
            status_enum = SuggestionStatus(status)
            filters.append(IntentSuggestion.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    if suggestion_type:
        try:
            type_enum = SuggestionType(suggestion_type)
            filters.append(IntentSuggestion.suggestion_type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid suggestion type")
    
    if priority:
        if priority not in ["low", "medium", "high", "critical"]:
            raise HTTPException(status_code=400, detail="Invalid priority")
        filters.append(IntentSuggestion.priority == priority)
    
    if created_by:
        try:
            user_uuid = UUID(created_by)
            filters.append(IntentSuggestion.created_by == user_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if school_id:
        try:
            school_uuid = UUID(school_id)
            filters.append(IntentSuggestion.school_id == school_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school ID")
    
    if pending_only:
        filters.append(IntentSuggestion.status == SuggestionStatus.PENDING)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    query = query.order_by(desc(IntentSuggestion.created_at))
    query = query.offset((page - 1) * limit).limit(limit)
    
    suggestions = query.all()
    
    # Build response with action items
    suggestion_responses = []
    for suggestion in suggestions:
        # Get original message context if available
        original_message = None
        assistant_response = None
        
        if suggestion.chat_message:
            original_message = _get_user_message_before(db, suggestion.chat_message)
            assistant_response = suggestion.chat_message.content
        
        # Serialize action items
        action_items_data = _serialize_action_items(suggestion, db)
        
        suggestion_responses.append(SuggestionResponse(
            id=str(suggestion.id),
            chat_message_id=str(suggestion.chat_message_id) if suggestion.chat_message_id else None,
            routing_log_id=suggestion.routing_log_id,
            suggestion_type=suggestion.suggestion_type.value,
            title=suggestion.title,
            description=suggestion.description,
            handler=suggestion.handler,
            intent=suggestion.intent,
            pattern=suggestion.pattern,
            template_text=suggestion.template_text,
            priority=suggestion.priority,
            tester_note=suggestion.tester_note,
            admin_note=suggestion.admin_note,
            status=suggestion.status.value,
            created_by=str(suggestion.created_by),
            created_by_name=suggestion.creator.full_name if suggestion.creator else "Unknown",
            reviewed_by=str(suggestion.reviewed_by) if suggestion.reviewed_by else None,
            reviewed_by_name=suggestion.reviewer.full_name if suggestion.reviewer else None,
            school_id=str(suggestion.school_id) if suggestion.school_id else None,
            created_at=suggestion.created_at,
            updated_at=suggestion.updated_at,
            reviewed_at=suggestion.reviewed_at,
            implemented_at=suggestion.implemented_at,
            original_message=original_message,
            assistant_response=assistant_response,
            admin_analysis=getattr(suggestion, 'admin_analysis', None),
            implementation_notes=getattr(suggestion, 'implementation_notes', None),
            action_items=action_items_data
        ))
    
    return SuggestionListResponse(
        suggestions=suggestion_responses,
        total=total,
        page=page,
        limit=limit,
        has_next=(page * limit) < total
    )

@router.get("/stats", response_model=SuggestionStatsResponse)
def get_suggestion_stats(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get suggestion statistics"""
    
    try:
        total_suggestions = db.query(IntentSuggestion).count()
        
        # Safely query for each status
        pending = db.query(IntentSuggestion).filter(
            IntentSuggestion.status == SuggestionStatus.PENDING
        ).count()
        
        approved = db.query(IntentSuggestion).filter(
            IntentSuggestion.status == SuggestionStatus.APPROVED
        ).count()
        
        rejected = db.query(IntentSuggestion).filter(
            IntentSuggestion.status == SuggestionStatus.REJECTED
        ).count()
        
        implemented = db.query(IntentSuggestion).filter(
            IntentSuggestion.status == SuggestionStatus.IMPLEMENTED
        ).count()
        
        # Safely check for NEEDS_ANALYSIS status
        needs_analysis = 0
        try:
            needs_analysis = db.query(IntentSuggestion).filter(
                IntentSuggestion.status == SuggestionStatus.NEEDS_ANALYSIS
            ).count()
        except AttributeError:
            # NEEDS_ANALYSIS doesn't exist in enum
            pass
        
        # Get counts by type
        by_type = {}
        for suggestion_type in SuggestionType:
            count = db.query(IntentSuggestion).filter(
                IntentSuggestion.suggestion_type == suggestion_type
            ).count()
            by_type[suggestion_type.value] = count
        
        # Get counts by priority
        by_priority = {}
        for priority in ["low", "medium", "high", "critical"]:
            count = db.query(IntentSuggestion).filter(
                IntentSuggestion.priority == priority
            ).count()
            by_priority[priority] = count
        
        return SuggestionStatsResponse(
            total_suggestions=total_suggestions,
            pending=pending,
            approved=approved,
            rejected=rejected,
            implemented=implemented,
            needs_analysis=needs_analysis,
            by_type=by_type,
            by_priority=by_priority
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()  # This will show you the actual error
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get suggestion stats: {str(e)}"
        )

@router.get("/{suggestion_id}", response_model=SuggestionResponse)
def get_suggestion(
    suggestion_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed suggestion information"""
    
    try:
        suggestion_uuid = UUID(suggestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid suggestion ID")
    
    suggestion = db.query(IntentSuggestion).options(
        joinedload(IntentSuggestion.creator),
        joinedload(IntentSuggestion.reviewer),
        joinedload(IntentSuggestion.chat_message),
        joinedload(IntentSuggestion.action_items_rel).joinedload(SuggestionActionItem.assignee)
    ).filter(IntentSuggestion.id == suggestion_uuid).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Get context
    original_message = None
    assistant_response = None
    
    if suggestion.chat_message:
        original_message = _get_user_message_before(db, suggestion.chat_message)
        assistant_response = suggestion.chat_message.content
    
    # Serialize action items
    action_items_data = _serialize_action_items(suggestion, db)
    
    return SuggestionResponse(
        id=str(suggestion.id),
        chat_message_id=str(suggestion.chat_message_id) if suggestion.chat_message_id else None,
        routing_log_id=suggestion.routing_log_id,
        suggestion_type=suggestion.suggestion_type.value,
        title=suggestion.title,
        description=suggestion.description,
        handler=suggestion.handler,
        intent=suggestion.intent,
        pattern=suggestion.pattern,
        template_text=suggestion.template_text,
        priority=suggestion.priority,
        tester_note=suggestion.tester_note,
        admin_note=suggestion.admin_note,
        status=suggestion.status.value,
        created_by=str(suggestion.created_by),
        created_by_name=suggestion.creator.full_name if suggestion.creator else "Unknown",
        reviewed_by=str(suggestion.reviewed_by) if suggestion.reviewed_by else None,
        reviewed_by_name=suggestion.reviewer.full_name if suggestion.reviewer else None,
        school_id=str(suggestion.school_id) if suggestion.school_id else None,
        created_at=suggestion.created_at,
        updated_at=suggestion.updated_at,
        reviewed_at=suggestion.reviewed_at,
        implemented_at=suggestion.implemented_at,
        original_message=original_message,
        assistant_response=assistant_response,
        admin_analysis=getattr(suggestion, 'admin_analysis', None),
        implementation_notes=getattr(suggestion, 'implementation_notes', None),
        action_items=action_items_data
    )

@router.post("/{suggestion_id}/review")
def review_suggestion(
    suggestion_id: str,
    request: ReviewSuggestionRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Review and approve/reject a suggestion"""
    
    try:
        suggestion_uuid = UUID(suggestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid suggestion ID")
    
    suggestion = db.query(IntentSuggestion).filter(IntentSuggestion.id == suggestion_uuid).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    if suggestion.status != SuggestionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only review pending suggestions")
    
    try:
        new_status = SuggestionStatus(request.status)
        if new_status not in [SuggestionStatus.APPROVED, SuggestionStatus.REJECTED]:
            raise ValueError("Invalid status")
    except ValueError:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")
    
    try:
        suggestion.status = new_status
        suggestion.admin_note = request.admin_note
        suggestion.reviewed_by = ctx["user"].id
        suggestion.reviewed_at = datetime.utcnow()
        suggestion.updated_at = datetime.utcnow()
        
        result = {"message": f"Suggestion {new_status.value}"}
        
        if new_status == SuggestionStatus.APPROVED and request.auto_implement:
            implementation_result = _implement_suggestion(db, suggestion)
            result.update(implementation_result)
        
        db.commit()
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to review suggestion: {str(e)}")

@router.post("/{suggestion_id}/implement")
def implement_suggestion(
    suggestion_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Implement an approved suggestion"""
    
    try:
        suggestion_uuid = UUID(suggestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid suggestion ID")
    
    suggestion = db.query(IntentSuggestion).filter(IntentSuggestion.id == suggestion_uuid).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    if suggestion.status != SuggestionStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Can only implement approved suggestions")
    
    try:
        result = _implement_suggestion(db, suggestion)
        db.commit()
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to implement suggestion: {str(e)}")

@router.post("/{suggestion_id}/review-enhanced")
def review_suggestion_enhanced(
    suggestion_id: str,
    request: EnhancedReviewSuggestionRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Enhanced review process with action item creation"""
    
    try:
        suggestion_uuid = UUID(suggestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid suggestion ID")
    
    suggestion = db.query(IntentSuggestion).filter(IntentSuggestion.id == suggestion_uuid).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    if suggestion.status not in [SuggestionStatus.PENDING, SuggestionStatus.APPROVED]:
        raise HTTPException(status_code=400, detail="Can only review pending or approved suggestions")
    
    try:
        suggestion.status = SuggestionStatus(request.status)
        suggestion.admin_note = request.admin_note
        suggestion.reviewed_by = ctx["user"].id
        suggestion.reviewed_at = datetime.utcnow()
        suggestion.updated_at = datetime.utcnow()
        
        if hasattr(suggestion, 'admin_analysis'):
            suggestion.admin_analysis = request.admin_analysis
        if hasattr(suggestion, 'implementation_notes'):
            suggestion.implementation_notes = request.implementation_notes
        
        result = {
            "message": f"Suggestion {request.status}",
            "action_items_created": []
        }
        
        if request.create_action_items and request.action_items:
            for action_item_req in request.action_items:
                action_item = SuggestionActionItem(
                    id=str(uuid.uuid4()),
                    suggestion_id=suggestion_uuid,
                    title=action_item_req.title,
                    description=action_item_req.description,
                    priority=action_item_req.priority,
                    implementation_type=action_item_req.implementation_type,
                    assigned_to=UUID(action_item_req.assigned_to) if action_item_req.assigned_to else None,
                    due_date=action_item_req.due_date,
                    status="pending",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(action_item)
                result["action_items_created"].append({
                    "id": action_item.id,
                    "title": action_item.title
                })
        
        db.commit()
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to review suggestion: {str(e)}")

@router.post("/{suggestion_id}/mark-addressed")
def mark_suggestion_addressed(
    suggestion_id: str,
    completion_notes: Optional[str] = None,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Mark a suggestion as addressed"""
    
    try:
        suggestion_uuid = UUID(suggestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid suggestion ID")
    
    suggestion = db.query(IntentSuggestion).filter(IntentSuggestion.id == suggestion_uuid).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    try:
        suggestion.status = SuggestionStatus.IMPLEMENTED
        suggestion.implemented_at = datetime.utcnow()
        suggestion.updated_at = datetime.utcnow()
        
        if completion_notes:
            suggestion.admin_note = (suggestion.admin_note or "") + f"\n\nCompleted: {completion_notes}"
        
        db.commit()
        
        return {
            "message": "Suggestion marked as addressed",
            "suggestion_id": suggestion_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to mark suggestion as addressed: {str(e)}")

@router.post("/{suggestion_id}/action-items")
def create_action_item_for_suggestion(
    suggestion_id: str,
    request: CreateActionItemRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create an action item for a suggestion"""
    
    try:
        suggestion_uuid = UUID(suggestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid suggestion ID")
    
    suggestion = db.query(IntentSuggestion).filter(IntentSuggestion.id == suggestion_uuid).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    try:
        action_item = SuggestionActionItem(
            id=str(uuid.uuid4()),
            suggestion_id=suggestion_uuid,
            title=request.title,
            description=request.description,
            priority=request.priority,
            implementation_type=request.implementation_type,
            assigned_to=UUID(request.assigned_to) if request.assigned_to else None,
            due_date=request.due_date,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(action_item)
        db.commit()
        db.refresh(action_item)
        
        return {
            "id": action_item.id,
            "title": action_item.title,
            "status": action_item.status,
            "message": "Action item created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create action item: {str(e)}")

@router.get("/{suggestion_id}/action-items")
def get_suggestion_action_items(
    suggestion_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all action items for a suggestion"""
    
    try:
        suggestion_uuid = UUID(suggestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid suggestion ID")
    
    action_items = db.query(SuggestionActionItem).options(
        joinedload(SuggestionActionItem.assignee)
    ).filter(
        SuggestionActionItem.suggestion_id == suggestion_uuid
    ).all()
    
    action_items_data = []
    for action_item in action_items:
        action_items_data.append({
            "id": str(action_item.id),
            "suggestion_id": str(action_item.suggestion_id),
            "title": action_item.title,
            "description": action_item.description,
            "priority": action_item.priority,
            "implementation_type": action_item.implementation_type,
            "status": action_item.status,
            "assigned_to": str(action_item.assigned_to) if action_item.assigned_to else None,
            "assigned_to_name": action_item.assignee.full_name if action_item.assignee else None,
            "due_date": action_item.due_date.isoformat() if action_item.due_date else None,
            "completed_at": action_item.completed_at.isoformat() if action_item.completed_at else None,
            "created_at": action_item.created_at.isoformat(),
            "updated_at": action_item.updated_at.isoformat()
        })
    
    return {
        "suggestion_id": suggestion_id,
        "action_items": action_items_data
    }

@router.get("/stats-enhanced", response_model=EnhancedSuggestionStatsResponse)
def get_enhanced_suggestion_stats(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get enhanced suggestion statistics including action items"""
    
    basic_stats = get_suggestion_stats(ctx, db)
    
    # Count action items
    total_action_items = db.query(SuggestionActionItem).count()
    pending_action_items = db.query(SuggestionActionItem).filter(
        SuggestionActionItem.status == "pending"
    ).count()
    in_progress_action_items = db.query(SuggestionActionItem).filter(
        SuggestionActionItem.status == "in_progress"
    ).count()
    completed_action_items = db.query(SuggestionActionItem).filter(
        SuggestionActionItem.status == "completed"
    ).count()
    
    # Count overdue action items
    now = datetime.utcnow()
    overdue_action_items = db.query(SuggestionActionItem).filter(
        SuggestionActionItem.due_date < now,
        SuggestionActionItem.status.in_(["pending", "in_progress"])
    ).count()
    
    # Count suggestions with action items
    suggestions_with_action_items = db.query(IntentSuggestion).join(
        SuggestionActionItem
    ).distinct().count()
    
    return EnhancedSuggestionStatsResponse(
        total_suggestions=basic_stats.total_suggestions,
        pending=basic_stats.pending,
        approved=basic_stats.approved,
        rejected=basic_stats.rejected,
        implemented=basic_stats.implemented,
        needs_analysis=basic_stats.needs_analysis,
        by_type=basic_stats.by_type,
        by_priority=basic_stats.by_priority,
        action_items={
            "total": total_action_items,
            "pending": pending_action_items,
            "in_progress": in_progress_action_items,
            "completed": completed_action_items,
            "overdue": overdue_action_items
        },
        suggestions_with_action_items=suggestions_with_action_items,
        avg_time_to_resolution=None
    )

# Helper functions
def _implement_suggestion(db: Session, suggestion: IntentSuggestion) -> dict:
    """Helper function to implement a suggestion"""
    
    candidate_version = db.query(IntentConfigVersion)\
        .filter(IntentConfigVersion.status == ConfigStatus.CANDIDATE)\
        .first()
    
    if not candidate_version:
        active_version = db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.status == ConfigStatus.ACTIVE)\
            .first()
        
        candidate_version = IntentConfigVersion(
            id=str(uuid.uuid4()),
            name=f"Auto-generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            status=ConfigStatus.CANDIDATE,
            notes=f"Created automatically from suggestion {suggestion.id}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(candidate_version)
        db.flush()
        
        if active_version:
            _copy_version_content(db, active_version.id, candidate_version.id)
    
    result = {"candidate_version_id": candidate_version.id}
    
    if suggestion.suggestion_type == SuggestionType.REGEX_PATTERN:
        if not suggestion.pattern:
            raise ValueError("Pattern required for regex pattern suggestion")
        
        import re
        try:
            re.compile
            re.compile(suggestion.pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {str(e)}")
        
        pattern = IntentPattern(
            id=str(uuid.uuid4()),
            version_id=candidate_version.id,
            handler=suggestion.handler,
            intent=suggestion.intent,
            kind=PatternKind.POSITIVE,
            pattern=suggestion.pattern,
            priority=_priority_to_number(suggestion.priority),
            enabled=True,
            scope_school_id=str(suggestion.school_id) if suggestion.school_id else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(pattern)
        
        result["created_pattern_id"] = pattern.id
    
    elif suggestion.suggestion_type == SuggestionType.PROMPT_TEMPLATE:
        if not suggestion.template_text:
            raise ValueError("Template text required for prompt template suggestion")
        
        template = PromptTemplate(
            id=str(uuid.uuid4()),
            version_id=candidate_version.id,
            handler=suggestion.handler,
            intent=suggestion.intent,
            template_type=TemplateType.USER,
            template_text=suggestion.template_text,
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(template)
        
        result["created_template_id"] = template.id
    
    suggestion.status = SuggestionStatus.IMPLEMENTED
    suggestion.implemented_at = datetime.utcnow()
    suggestion.updated_at = datetime.utcnow()
    
    candidate_version.updated_at = datetime.utcnow()
    
    result["message"] = f"Suggestion implemented successfully in candidate version"
    return result

def _copy_version_content(db: Session, source_version_id: str, target_version_id: str):
    """Copy patterns and templates from source to target version"""
    
    source_patterns = db.query(IntentPattern)\
        .filter(IntentPattern.version_id == source_version_id)\
        .all()
    
    for pattern in source_patterns:
        new_pattern = IntentPattern(
            id=str(uuid.uuid4()),
            version_id=target_version_id,
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
    
    source_templates = db.query(PromptTemplate)\
        .filter(PromptTemplate.version_id == source_version_id)\
        .all()
    
    for template in source_templates:
        new_template = PromptTemplate(
            id=str(uuid.uuid4()),
            version_id=target_version_id,
            handler=template.handler,
            intent=template.intent,
            template_type=template.template_type,
            template_text=template.template_text,
            enabled=template.enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_template)

def _get_user_message_before(db: Session, chat_message: ChatMessage) -> Optional[str]:
    """Get the user message that preceded this assistant message"""
    if not chat_message:
        return None
        
    try:
        user_message = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == chat_message.conversation_id,
            ChatMessage.message_type == MessageType.USER,
            ChatMessage.created_at < chat_message.created_at
        ).order_by(desc(ChatMessage.created_at)).first()
        
        return user_message.content if user_message else None
        
    except Exception as e:
        print(f"Error getting user message before: {e}")
        return None

def _priority_to_number(priority: str) -> int:
    """Convert priority string to number for sorting"""
    priority_map = {
        "critical": 10,
        "high": 20,
        "medium": 50,
        "low": 100
    }
    return priority_map.get(priority.lower(), 50)