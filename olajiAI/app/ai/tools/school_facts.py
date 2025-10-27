from app.ai.tools.base import ToolContext, ToolResult
from app.core.logging import log

async def run(ctx: ToolContext) -> ToolResult:
    # Debug: Log what we're about to send
    log.info(
        "school_facts_tool_start",
        school_id=ctx.school_id,
        bearer_present=bool(ctx.bearer),
        bearer_preview=ctx.bearer[:20] + "..." if ctx.bearer else "None",
    )
    
    try:
        r = await ctx.http.get("/schools/mine", ctx.bearer, None)
        
        log.info(
            "school_facts_tool_response",
            status_code=r.status_code,
            has_content=bool(r.content),
            content_preview=str(r.content)[:200] if r.content else None,
        )
        
        if r.status_code != 200:
            return {"status": r.status_code, "body": r.json() if r.content else None}
        
        items = r.json() or []
        log.info(
            "school_facts_tool_parsing",
            items_count=len(items),
            looking_for_school_id=ctx.school_id,
            item_ids=[item.get("id") for item in items[:5]],  # First 5 IDs for debugging
        )
        
        current = next((x for x in items if x.get("id") == ctx.school_id), None)
        if not current:
            log.warning(
                "school_facts_tool_no_match",
                school_id=ctx.school_id,
                available_schools=[{"id": item.get("id"), "name": item.get("name")} for item in items],
            )
            return {"status": 404, "body": {"detail": "Current school not in /schools/mine for this user"}}
        
        log.info(
            "school_facts_tool_success",
            school_id=ctx.school_id,
            school_name=current.get("name"),
        )
        
        return {"status": 200, "body": {"school_id": ctx.school_id, "school_name": current.get("name")}}
    
    except Exception as e:
        log.error(
            "school_facts_tool_error",
            error=str(e),
            error_type=type(e).__name__,
            school_id=ctx.school_id,
        )
        raise