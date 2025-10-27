# app/api/routes/schools.py - Add auto-active school functionality
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text

from app.api.deps.auth import get_current_user
from app.api.deps.tenancy import require_school
from app.core.db import get_db, set_rls_context
from app.models.school import School, SchoolMember
from app.models.student import Student
from app.models.class_model import Class
from app.models.payment import Payment, Invoice
from app.schemas.school import SchoolCreate, SchoolOut, SchoolLite, SchoolOverview, SchoolMineItem
from app.services.helpers.bootstrap_school import bootstrap_school

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.post("", response_model=SchoolOut)
def create_school(
    data: SchoolCreate,
    response: Response,  # Add Response to set headers
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = ctx["user"]
    print(f"🔍 Creating school for user: {user.id}")

    # Basic uniqueness checks (optional, keep simple)
    if data.short_code:
        exists_sc = db.execute(
            select(School.id).where(School.short_code == data.short_code)
        ).first()
        if exists_sc:
            raise HTTPException(status_code=400, detail="short_code already in use")

    try:
        # Create the school
        s = School(
            name=data.name,
            address=data.address,
            contact=data.contact,
            created_by=user.id,
            short_code=data.short_code,
            email=data.email,
            phone=data.phone,
            currency=data.currency or "KES",
            academic_year_start=data.academic_year_start,
        )
        db.add(s)
        db.flush()  # Get the school ID
        print(f"🔍 School created with ID: {s.id}")

        # Add the creator as school owner
        db.add(SchoolMember(school_id=s.id, user_id=user.id, role="OWNER"))
        db.flush()  # Ensure membership is created
        print(f"🔍 School membership created for user: {user.id}")

        # Set RLS context BEFORE bootstrapping
        set_rls_context(db, user_id=str(user.id), school_id=str(s.id))
        print(f"🔍 RLS context set - user_id: {user.id}, school_id: {s.id}")

        # Bootstrap the school with academic data
        print(f"🔍 Starting bootstrap for school: {s.id}")
        bootstrap_school(db=db, school_id=str(s.id), created_by=str(user.id))
        print(f"🔍 Bootstrap completed for school: {s.id}")

        # Commit all changes
        db.commit()
        print(f"🔍 Transaction committed for school: {s.id}")

        # 🆕 AUTOMATICALLY SET AS ACTIVE SCHOOL
        # Set a custom header in the response to tell the frontend to use this school
        response.headers["X-Set-Active-School"] = str(s.id)

        return SchoolOut(id=s.id, name=s.name, address=s.address, contact=s.contact)

    except Exception as e:
        print(f"❌ Error creating school: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create school: {str(e)}")


@router.get("/mine", response_model=list[SchoolMineItem])
def my_schools(
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = ctx["user"]
    rows = db.execute(
        select(School.id, School.name, SchoolMember.role)
        .join(SchoolMember, SchoolMember.school_id == School.id)
        .where(SchoolMember.user_id == user.id)
        .order_by(School.name.asc())
    ).all()
    return [SchoolMineItem(id=r[0], name=r[1], role=r[2]) for r in rows]


@router.get("/active", response_model=SchoolLite)
def get_active_school(
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the user's active school. If they only have one school, return that.
    If they have multiple schools, they need to set an active one via X-School-ID header.
    """
    user = ctx["user"]
    
    # Get all schools the user belongs to
    schools = db.execute(
        select(School.id, School.name, SchoolMember.role)
        .join(SchoolMember, SchoolMember.school_id == School.id)
        .where(SchoolMember.user_id == user.id)
        .order_by(School.name.asc())
    ).all()
    
    if not schools:
        raise HTTPException(status_code=404, detail="No schools found for user")
    
    # If user has only one school, automatically return it
    if len(schools) == 1:
        school_id, school_name, role = schools[0]
        return SchoolLite(id=school_id, name=school_name)
    
    # If user has multiple schools, they need to specify which one is active
    raise HTTPException(
        status_code=400, 
        detail="Multiple schools found. Please set X-School-ID header to specify active school."
    )


@router.get("/overview", response_model=SchoolOverview)
def overview(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    # Convert school_id string to UUID for queries
    from uuid import UUID
    school_uuid = UUID(school_id)
    
    # counts
    total_students = db.execute(
        select(func.count()).select_from(Student).where(Student.school_id == school_uuid)
    ).scalar_one()
    total_classes = db.execute(
        select(func.count()).select_from(Class).where(Class.school_id == school_uuid)
    ).scalar_one()

    # fees collected (sum of payments)
    fees_collected = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.school_id == school_uuid)
    ).scalar_one()
    fees_collected_int = int(fees_collected)  # as per spec (int)

    # pending invoices count (ISSUED or PARTIAL)
    pending_invoices = db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.school_id == school_uuid,
            Invoice.status.in_(["ISSUED", "PARTIAL"])
        )
    ).scalar_one()

    return SchoolOverview(
        students=int(total_students),
        classes=int(total_classes),
        feesCollected=fees_collected_int,
        pendingInvoices=int(pending_invoices),
    )


# [Rest of the endpoints remain the same...]
# --- Membership: canonical verifier for other services (e.g., chat app) ---

PRIVILEGED_ROLES = {"OWNER", "ADMIN"}

def _ensure_caller_authorized_for_membership_check(
    *,
    caller_user_id: str,
    target_user_id: str,
    school_id: str,
    db: Session,
) -> None:
    """
    Allow the call if:
      - the caller is checking their own membership (caller_user_id == target_user_id), OR
      - the caller has a privileged role in the school (OWNER/ADMIN by default).
    """
    if caller_user_id == target_user_id:
        return

    from uuid import UUID
    school_uuid = UUID(school_id)
    caller_uuid = UUID(caller_user_id)

    role_row = db.execute(
        select(SchoolMember.role)
        .where(SchoolMember.school_id == school_uuid, SchoolMember.user_id == caller_uuid)
    ).first()

    if not role_row or (role_row[0] or "").upper() not in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.get("/{school_id}/members/{user_id}")
def is_member(
    school_id: str,
    user_id: str,
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns 200 if user_id is a member of school_id, else 404.
    Safe for cross-service checks (e.g., chat app).
    """
    caller = ctx["user"]

    # 🔐 Ensure the caller is authorized to ask
    _ensure_caller_authorized_for_membership_check(
        caller_user_id=str(caller.id),
        target_user_id=str(user_id),
        school_id=school_id,
        db=db,
    )

    # ✅ Set RLS context so membership rows are visible
    set_rls_context(db, user_id=str(caller.id), school_id=school_id)

    from uuid import UUID
    school_uuid = UUID(school_id)
    user_uuid = UUID(user_id)

    mem = db.execute(
        select(SchoolMember.role)
        .where(SchoolMember.school_id == school_uuid, SchoolMember.user_id == user_uuid)
    ).first()

    if not mem:
        raise HTTPException(status_code=404, detail="Not Found")

    return {"ok": True, "user_id": user_id, "school_id": school_id, "role": mem[0]}


@router.get("/{school_id}/members")
def is_member_by_query(
    school_id: str,
    user_id: str = Query(..., alias="user_id"),
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Alternate form via query param."""
    caller = ctx["user"]

    _ensure_caller_authorized_for_membership_check(
        caller_user_id=str(caller.id),
        target_user_id=str(user_id),
        school_id=school_id,
        db=db,
    )

    # ✅ Set RLS for this request
    set_rls_context(db, user_id=str(caller.id), school_id=school_id)

    from uuid import UUID
    school_uuid = UUID(school_id)
    user_uuid = UUID(user_id)

    mem = db.execute(
        select(SchoolMember.role)
        .where(SchoolMember.school_id == school_uuid, SchoolMember.user_id == user_uuid)
    ).first()

    if not mem:
        raise HTTPException(status_code=404, detail="Not Found")

    return {"ok": True, "user_id": user_id, "school_id": school_id, "role": mem[0]}

@router.get("/cbc-levels")
def list_cbc_levels(
    school_id: str = Depends(require_school),
    db: Session = Depends(get_db),
):
    """
    Return CBC levels for the current school (RLS enforced via X-School-ID).
    """
    # fetch raw levels
    rows = db.execute(
        text("""
            SELECT id, label, group_name
            FROM cbc_level
            WHERE school_id = :sid
            ORDER BY group_name, label
        """),
        {"sid": school_id}
    ).all()

    # optional: class counts per level (if your Class has cbc_level_id)
    from uuid import UUID
    school_uuid = UUID(school_id)
    
    counts = dict(
        db.execute(
            select(Class.level, func.count())  # Assuming Class.level instead of cbc_level_id
            .where(Class.school_id == school_uuid)
            .group_by(Class.level)
        ).all()
    )

    levels: List[Dict[str, Any]] = []
    groups: Dict[str, List[str]] = {}
    for (lvl_id, label, group_name) in rows:
        levels.append({
            "id": lvl_id,
            "label": label,
            "group_name": group_name,
            "class_count": int(counts.get(label, 0)),  # Use label as key
        })
        groups.setdefault(group_name, []).append(label)

    return {"levels": levels, "groups": groups}

@router.get("/{school_id}", response_model=SchoolLite)
def get_school_by_id(
    school_id: str,
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # set RLS to the caller + school being requested
    set_rls_context(db, user_id=str(ctx["user"].id), school_id=school_id)

    from uuid import UUID
    school_uuid = UUID(school_id)

    row = db.execute(
        select(School.id, School.name).where(School.id == school_uuid)
    ).first()
    if not row:
        # If the caller isn't a member or row doesn't exist under RLS, this is 404
        raise HTTPException(status_code=404, detail="School not found")
    return SchoolLite(id=row[0], name=row[1])