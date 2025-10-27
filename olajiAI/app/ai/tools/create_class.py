from app.ai.tools.base import ToolContext, ToolResult

async def run(ctx: ToolContext, payload: dict) -> ToolResult:
    # Use POST /classes to create a new class (not /api/v1/classes)
    resp = await ctx.http.post("/classes", ctx.bearer, ctx.school_id, payload, ctx.message_id)
    return {"status": resp.status_code, "body": resp.json() if resp.content else None}