from pydantic import BaseModel

class NotificationCreate(BaseModel):
    type: str  # IN_APP or EMAIL
    subject: str | None = None
    body: str
    to_guardian_id: str | None = None
    to_user_id: str | None = None

class NotificationOut(BaseModel):
    id: str
    type: str
    subject: str | None
    body: str
    to_guardian_id: str | None
    to_user_id: str | None
    status: str