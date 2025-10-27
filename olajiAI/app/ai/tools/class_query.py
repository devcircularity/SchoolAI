from app.ai.tools.base import ToolContext, ToolResult

async def run(ctx: ToolContext, query_type: str = "count") -> ToolResult:
    """
    Query classes for the school
    query_type: "count" to get count, "list" to get all classes
    """
    # Use GET /classes endpoint to fetch all classes
    resp = await ctx.http.get("/classes", ctx.bearer, ctx.school_id)
    
    if resp.status_code != 200:
        return {"status": resp.status_code, "body": resp.json() if resp.content else None}
    
    classes = resp.json() or []
    
    if query_type == "count":
        return {
            "status": 200, 
            "body": {
                "count": len(classes),
                "classes": classes
            }
        }
    elif query_type == "list":
        return {
            "status": 200,
            "body": {
                "count": len(classes),
                "classes": classes
            }
        }
    else:
        return {
            "status": 200,
            "body": {
                "count": len(classes),
                "classes": classes
            }
        }