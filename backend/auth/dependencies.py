"""FastAPI dependency — resolve current authenticated user from session cookie."""
from __future__ import annotations

from fastapi import Cookie, HTTPException, Request, status

from backend.auth.sessions import get_session, COOKIE_NAME
from backend.auth.user_db import get_user_by_id


class AuthenticatedUser:
    __slots__ = ("id", "full_name", "email", "csrf_token")

    def __init__(self, id: int, full_name: str, email: str, csrf_token: str):
        self.id         = id
        self.full_name  = full_name
        self.email      = email
        self.csrf_token = csrf_token


def get_current_user(request: Request) -> AuthenticatedUser:
    """FastAPI dependency. Raises 401 if session is missing or expired."""
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please sign in.",
        )

    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
        )

    user = get_user_by_id(session["user_id"])
    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found or inactive.",
        )

    return AuthenticatedUser(
        id         = user["id"],
        full_name  = user["full_name"],
        email      = user["email"],
        csrf_token = session["csrf_token"],
    )


def require_csrf(request: Request, current_user: AuthenticatedUser) -> None:
    """Validate X-CSRF-Token header on state-changing requests."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    provided = request.headers.get("X-CSRF-Token")
    from backend.auth.csrf import validate_csrf_token
    if not validate_csrf_token(current_user.csrf_token, provided):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token.",
        )
