# app/api/routers/admin/user_management.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import uuid
from pydantic import BaseModel, EmailStr

from app.core.db import get_db
from app.models.user import User, UserRole
from app.models.school import SchoolMember
from app.core.security import hash_password
from app.api.deps.auth import get_current_user

router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])

# Pydantic schemas
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    roles: List[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    school_count: int = 0

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    limit: int
    has_next: bool

class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    roles: List[str] = ["PARENT"]
    is_active: bool = True

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UpdateUserRolesRequest(BaseModel):
    roles: List[str]

class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    users_by_role: dict
    new_users_this_week: int
    new_users_this_month: int

def require_admin(ctx = Depends(get_current_user)):
    """Require admin role for user management"""
    user = ctx["user"]
    if not user.can_manage_users():
        raise HTTPException(status_code=403, detail="Admin access required")
    return ctx

def require_super_admin(ctx = Depends(get_current_user)):
    """Require super admin role for sensitive operations"""
    user = ctx["user"]
    if not user.is_super_admin():
        raise HTTPException(status_code=403, detail="Super admin access required")
    return ctx

@router.get("/", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by email or name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    active_only: bool = Query(False),
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users with filtering and pagination"""
    
    # Build query
    query = select(User)
    
    # Apply filters
    filters = []
    if search:
        search_term = f"%{search.lower()}%"
        filters.append(
            or_(
                func.lower(User.email).like(search_term),
                func.lower(User.full_name).like(search_term)
            )
        )
    
    if role:
        # Check if role is valid
        if role not in [r.value for r in UserRole]:
            raise HTTPException(status_code=400, detail="Invalid role")
        filters.append(User.roles_csv.like(f"%{role}%"))
    
    if active_only:
        filters.append(User.is_active == True)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    total_query = select(func.count(User.id))
    if filters:
        total_query = total_query.where(and_(*filters))
    total = db.execute(total_query).scalar()
    
    # Apply pagination
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    users = db.execute(query).scalars().all()
    
    # Build response with school counts
    user_responses = []
    for user in users:
        # Count school memberships for each user
        school_count = db.execute(
            select(func.count(SchoolMember.school_id))
            .where(SchoolMember.user_id == user.id)
        ).scalar() or 0
        
        user_responses.append(UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            school_count=school_count
        ))
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        limit=limit,
        has_next=(page * limit) < total
    )

@router.get("/stats", response_model=UserStatsResponse)
def get_user_stats(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    
    # Basic counts
    total_users = db.execute(select(func.count(User.id))).scalar()
    active_users = db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    ).scalar()
    
    # Users by role
    all_users = db.execute(select(User.roles_csv)).scalars().all()
    role_counts = {}
    for role in UserRole:
        role_counts[role.value] = 0
    
    for roles_csv in all_users:
        if roles_csv:
            for role in roles_csv.split(","):
                role = role.strip()
                if role in role_counts:
                    role_counts[role] += 1
    
    # New users this week/month
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    
    new_users_week = db.execute(
        select(func.count(User.id)).where(User.created_at >= one_week_ago)
    ).scalar()
    
    new_users_month = db.execute(
        select(func.count(User.id)).where(User.created_at >= one_month_ago)
    ).scalar()
    
    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        users_by_role=role_counts,
        new_users_this_week=new_users_week,
        new_users_this_month=new_users_month
    )

@router.post("/", response_model=UserResponse)
def create_user(
    request: CreateUserRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    
    # Check if email already exists
    existing_user = db.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate roles
    invalid_roles = [role for role in request.roles if role not in [r.value for r in UserRole]]
    if invalid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid roles: {invalid_roles}")
    
    # Only super admins can create other super admins
    if "SUPER_ADMIN" in request.roles and not ctx["user"].is_super_admin():
        raise HTTPException(status_code=403, detail="Only super admins can create super admin users")
    
    try:
        # Create user
        user = User(
            id=uuid.uuid4(),
            email=request.email,
            full_name=request.full_name,
            password_hash=hash_password(request.password),
            is_active=request.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        user.set_roles(request.roles)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            school_count=0
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get user details"""
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.execute(
        select(User).where(User.id == user_uuid)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get school count
    school_count = db.execute(
        select(func.count(SchoolMember.school_id))
        .where(SchoolMember.user_id == user.id)
    ).scalar() or 0
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        roles=user.roles,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        school_count=school_count
    )

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    request: UpdateUserRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user details"""
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.execute(
        select(User).where(User.id == user_uuid)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent users from modifying themselves inappropriately
    if str(user.id) == str(ctx["user"].id):
        if request.is_active is False:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        if request.roles and not ctx["user"].is_super_admin():
            if "SUPER_ADMIN" not in ctx["user"].roles and "SUPER_ADMIN" in request.roles:
                raise HTTPException(status_code=403, detail="Cannot grant super admin to yourself")
    
    try:
        # Update fields
        if request.full_name is not None:
            user.full_name = request.full_name
        
        if request.roles is not None:
            # Validate roles
            invalid_roles = [role for role in request.roles if role not in [r.value for r in UserRole]]
            if invalid_roles:
                raise HTTPException(status_code=400, detail=f"Invalid roles: {invalid_roles}")
            
            # Only super admins can grant/revoke super admin
            if "SUPER_ADMIN" in request.roles and not ctx["user"].is_super_admin():
                raise HTTPException(status_code=403, detail="Only super admins can grant super admin role")
            
            user.set_roles(request.roles)
        
        if request.is_active is not None:
            user.is_active = request.is_active
        
        if request.is_verified is not None:
            user.is_verified = request.is_verified
        
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        # Get school count for response
        school_count = db.execute(
            select(func.count(SchoolMember.school_id))
            .where(SchoolMember.user_id == user.id)
        ).scalar() or 0
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            school_count=school_count
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

@router.put("/{user_id}/roles", response_model=UserResponse)
def update_user_roles(
    user_id: str,
    request: UpdateUserRolesRequest,
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user roles specifically"""
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.execute(
        select(User).where(User.id == user_uuid)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate roles
    invalid_roles = [role for role in request.roles if role not in [r.value for r in UserRole]]
    if invalid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid roles: {invalid_roles}")
    
    # Only super admins can grant/revoke super admin
    if "SUPER_ADMIN" in request.roles and not ctx["user"].is_super_admin():
        raise HTTPException(status_code=403, detail="Only super admins can grant super admin role")
    
    # Prevent removing super admin from yourself
    if str(user.id) == str(ctx["user"].id) and ctx["user"].is_super_admin():
        if "SUPER_ADMIN" not in request.roles:
            raise HTTPException(status_code=400, detail="Cannot remove super admin role from yourself")
    
    try:
        user.set_roles(request.roles)
        db.commit()
        db.refresh(user)
        
        # Get school count for response
        school_count = db.execute(
            select(func.count(SchoolMember.school_id))
            .where(SchoolMember.user_id == user.id)
        ).scalar() or 0
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            school_count=school_count
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user roles: {str(e)}")

@router.delete("/{user_id}")
def deactivate_user(
    user_id: str,
    ctx = Depends(require_super_admin),  # Only super admins can deactivate users
    db: Session = Depends(get_db)
):
    """Deactivate a user (soft delete)"""
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = db.execute(
        select(User).where(User.id == user_uuid)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deactivating yourself
    if str(user.id) == str(ctx["user"].id):
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    try:
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": f"User {user.email} has been deactivated"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to deactivate user: {str(e)}")

@router.get("/roles/available")
def get_available_roles(
    ctx = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get list of available user roles"""
    
    roles = []
    for role in UserRole:
        roles.append({
            "value": role.value,
            "label": role.value.replace("_", " ").title(),
            "description": _get_role_description(role.value)
        })
    
    return {"roles": roles}

def _get_role_description(role: str) -> str:
    """Get description for a role"""
    descriptions = {
        "SUPER_ADMIN": "Full system access, can manage all schools and users",
        "ADMIN": "Can manage specific schools and their users",
        "TESTER": "Can review and suggest intent improvements",
        "TEACHER": "Can manage classes and students",
        "ACCOUNTANT": "Can manage fees and payments",
        "PARENT": "Basic user access for parents"
    }
    return descriptions.get(role, "No description available")