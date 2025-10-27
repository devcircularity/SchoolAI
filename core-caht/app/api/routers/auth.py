# app/api/routers/auth.py - Complete auth router with password reset
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_token
from app.schemas.auth import (
    RegisterIn, LoginIn, LoginOut, SwitchSchoolIn, TokenOut,
    ForgotPasswordIn, ForgotPasswordOut, 
    VerifyResetTokenIn, VerifyResetTokenOut,
    ResetPasswordIn, ResetPasswordOut
)
from app.models.user import User, UserRole
from app.models.school import SchoolMember
from app.models.password_reset import PasswordResetToken
from app.api.deps.auth import get_current_user
from uuid import UUID
from datetime import datetime, timedelta
import secrets
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    """Register a new user account"""
    # Check if email already exists
    existing_user = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength
    if len(data.password) < 6:
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 6 characters long"
        )
    
    # Create new user with default PARENT role
    user = User(
        email=data.email, 
        full_name=data.full_name, 
        password_hash=hash_password(data.password),
        is_active=True,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user.set_roles(["ADMIN"])  # Default role for new registrations
    
    db.add(user)
    db.flush()
    
    logger.info(f"New user registered: {user.email} (ID: {user.id})")
    
    # Create token with string conversion of UUID
    token = create_token(
        sub=str(user.id),  # Convert UUID to string
        roles=user.roles, 
        active_school_id=None, 
        minutes=60,
        full_name=user.full_name, 
        email=user.email
    )
    db.commit()
    return TokenOut(access_token=token)

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    # Find user
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {payload.email} from IP: {get_client_ip(request)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for deactivated account: {payload.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account deactivated")

    logger.info(f"User login: {user.email} (ID: {user.id})")

    # Update last login
    user.last_login = datetime.utcnow()
    
    # Get roles from user model
    roles = user.roles

    # Get memberships and decide active_school_id
    memberships = db.execute(
        select(SchoolMember.school_id, SchoolMember.role).where(SchoolMember.user_id == user.id)
    ).all()
    
    if len(memberships) == 1:
        active_school_id = str(memberships[0][0])  # Convert UUID to string
    elif len(memberships) > 1:
        # For multiple memberships, pick the first one
        active_school_id = str(memberships[0][0])  # Convert UUID to string
    else:
        active_school_id = None

    # Issue token with string UUID
    token = create_token(
        sub=str(user.id),  # Convert UUID to string
        roles=roles, 
        active_school_id=active_school_id, 
        minutes=60,
        full_name=user.full_name, 
        email=user.email
    )

    # Commit the last_login update
    db.commit()

    return LoginOut(access_token=token, school_id=active_school_id)

@router.post("/switch-school", response_model=LoginOut)
def switch_school(
    payload: SwitchSchoolIn,
    ctx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Switch active school context"""
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

    roles = user.roles  # Get roles from user model
    token = create_token(
        sub=str(user.id),  # Convert UUID to string
        roles=roles, 
        active_school_id=payload.school_id,  # Keep as string
        minutes=60,
        full_name=user.full_name, 
        email=user.email
    )
    return LoginOut(access_token=token, school_id=payload.school_id)

@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(data: ForgotPasswordIn, request: Request, db: Session = Depends(get_db)):
    """Request password reset email"""
    client_ip = get_client_ip(request)
    
    # Find user by email
    user = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none()
    
    # Always return success for security (don't reveal if email exists)
    success_message = "If an account with this email exists, you will receive password reset instructions."
    
    if not user:
        logger.info(f"Password reset requested for non-existent email: {data.email} from IP: {client_ip}")
        return ForgotPasswordOut(message=success_message)
    
    # Check if user is active
    if not user.is_active:
        logger.info(f"Password reset requested for inactive account: {data.email} from IP: {client_ip}")
        return ForgotPasswordOut(message=success_message)
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    current_time = datetime.utcnow()
    expires_at = current_time + timedelta(hours=1)  # Token expires in 1 hour
    
    # Clean up any existing unused tokens for this user (older than 5 minutes)
    cleanup_time = datetime.utcnow() - timedelta(minutes=5)
    db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
            PasswordResetToken.created_at < cleanup_time
        )
    )
    
    # Create new reset token with explicit created_at to ensure constraint works
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        created_at=current_time,  # Set explicitly to match expires_at calculation
        created_ip=client_ip
    )
    db.add(reset_token)
    db.commit()
    
    logger.info(f"Password reset token created for user: {user.email} (expires: {expires_at})")
    
    # Send email
    try:
        send_password_reset_email(user.email, user.full_name, token)
        logger.info(f"Password reset email sent to: {user.email}")
    except Exception as e:
        logger.error(f"Failed to send reset email to {user.email}: {str(e)}")
        # Don't fail the request if email fails - token is still created
    
    return ForgotPasswordOut(message=success_message)

@router.post("/verify-reset-token", response_model=VerifyResetTokenOut)
def verify_reset_token(data: VerifyResetTokenIn, request: Request, db: Session = Depends(get_db)):
    """Verify if a password reset token is valid"""
    client_ip = get_client_ip(request)
    
    # Find the token
    reset_token = db.execute(
        select(PasswordResetToken)
        .join(User)
        .where(
            PasswordResetToken.token == data.token,
            User.email == data.email,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        )
    ).scalar_one_or_none()
    
    if not reset_token:
        logger.warning(f"Invalid token verification attempt from IP: {client_ip} for email: {data.email}")
        return VerifyResetTokenOut(
            valid=False,
            message="Invalid or expired reset token"
        )
    
    logger.info(f"Valid token verification for user: {reset_token.user.email}")
    return VerifyResetTokenOut(
        valid=True,
        message="Reset token is valid"
    )

@router.post("/reset-password", response_model=ResetPasswordOut)
def reset_password(data: ResetPasswordIn, request: Request, db: Session = Depends(get_db)):
    """Reset user password using valid token"""
    client_ip = get_client_ip(request)
    
    # Find the token and user
    reset_token = db.execute(
        select(PasswordResetToken)
        .join(User)
        .where(
            PasswordResetToken.token == data.token,
            User.email == data.email,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        )
    ).scalar_one_or_none()
    
    if not reset_token:
        logger.warning(f"Invalid password reset attempt from IP: {client_ip} for email: {data.email}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid or expired reset token"
        )
    
    # Get the user
    user = reset_token.user
    
    if not user.is_active:
        logger.warning(f"Password reset attempt for inactive account: {user.email}")
        raise HTTPException(
            status_code=400,
            detail="Account is deactivated"
        )
    
    # Validate password strength
    if len(data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long"
        )
    
    # Update user password
    user.password_hash = hash_password(data.password)
    user.updated_at = datetime.utcnow()
    
    # Mark token as used
    reset_token.mark_used(client_ip)
    
    # Invalidate all other tokens for this user
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        )
        .values(used=True, used_at=datetime.utcnow())
    )
    
    db.commit()
    
    logger.info(f"Password successfully reset for user: {user.email}")
    
    return ResetPasswordOut(
        message="Password has been successfully reset"
    )

@router.get("/me")
def get_current_user_info(ctx = Depends(get_current_user)):
    """Get current user information including roles"""
    user = ctx["user"]
    claims = ctx["claims"]
    
    return {
        "user_id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "active_school_id": claims.get("active_school_id"),
        "last_login": user.last_login,
        "permissions": {
            "can_manage_users": user.can_manage_users(),
            "is_admin": user.is_admin(),
            "is_super_admin": user.is_super_admin(),
            "is_tester": user.is_tester()
        }
    }

@router.get("/permissions")
def get_user_permissions(ctx = Depends(get_current_user)):
    """Get detailed user permissions for frontend use"""
    user = ctx["user"]
    
    permissions = {
        # Basic permissions
        "can_chat": True,  # All users can chat
        "can_view_conversations": True,  # All users can view their conversations
        
        # Management permissions
        "can_manage_students": user.has_any_role(["TEACHER", "ADMIN", "SUPER_ADMIN"]),
        "can_manage_classes": user.has_any_role(["TEACHER", "ADMIN", "SUPER_ADMIN"]),
        "can_manage_fees": user.has_any_role(["ACCOUNTANT", "ADMIN", "SUPER_ADMIN"]),
        "can_manage_payments": user.has_any_role(["ACCOUNTANT", "ADMIN", "SUPER_ADMIN"]),
        "can_manage_school": user.has_any_role(["ADMIN", "SUPER_ADMIN"]),
        
        # Admin permissions
        "can_manage_users": user.can_manage_users(),
        "can_view_logs": user.is_admin(),
        "can_manage_intent_config": user.is_admin(),
        
        # Tester permissions
        "can_access_tester_queue": user.is_tester(),
        "can_submit_suggestions": user.is_tester(),
        
        # Super admin permissions
        "can_manage_all_schools": user.is_super_admin(),
        "can_promote_admins": user.is_super_admin(),
        "can_access_system_settings": user.is_super_admin(),
        
        # Role information
        "roles": user.roles,
        "primary_role": user.roles[0] if user.roles else "PARENT"
    }
    
    return permissions

def send_password_reset_email(email: str, full_name: str, token: str):
    """Send password reset email using Brevo SMTP service"""
    
    # Get frontend URL from environment or use default
    frontend_url = os.getenv("FRONTEND_URL", "https://olaji.co")
    
    # Brevo SMTP configuration (matching your existing setup)
    smtp_server = "smtp-relay.brevo.com"
    smtp_port = 587
    smtp_user = "844a62001@smtp-brevo.com"
    smtp_password = "Brpd1SAyVsPMRJhW"
    from_email = "no.reply@olaji.co"
    
    if not smtp_user or not smtp_password:
        # For development/testing - just log the reset URL
        reset_url = f"{frontend_url}/reset-password?token={token}&email={email}"
        logger.info(f"Password reset URL for {email}: {reset_url}")
        return
    
    reset_url = f"{frontend_url}/reset-password?token={token}&email={email}"
    subject = "Reset your school account password"
    
    # Professional HTML email template matching your school management theme
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
        <style>
            body {{ 
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                line-height: 1.6; 
                color: #333333; 
                margin: 0; 
                padding: 0; 
                background-color: #f5f5f5; 
            }}
            .container {{ 
                max-width: 600px; 
                margin: 0 auto; 
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                margin-top: 20px;
                margin-bottom: 20px;
            }}
            .header {{ 
                background: linear-gradient(135deg, #1f7daf 0%, #3caedb 100%); 
                color: white; 
                padding: 40px 30px; 
                text-align: center; 
            }}
            .header h1 {{ 
                margin: 0; 
                font-size: 24px; 
                font-weight: 600; 
            }}
            .content {{ 
                padding: 40px 30px; 
            }}
            .content p {{ 
                margin: 0 0 16px 0; 
                color: #555555; 
            }}
            .button {{ 
                display: inline-block; 
                background: #1f7daf; 
                color: white !important; 
                padding: 16px 32px; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: 600; 
                margin: 24px 0; 
                transition: background-color 0.2s;
            }}
            .button:hover {{
                background: #104f73 !important;
            }}
            .button-container {{ 
                text-align: center; 
                margin: 32px 0; 
            }}
            .url-box {{ 
                word-break: break-all; 
                background: #f8f9fa; 
                border: 1px solid #e9ecef;
                padding: 16px; 
                border-radius: 6px; 
                font-family: monospace;
                font-size: 14px;
                margin: 16px 0;
            }}
            .footer {{ 
                background-color: #f8f9fa;
                text-align: center; 
                padding: 24px 30px; 
                color: #6c757d; 
                font-size: 14px; 
                border-top: 1px solid #e9ecef;
            }}
            .security-notice {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 6px;
                padding: 16px;
                margin: 24px 0;
                color: #856404;
            }}
            .security-notice strong {{
                color: #533f03;
            }}
            .brand {{
                color: #1f7daf;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏫 Reset Your Password</h1>
            </div>
            <div class="content">
                <p>Hi {full_name},</p>
                <p>You requested to reset your password for your <span class="brand">School Management</span> account. Click the button below to create a new password:</p>
                
                <div class="button-container">
                    <a href="{reset_url}" class="button">Reset My Password</a>
                </div>
                
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <div class="url-box">{reset_url}</div>
                
                <div class="security-notice">
                    <strong>⏰ Important:</strong> This link will expire in 1 hour for security reasons. If you didn't request this password reset, please ignore this email or contact our support team.
                </div>
                
                <p>If you're having trouble accessing your account, please don't hesitate to contact our support team.</p>
                
                <p>Best regards,<br><span class="brand">Your School Management Team</span></p>
            </div>
            <div class="footer">
                <p>This is an automated email, please do not reply directly to this message.</p>
                <p>If you need help, please contact our support team at support@olaji.co</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Text version for email clients that don't support HTML
    text_content = f"""
    Hi {full_name},

    You requested to reset your password for your School Management account.

    Please visit the following link to set a new password:
    {reset_url}

    IMPORTANT: This link will expire in 1 hour for security reasons.

    If you didn't request this password reset, please ignore this email or contact our support team.

    If you're having trouble accessing your account, please reach out to our support team.

    Best regards,
    Your School Management Team

    ---
    This is an automated email, please do not reply directly to this message.
    Support: support@olaji.co
    """
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = email
        
        # Attach both text and HTML versions
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email using Brevo SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        logger.info(f"Password reset email sent successfully to {email} via Brevo")
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email} via Brevo: {str(e)}")
        raise Exception(f"Email delivery failed: {str(e)}")