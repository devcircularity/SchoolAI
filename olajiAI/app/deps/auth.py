from fastapi import Header, HTTPException
from typing import Optional, Dict, Any
import jwt
from app.core.config import settings

class AuthContext:
    def __init__(self, user_id: str, school_id: Optional[str], raw_bearer: str):
        self.user_id = user_id
        self.school_id = school_id
        self.raw_bearer = raw_bearer

def parse_bearer(auth_header: Optional[str]) -> str:
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Malformed Authorization header")
    return auth_header.split(" ", 1)[1]

def decode_jwt(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_aud": False},
            algorithms=[settings.JWT_ALG],
            leeway=settings.JWT_LEEWAY,
            audience=settings.JWT_AUDIENCE,
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

async def get_auth_ctx(authorization: Optional[str] = Header(None), x_school_id: Optional[str] = Header(None)) -> AuthContext:
    token = parse_bearer(authorization)
    claims = decode_jwt(token)
    user_id = claims.get("sub") or claims.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user sub")
    school_id = claims.get("active_school_id") or x_school_id
    return AuthContext(user_id=user_id, school_id=school_id, raw_bearer=token)
