"""
Security utilities for MovieRec Version 2.
Argon2id password hashing and JWT token handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Argon2id password context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash plaintext password using Argon2id."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against an Argon2id hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """Generate short-lived signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
