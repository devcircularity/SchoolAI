# app/api/routers/auth.py - Fixed with UUID handling
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_token
from app.schemas.auth import RegisterIn, LoginIn, LoginOut, SwitchSchoolIn, TokenOut
from app.models.user import User
from app.models.school import SchoolMember
from app.api.deps.auth import get_current_user
from sqlalchemy import select
from uuid import UUID

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    u = User(
        email=data.email, 
        full_name=data.full_name, 
        password_hash=hash_password(data.password)
    )
    db.add(u)
    db.flush()
    
    # Create token with string conversion of UUID
    token = create_token(
        sub=str(u.id),  # Convert UUID to string
        roles=u.roles, 
        active_school_id=None, 
        minutes=60,
        full_name=u.full_name, 
        email=u.email
    )
    db.commit()
    return TokenOut(access_token=token)

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    # 1) Find user
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    print(f"🔍 Backend: User ID: {user.id}")

    # 2) Get roles
    roles = (user.roles_csv or "").split(",") if getattr(user, "roles_csv", None) else ["PARENT"]
    print(f"🔍 Backend: User roles: {roles}")

    # 3) Get memberships and decide active_school_id
    memberships = db.execute(
        select(SchoolMember.school_id, SchoolMember.role).where(SchoolMember.user_id == user.id)
    ).all()
    
    print(f"🔍 Backend: Found {len(memberships)} memberships")
    for i, (school_id, role) in enumerate(memberships):
        print(f"🔍 Backend: Membership {i}: school_id={school_id}, role={role}")
    
    if len(memberships) == 1:
        active_school_id = str(memberships[0][0])  # Convert UUID to string
        print(f"🔍 Backend: Single membership - active_school_id: {active_school_id}")
    elif len(memberships) > 1:
        # For multiple memberships, pick the first one
        active_school_id = str(memberships[0][0])  # Convert UUID to string
        print(f"🔍 Backend: Multiple memberships - choosing first: {active_school_id}")
    else:
        active_school_id = None
        print(f"🔍 Backend: No memberships found - active_school_id: None")

    print(f"🔍 Backend: Final active_school_id: {active_school_id}")

    # 4) Issue token with string UUID
    token = create_token(
        sub=str(user.id),  # Convert UUID to string
        roles=roles, 
        active_school_id=active_school_id, 
        minutes=60,
        full_name=user.full_name, 
        email=user.email
    )

    return LoginOut(access_token=token, school_id=active_school_id)


@router.post("/switch-school", response_model=LoginOut)
def switch_school(
    payload: SwitchSchoolIn,
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = ctx["user"]
    
    # Convert string school_id to UUID for database query
    try:
        school_uuid = UUID(payload.school_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid school ID format")
    
    # Verify membership
    is_member = db.execute(
        select(SchoolMember).where(
            SchoolMember.school_id == school_uuid,
            SchoolMember.user_id == user.id
        )
    ).scalar_one_or_none()
    
    if not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this school")

    roles = ctx["claims"].get("roles", ["PARENT"])
    token = create_token(
        sub=str(user.id),  # Convert UUID to string
        roles=roles, 
        active_school_id=payload.school_id,  # Keep as string
        minutes=60,
        full_name=user.full_name, 
        email=user.email
    )
    return LoginOut(access_token=token, school_id=payload.school_id)