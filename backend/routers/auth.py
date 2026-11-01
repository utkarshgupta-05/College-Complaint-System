"""
backend/routers/auth.py
-----------------------
Authentication endpoints for user registration, login, and profile retrieval.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: UserRegisterRequest, db: Annotated[Session, Depends(get_db)]):
    """Register a new student, staff, or admin user."""
    # Check if username or email already exists
    existing = db.query(User).filter(
        (User.username == req.username) | (User.email == req.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered.",
        )

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name or req.username,
        role=req.role,
        department=req.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user registered: %s (role: %s)", user.username, user.role)
    return user


@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest, db: Annotated[Session, Depends(get_db)]):
    """Authenticate with username and password, returning an access token."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id, user.username, user.role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Return the profile of the currently authenticated user."""
    return current_user

