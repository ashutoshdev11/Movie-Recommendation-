"""
Authentication API endpoints for MovieRec Version 2.
Registration, login, logout, and active user profile retrieval.
Sets secure HTTP-only cookies and returns JWT tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.models import User
from app.schemas.all_schemas import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: UserRegister, response: Response, db: Session = Depends(get_db)):
    """Register a new user account with Argon2id password hashing."""
    # Check email conflict
    if db.query(User).filter(User.email == req.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Check username conflict
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken.",
        )

    # Hash password with Argon2id
    hashed = get_password_hash(req.password)

    new_user = User(
        email=req.email.lower(),
        username=req.username,
        hashed_password=hashed,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token
    access_token = create_access_token(subject=new_user.id)

    # Set HTTP-only Cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticate credentials and return JWT access token and HTTP-only cookie."""
    identifier = req.username_or_email.strip().lower()
    
    # Query user by username or email
    user = db.query(User).filter(
        (User.email == identifier) | (User.username.ilike(identifier))
    ).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your username/email and password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated.",
        )

    access_token = create_access_token(subject=user.id)

    # Set HTTP-only Cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
def logout(response: Response):
    """Log out user by deleting the HTTP-only authentication cookie."""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=settings.COOKIE_HTTPONLY,
        samesite=settings.COOKIE_SAMESITE,
    )
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
