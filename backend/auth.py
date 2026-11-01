"""
backend/auth.py
---------------
Authentication and Role-Based Access Control (RBAC).
Uses standard library hashlib/secrets for secure password hashing (PBKDF2-SHA256)
and signed HMAC-SHA256 tokens without external C-extension risks.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import User, UserRole

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)


# =========================================================================
# Password Hashing via PBKDF2-HMAC-SHA256
# =========================================================================

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique cryptographic salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored PBKDF2 hash using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        meta, salt, stored_hash = parts
        _, _, iters_str = meta.split(":")
        iters = int(iters_str)

        computed = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=iters,
        )
        return hmac.compare_digest(computed.hex(), stored_hash)
    except Exception as exc:
        logger.warning("Error verifying password: %s", exc)
        return False


# =========================================================================
# Token Generation & Verification
# =========================================================================

def create_access_token(user_id: int, username: str, role: str) -> str:
    """Generate a tamper-proof HMAC-SHA256 signed bearer token."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": int(time.time()) + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    }
    raw_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(raw_json.encode("utf-8")).decode("utf-8")

    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def decode_access_token(token: str) -> dict:
    """Verify and decode HMAC-SHA256 signed token."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("Malformed token format.")
        payload_b64, signature = parts

        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid token signature.")

        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("exp", 0) < time.time():
            raise ValueError("Token has expired.")

        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =========================================================================
# Dependencies
# =========================================================================

def get_current_user(
    auth_header: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Dependency to retrieve authenticated user from Bearer token."""
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth_header.credentials)
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found.",
        )
    return user


def require_role(allowed_roles: list[str]):
    """Factory dependency enforcing RBAC permissions."""
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role in {allowed_roles}, but your role is '{current_user.role}'.",
            )
        return current_user
    return role_checker


require_student = require_role([UserRole.STUDENT.value, UserRole.STAFF.value, UserRole.ADMIN.value])
require_staff = require_role([UserRole.STAFF.value, UserRole.ADMIN.value])
require_admin = require_role([UserRole.ADMIN.value])

