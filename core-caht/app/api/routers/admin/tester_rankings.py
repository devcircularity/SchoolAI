# app/api/routers/admin/tester_rankings.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.db import get_db
from app.models.intent_suggestion import IntentSuggestion, SuggestionStatus
from app.models.user import User
from app.api.deps.auth import require_admin

router = APIRouter(prefix="/admin/tester-rankings", tags=["Admin - Tester Rankings"])

class TesterRankingResponse(BaseModel):
    user_id: str
    user_name: str
    email: str
    total_suggestions: int
    approved_suggestions: int
    implemented_suggestions: int
    rejected_suggestions: int
    pending_suggestions: int
    approval_rate: float
    implementation_rate: float
    success_score: float  # Custom scoring algorithm
    rank: int
    last_suggestion_date: Optional[datetime]

class TesterRankingsListResponse(BaseModel):
    rankings: List[TesterRankingResponse]
    total_testers: int
    period: str

class TesterDetailedStatsResponse(BaseModel):
    user_id: str
    user_name: str
    email: str
    total_suggestions: int
    by_status: dict
    by_type: dict
    by_priority: dict
    recent_suggestions: List[dict]
    monthly_trend: List[dict]

@router.get("/", response_model=TesterRankingsListResponse)
def get_tester_rankings(
    period: str = Query("all_time", description="all_time, last_30_days, last_90_days"),
    limit: int = Query(20, ge=1, le=100),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get tester rankings based on suggestion activity and success rate"""
    
    # Calculate date filter
    date_filter = None
    if period == "last_30_days":
        date_filter = datetime.utcnow() - timedelta(days=30)
    elif period == "last_90_days":
        date_filter = datetime.utcnow() - timedelta(days=90)
    
    # Build base query
    query = db.query(
        User.id.label('user_id'),
        User.full_name.label('user_name'),
        User.email.label('email'),
        func.count(IntentSuggestion.id).label('total_suggestions'),
        func.sum(case((IntentSuggestion.status == SuggestionStatus.APPROVED, 1), else_=0)).label('approved'),
        func.sum(case((IntentSuggestion.status == SuggestionStatus.IMPLEMENTED, 1), else_=0)).label('implemented'),
        func.sum(case((IntentSuggestion.status == SuggestionStatus.REJECTED, 1), else_=0)).label('rejected'),
        func.sum(case((IntentSuggestion.status == SuggestionStatus.PENDING, 1), else_=0)).label('pending'),
        func.max(IntentSuggestion.created_at).label('last_suggestion_date')
    ).join(
        IntentSuggestion, User.id == IntentSuggestion.created_by
    )
    
    # Apply date filter if specified
    if date_filter:
        query = query.filter(IntentSuggestion.created_at >= date_filter)
    
    # Group by user
    query = query.group_by(User.id, User.full_name, User.email)
    
    # Execute query
    results = query.all()
    
    # Calculate rates and scores
    rankings = []
    for result in results:
        total = result.total_suggestions or 0
        approved = result.approved or 0
        implemented = result.implemented or 0
        
        approval_rate = (approved / total * 100) if total > 0 else 0
        implementation_rate = (implemented / total * 100) if total > 0 else 0
        
        # Success score: weighted formula
        # - 40% implementation rate
        # - 30% approval rate  
        # - 30% total volume (normalized, max 100 suggestions = 100%)
        volume_score = min(total / 100 * 100, 100)
        success_score = (
            implementation_rate * 0.4 +
            approval_rate * 0.3 +
            volume_score * 0.3
        )
        
        rankings.append({
            'user_id': str(result.user_id),
            'user_name': result.user_name,
            'email': result.email,
            'total_suggestions': total,
            'approved_suggestions': approved,
            'implemented_suggestions': implemented,
            'rejected_suggestions': result.rejected or 0,
            'pending_suggestions': result.pending or 0,
            'approval_rate': round(approval_rate, 1),
            'implementation_rate': round(implementation_rate, 1),
            'success_score': round(success_score, 1),
            'last_suggestion_date': result.last_suggestion_date
        })
    
    # Sort by success score
    rankings.sort(key=lambda x: x['success_score'], reverse=True)
    
    # Add rank
    for idx, ranking in enumerate(rankings[:limit], start=1):
        ranking['rank'] = idx
    
    return TesterRankingsListResponse(
        rankings=rankings[:limit],
        total_testers=len(rankings),
        period=period
    )

@router.get("/{user_id}/stats", response_model=TesterDetailedStatsResponse)
def get_tester_detailed_stats(
    user_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific tester"""
    
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Get user
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all suggestions
    suggestions = db.query(IntentSuggestion).filter(
        IntentSuggestion.created_by == user_uuid
    ).all()
    
    # Calculate stats
    total = len(suggestions)
    by_status = {}
    by_type = {}
    by_priority = {}
    
    for suggestion in suggestions:
        # By status
        status_key = suggestion.status.value
        by_status[status_key] = by_status.get(status_key, 0) + 1
        
        # By type
        type_key = suggestion.suggestion_type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1
        
        # By priority
        priority_key = suggestion.priority
        by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
    
    # Recent suggestions
    recent = sorted(suggestions, key=lambda x: x.created_at, reverse=True)[:10]
    recent_suggestions = [
        {
            'id': str(s.id),
            'title': s.title,
            'status': s.status.value,
            'type': s.suggestion_type.value,
            'created_at': s.created_at.isoformat()
        }
        for s in recent
    ]
    
    # Monthly trend (last 6 months)
    monthly_trend = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        month_start = now - timedelta(days=30*i)
        month_end = now - timedelta(days=30*(i-1)) if i > 0 else now
        
        month_suggestions = [
            s for s in suggestions 
            if month_start <= s.created_at < month_end
        ]
        
        monthly_trend.append({
            'month': month_start.strftime('%b %Y'),
            'total': len(month_suggestions),
            'approved': len([s for s in month_suggestions if s.status == SuggestionStatus.APPROVED]),
            'implemented': len([s for s in month_suggestions if s.status == SuggestionStatus.IMPLEMENTED])
        })
    
    return TesterDetailedStatsResponse(
        user_id=str(user.id),
        user_name=user.full_name,
        email=user.email,
        total_suggestions=total,
        by_status=by_status,
        by_type=by_type,
        by_priority=by_priority,
        recent_suggestions=recent_suggestions,
        monthly_trend=monthly_trend
    )