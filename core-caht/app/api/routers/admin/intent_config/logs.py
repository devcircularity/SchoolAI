# app/api/routers/admin/intent_config/logs.py
"""Logs and analytics for intent routing"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.db import get_db
from app.api.deps.auth import require_admin
from app.models.intent_config import RoutingLog
from app.models.chat import ChatMessage, MessageType
from .shared import LogResponse, LogStatsResponse

router = APIRouter()

@router.get("/logs", response_model=List[LogResponse])
def get_routing_logs(
    limit: int = Query(50, le=200),
    intent: Optional[str] = Query(None),
    handler: Optional[str] = Query(None),
    fallback_only: bool = Query(False),
    low_confidence: bool = Query(False),
    negative_rating: bool = Query(False),
    unhandled_only: bool = Query(False),
    confidence_threshold: float = Query(0.7, le=1.0, ge=0.0),
    days_back: int = Query(7, le=30),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get routing logs for analysis with enhanced filtering for problematic messages"""
    
    # Build base query with optional join to chat messages for ratings
    query = db.query(RoutingLog, ChatMessage.rating.label('user_rating'))\
        .outerjoin(ChatMessage, and_(
            RoutingLog.message == ChatMessage.content,
            RoutingLog.school_id == ChatMessage.school_id,
            ChatMessage.message_type == MessageType.ASSISTANT
        ))\
        .order_by(RoutingLog.created_at.desc())
    
    # Apply date filter
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    query = query.filter(RoutingLog.created_at >= date_threshold)
    
    # Apply filters
    if intent:
        query = query.filter(RoutingLog.final_intent == intent)
    if handler:
        query = query.filter(RoutingLog.final_handler == handler)
    if fallback_only:
        query = query.filter(RoutingLog.fallback_used == True)
    if low_confidence:
        query = query.filter(
            (RoutingLog.llm_confidence < confidence_threshold) |
            (RoutingLog.llm_confidence.is_(None))
        )
    if negative_rating:
        query = query.filter(ChatMessage.rating == -1)
    if unhandled_only:
        query = query.filter(RoutingLog.final_intent.in_(["unhandled", "unknown", "ollama_fallback"]))
    
    results = query.limit(limit).all()
    
    return [
        LogResponse(
            id=log.id,
            message=log.message,
            llm_intent=log.llm_intent,
            llm_confidence=log.llm_confidence,
            router_intent=log.router_intent,
            router_reason=log.router_reason,
            final_intent=log.final_intent,
            final_handler=log.final_handler,
            fallback_used=log.fallback_used,
            latency_ms=log.latency_ms,
            created_at=log.created_at,
            has_negative_rating=user_rating == -1 if user_rating is not None else None,
            user_rating=user_rating
        ) for log, user_rating in results
    ]

