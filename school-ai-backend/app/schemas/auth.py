# app/schemas/auth.py
from pydantic import BaseModel, EmailStr

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