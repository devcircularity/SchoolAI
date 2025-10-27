# app/schemas/auth.py - Complete auth schemas with password reset
from pydantic import BaseModel, EmailStr

# Existing authentication schemas
class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    school_id: str | None = None

class SwitchSchoolIn(BaseModel):
    school_id: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Password reset schemas
class ForgotPasswordIn(BaseModel):
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class ForgotPasswordOut(BaseModel):
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "If an account with this email exists, you will receive password reset instructions."
            }
        }

class VerifyResetTokenIn(BaseModel):
    token: str
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456",
                "email": "user@example.com"
            }
        }

class VerifyResetTokenOut(BaseModel):
    valid: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "message": "Reset token is valid"
            }
        }

class ResetPasswordIn(BaseModel):
    token: str
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456",
                "email": "user@example.com",
                "password": "newSecurePassword123"
            }
        }

class ResetPasswordOut(BaseModel):
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Password has been successfully reset"
            }
        }