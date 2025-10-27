# app/api/deps/auth.py - Enhanced with role-based authorization
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User
from uuid import UUID
from typing import Dict, Any, List

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Decode JWT and return user + claims.
    Returns: {"user": User, "claims": dict}
    """
    token = credentials.credentials
    try:
        claims = decode_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user_id from claims (it's stored as string)
    user_id_str = claims.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID"
        )
    
    # Convert string to UUID for database query
    try:
        user_uuid = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
    
    # Fetch user from database
    user = db.execute(
        select(User).where(User.id == user_uuid)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated"
        )
    
    return {
        "user": user,
        "claims": claims
    }

def require_roles(required_roles: List[str]):
    """
    Create a dependency that requires specific roles.
    Usage: @router.get("/admin", dependencies=[Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))])
    """
    def role_checker(ctx = Depends(get_current_user)):
        user = ctx["user"]
        if not user.has_any_role(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {required_roles}"
            )
        return ctx
    return role_checker

def require_admin(ctx = Depends(get_current_user)):
    """Require admin or super admin role"""
    user = ctx["user"]
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return ctx

def require_super_admin(ctx = Depends(get_current_user)):
    """Require super admin role only"""
    user = ctx["user"]
    if not user.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return ctx

def require_tester(ctx = Depends(get_current_user)):
    """Require tester, admin, or super admin role"""
    user = ctx["user"]
    if not user.is_tester():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tester access required"
        )
    return ctx

def require_teacher(ctx = Depends(get_current_user)):
    """Require teacher role or higher"""
    user = ctx["user"]
    if not user.has_any_role(["TEACHER", "ADMIN", "SUPER_ADMIN"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    return ctx

def require_accountant(ctx = Depends(get_current_user)):
    """Require accountant role or higher"""
    user = ctx["user"]
    if not user.has_any_role(["ACCOUNTANT", "ADMIN", "SUPER_ADMIN"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accountant access required"
        )
    return ctx

# Alias for backward compatibility
verify_auth_and_get_context = get_current_user