# app/api/routers/chat/deps.py
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.db import get_db, set_rls_context

def verify_auth_and_get_context(
    authorization: str = Header(...),
    x_school_id: str = Header(..., alias="X-School-ID"),
    db: Session = Depends(get_db)
):
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")

        token = authorization.split(" ")[1]
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        membership = db.execute(
            text("""
                SELECT sm.user_id, sm.school_id, sm.role, u.full_name
                FROM schoolmember sm
                JOIN users u ON sm.user_id = u.id
                WHERE sm.user_id = :user_id AND sm.school_id = :school_id
            """),
            {"user_id": user_id, "school_id": x_school_id}
        ).first()

        if not membership:
            raise HTTPException(status_code=403, detail="Access denied to this school")

        set_rls_context(db, user_id=user_id, school_id=x_school_id)

        return {
            "user_id": user_id,
            "school_id": x_school_id,
            "role": membership.role,
            "full_name": membership.full_name
        }
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")