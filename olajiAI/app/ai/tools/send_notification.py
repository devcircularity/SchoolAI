from app.ai.tools.base import ToolContext, ToolResult
async def run(ctx: ToolContext, payload: dict) -> ToolResult:
    r = await ctx.http.post("/api/v1/notifications/send", ctx.bearer, ctx.school_id, payload, ctx.message_id)
    return {"status": r.status_code, "body": r.json() if r.content else None}
