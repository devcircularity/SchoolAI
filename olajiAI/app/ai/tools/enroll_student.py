from app.ai.tools.base import ToolContext, ToolResult
import datetime

async def resolve_class_id(ctx: ToolContext, class_name: str) -> str | None:
    """Find class ID by searching through all classes for a matching name"""
    r = await ctx.http.get("/classes", ctx.bearer, ctx.school_id)
    if r.status_code != 200:
        return None
    
    classes = r.json() or []
    # Look for exact match first, then partial match
    for cls in classes:
        if cls.get("name", "").lower() == class_name.lower():
            return cls.get("id")
    
    # Try partial match if exact match not found
    for cls in classes:
        if class_name.lower() in cls.get("name", "").lower():
            return cls.get("id")
    
    return None

async def run(ctx: ToolContext, payload: dict) -> ToolResult:
    # Debug logging
    print(f"🔍 DEBUG enroll_student payload: {payload}")
    
    # Resolve class_id if only class_name is provided
    class_id = payload.get("class_id")
    if not class_id and payload.get("class_name"):
        class_id = await resolve_class_id(ctx, payload["class_name"])
        if not class_id:
            return {"status": 400, "body": {"detail": f"Class '{payload['class_name']}' not found"}}

    # Generate admission number if not provided
    admission_no = payload.get("admission_no")
    if not admission_no:
        # Simple auto-generation: use first 3 letters of name + current year + random
        first_name = payload.get("first_name", "Unknown")
        year = str(datetime.date.today().year)
        admission_no = f"{first_name[:3].upper()}{year}{ctx.message_id[-4:]}"

    # Create student payload
    student_payload = {
        "admission_no": admission_no,
        "first_name": payload.get("first_name", "A"),  # Debug: show why it's "A Student"
        "last_name": payload.get("last_name", "Student"),  # Debug: show why it's "A Student"
        "gender": payload.get("gender"),
        "class_id": class_id,
    }
    
    print(f"🔍 DEBUG student_payload being sent to API: {student_payload}")
    
    # Add optional fields if provided
    if payload.get("dob"):
        student_payload["dob"] = payload["dob"]

    # Create student
    r1 = await ctx.http.post("/students", ctx.bearer, ctx.school_id, student_payload, ctx.message_id)
    if r1.status_code not in (200, 201):
        return {"status": r1.status_code, "body": r1.json() if r1.content else None}

    student = r1.json()
    return {"status": r1.status_code, "body": student}