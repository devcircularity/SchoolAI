from app.ai.tools.base import ToolContext, ToolResult

async def run(ctx: ToolContext, query_type: str = "count") -> ToolResult:
    """
    Query students for the school
    query_type: "count" to get count, "list" to get all students
    """
    # Use GET /students endpoint to fetch all students
    resp = await ctx.http.get("/students", ctx.bearer, ctx.school_id)
    
    if resp.status_code != 200:
        return {"status": resp.status_code, "body": resp.json() if resp.content else None}
    
    students = resp.json() or []
    
    if query_type == "count":
        return {
            "status": 200, 
            "body": {
                "count": len(students),
                "students": students
            }
        }
    elif query_type == "list":
        return {
            "status": 200,
            "body": {
                "count": len(students),
                "students": students
            }
        }
    else:
        return {
            "status": 200,
            "body": {
                "count": len(students),
                "students": students
            }
        }