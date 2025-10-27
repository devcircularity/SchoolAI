from pydantic import BaseModel, EmailStr

class GuardianCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr | None = None
    relationship: str | None = None

class GuardianOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone: str
    email: EmailStr | None = None
    relationship: str | None = None