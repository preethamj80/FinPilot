"""Authentication router — register, login, logout, me, csrf-token."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from backend.auth.hashing import hash_password, verify_password
from backend.auth.rate_limiter import is_locked_out, record_attempt, cleanup_old_attempts
from backend.auth.sessions import (
    create_session, destroy_session, destroy_all_user_sessions,
    prune_expired_sessions, get_session, COOKIE_NAME, SESSION_DURATION_DAYS,
)
from backend.auth.user_db import email_exists, create_user, get_user_by_email
from backend.auth.dependencies import get_current_user, AuthenticatedUser
from backend.schemas.auth import RegisterIn, LoginIn, UserOut, AuthResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

_GENERIC_LOGIN_ERROR = "Email or password is incorrect."
_LOCKOUT_ERROR = "Too many failed attempts. Please try again in 15 minutes."

COOKIE_MAX_AGE = SESSION_DURATION_DAYS * 24 * 60 * 60  # seconds


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=os.getenv("FINPILOT_ENV", "development").lower() == "production",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/", httponly=True, samesite="lax")


def _get_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ─── Register ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterIn, request: Request, response: Response):
    """Create a new FinPilot account."""
    # Always return generic message to avoid email enumeration
    if email_exists(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    hashed = hash_password(payload.password)
    user_id = create_user(payload.full_name, payload.email, hashed)

    ip = _get_ip(request)
    ua = request.headers.get("User-Agent")
    session_id, csrf_token = create_session(user_id, ip, ua)
    _set_session_cookie(response, session_id)

    record_attempt(payload.email, ip, success=True)

    return AuthResponse(
        user=UserOut(
            id=user_id,
            full_name=payload.full_name,
            email=payload.email,
            created_at=datetime.now(timezone.utc).isoformat(),
        ),
        csrf_token=csrf_token,
        message="Account created successfully. Welcome to FinPilot!",
    )


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginIn, request: Request, response: Response):
    """Sign in with email and password."""
    ip = _get_ip(request)
    cleanup_old_attempts()

    # Brute-force check (before any DB lookup)
    if is_locked_out(payload.email, ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=_LOCKOUT_ERROR)

    user = get_user_by_email(payload.email)

    # Constant-time comparison even when user not found
    dummy_hash = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    stored_hash = user["password_hash"] if user else dummy_hash
    password_ok = verify_password(payload.password, stored_hash)

    if not user or not password_ok:
        record_attempt(payload.email, ip, success=False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_GENERIC_LOGIN_ERROR)

    record_attempt(payload.email, ip, success=True)
    prune_expired_sessions()

    ua = request.headers.get("User-Agent")
    # Reuse existing session if present (e.g., after registration)
    existing_session_id = request.cookies.get(COOKIE_NAME)
    if existing_session_id:
        sess = get_session(existing_session_id)
        if sess and sess.get("user_id") == user["id"]:
            # Session valid for this user – keep it and its CSRF token
            session_id = existing_session_id
            csrf_token = sess.get("csrf_token")
        else:
            # Invalid or different user – create fresh session
            session_id, csrf_token = create_session(user["id"], ip, ua)
    else:
        session_id, csrf_token = create_session(user["id"], ip, ua)
    _set_session_cookie(response, session_id)

    return AuthResponse(
        user=UserOut(
            id=user["id"],
            full_name=user["full_name"],
            email=user["email"],
            created_at=str(user["created_at"]),
        ),
        csrf_token=csrf_token,
        message=f"Welcome back, {user['full_name'].split()[0]}!",
    )


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Sign out — destroy session cookie and server-side record."""
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        destroy_session(session_id)
    _clear_session_cookie(response)
    return {"message": "You have been signed out successfully."}


# ─── Current user ─────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Return the authenticated user's profile. Use on app load to verify session."""
    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        created_at="",  # not stored on AuthenticatedUser; pull from DB if needed
    )


# ─── CSRF token ───────────────────────────────────────────────────────────────

@router.get("/csrf-token")
def get_csrf_token(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Return the CSRF token for the current session. Frontend must include this
    as X-CSRF-Token header on all POST/PUT/PATCH/DELETE requests."""
    return {"csrf_token": current_user.csrf_token}
