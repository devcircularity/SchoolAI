from fastapi import Depends, HTTPException
from app.deps.auth import get_auth_ctx, AuthContext

async def get_school_id(ctx: AuthContext = Depends(get_auth_ctx)) -> str:
    if not ctx.school_id:
        raise HTTPException(status_code=400, detail="No school selected. Provide X-School-ID header or ensure token has active_school_id.")
    return ctx.school_id
