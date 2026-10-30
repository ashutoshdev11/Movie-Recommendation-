"""
FastAPI dependency injection utilities for authentication, database sessions, and permissions.
Extracts JWT from HTTP-only cookie or Authorization header.
"""

from typing import Optional
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.db.models import User


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    movierec_access_token: Optional[str] = Cookie(None),
) -> User:
    """
    Authenticate active user from either Authorization header or HTTP-only cookie.
    Guarantees server-side ownership enforcement across all user routes.
    """
    token = None

    # 1. Prefer Authorization Bearer header
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    # 2. Fall back to secure HTTP-only cookie
    elif movierec_access_token:
        token = movierec_access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Access token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str or not user_id_str.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token subject.",
        )

    user_id = int(user_id_str)
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user
