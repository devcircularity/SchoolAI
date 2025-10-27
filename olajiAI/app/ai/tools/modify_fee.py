from app.ai.tools.base import ToolContext, ToolResult

async def preview(ctx: ToolContext, term: int, year: int, items: list[dict]) -> ToolResult:
    r = await ctx.http.get(f"/api/v1/fees/structures?term={term}&year={year}", ctx.bearer, ctx.school_id)
    if r.status_code != 200:
        return {"status": r.status_code, "body": r.json() if r.content else None}
    data = r.json()
    if not data:
        return {"status": 404, "body": {"detail": "No fee structure found"}}
    target = data[0] if isinstance(data, list) else data
    diff = {"structure_id": target["id"], "changes": items}
    return {"status": 200, "body": {"target": target, "diff": diff}}

async def apply(ctx: ToolContext, structure_id: str, changes: list[dict]) -> ToolResult:
    r = await ctx.http.patch(f"/api/v1/fees/structures/{structure_id}", ctx.bearer, ctx.school_id, {"items": changes}, ctx.message_id)
    return {"status": r.status_code, "body": r.json() if r.content else None}