@router.get("/logs/{log_id}", response_model=LogResponse)
def get_routing_log(
    log_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed routing log information"""
    log = db.query(RoutingLog).filter(RoutingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Routing log not found")
    
    # Check for associated chat message rating
    user_rating = None
    chat_msg = db.query(ChatMessage).filter(
        and_(
            ChatMessage.content == log.message,
            ChatMessage.school_id == log.school_id,
            ChatMessage.message_type == MessageType.ASSISTANT
        )
    ).first()
    
    if chat_msg:
        user_rating = chat_msg.rating
    
    return LogResponse(
        id=log.id,
        message=log.message,
        llm_intent=log.llm_intent,
        llm_confidence=log.llm_confidence,
        router_intent=log.router_intent,
        router_reason=log.router_reason,
        final_intent=log.final_intent,
        final_handler=log.final_handler,
        fallback_used=log.fallback_used,
        latency_ms=log.latency_ms,
        created_at=log.created_at,
        has_negative_rating=user_rating == -1 if user_rating is not None else None,
        user_rating=user_rating
    )

@router.get("/logs/stats", response_model=LogStatsResponse)
def get_routing_stats(
    days_back: int = Query(7, le=30),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive routing statistics"""
    
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    
    # Total logs
    total_logs = db.query(RoutingLog)\
        .filter(RoutingLog.created_at >= date_threshold)\
        .count()
    
    # Fallback rate
    fallback_count = db.query(RoutingLog)\
        .filter(
            RoutingLog.created_at >= date_threshold,
            RoutingLog.fallback_used == True
        )\
        .count()
    fallback_rate = (fallback_count / total_logs * 100) if total_logs > 0 else 0
    
    # Average confidence
    avg_confidence_result = db.query(func.avg(RoutingLog.llm_confidence))\
        .filter(
            RoutingLog.created_at >= date_threshold,
            RoutingLog.llm_confidence.isnot(None)
        )\
        .scalar()
    avg_confidence = float(avg_confidence_result) if avg_confidence_result else None
    
    # Negative ratings (need to join with chat messages)
    negative_ratings = db.query(ChatMessage)\
        .filter(
            ChatMessage.created_at >= date_threshold,
            ChatMessage.message_type == MessageType.ASSISTANT,
            ChatMessage.rating == -1
        )\
        .count()
    
    # Low confidence count
    low_confidence_count = db.query(RoutingLog)\
        .filter(
            RoutingLog.created_at >= date_threshold,
            RoutingLog.llm_confidence < 0.6,
            RoutingLog.llm_confidence.isnot(None)
        )\
        .count()
    
    # Unhandled count
    unhandled_count = db.query(RoutingLog)\
        .filter(
            RoutingLog.created_at >= date_threshold,
            RoutingLog.final_intent.in_(["unhandled", "unknown", "ollama_fallback"])
        )\
        .count()
    
    # Top intents
    top_intents_query = db.query(
        RoutingLog.final_intent,
        func.count(RoutingLog.id).label('count')
    )\
        .filter(RoutingLog.created_at >= date_threshold)\
        .group_by(RoutingLog.final_intent)\
        .order_by(func.count(RoutingLog.id).desc())\
        .limit(10)\
        .all()
    
    top_intents = [
        {"intent": intent, "count": count}
        for intent, count in top_intents_query
    ]
    
    # Top handlers
    top_handlers_query = db.query(
        RoutingLog.final_handler,
        func.count(RoutingLog.id).label('count')
    )\
        .filter(RoutingLog.created_at >= date_threshold)\
        .group_by(RoutingLog.final_handler)\
        .order_by(func.count(RoutingLog.id).desc())\
        .limit(10)\
        .all()
    
    top_handlers = [
        {"handler": handler, "count": count}
        for handler, count in top_handlers_query
    ]
    
    return LogStatsResponse(
        total_logs=total_logs,
        fallback_rate=round(fallback_rate, 2),
        avg_confidence=round(avg_confidence, 3) if avg_confidence else None,
        negative_ratings=negative_ratings,
        low_confidence_count=low_confidence_count,
        unhandled_count=unhandled_count,
        top_intents=top_intents,
        top_handlers=top_handlers
    )

@router.get("/logs/export")
def export_routing_logs(
    days_back: int = Query(7, le=30),
    format: str = Query("csv", description="Export format: csv or json"),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export routing logs for analysis"""
    from fastapi.responses import Response
    import csv
    import json
    from io import StringIO
    
    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    
    logs = db.query(RoutingLog)\
        .filter(RoutingLog.created_at >= date_threshold)\
        .order_by(RoutingLog.created_at.desc())\
        .all()
    
    if format.lower() == "csv":
        output = StringIO()
        writer = csv.writer(output)
        
        # CSV headers
        writer.writerow([
            "id", "message", "llm_intent", "llm_confidence", "router_intent", 
            "router_reason", "final_intent", "final_handler", "fallback_used",
            "latency_ms", "created_at"
        ])
        
        # CSV data
        for log in logs:
            writer.writerow([
                log.id, log.message, log.llm_intent, log.llm_confidence,
                log.router_intent, log.router_reason, log.final_intent,
                log.final_handler, log.fallback_used, log.latency_ms,
                log.created_at.isoformat()
            ])
        
        content = output.getvalue()
        output.close()
        
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=routing_logs_{days_back}days.csv"}
        )
    
    elif format.lower() == "json":
        log_data = []
        for log in logs:
            log_data.append({
                "id": log.id,
                "message": log.message,
                "llm_intent": log.llm_intent,
                "llm_confidence": log.llm_confidence,
                "router_intent": log.router_intent,
                "router_reason": log.router_reason,
                "final_intent": log.final_intent,
                "final_handler": log.final_handler,
                "fallback_used": log.fallback_used,
                "latency_ms": log.latency_ms,
                "created_at": log.created_at.isoformat()
            })
        
        content = json.dumps(log_data, indent=2)
        
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=routing_logs_{days_back}days.json"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'json'.")