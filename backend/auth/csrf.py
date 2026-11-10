"""CSRF token generation, validation, and session-bound request middleware."""
from __future__ import annotations
import secrets

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse



def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def validate_csrf_token(expected: str, provided: str | None) -> bool:
    if not provided or not expected:
        return False
    return secrets.compare_digest(expected, provided)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Require the session's CSRF token on state-changing authenticated requests.

    Requests without a valid session are left to the route's authentication
    dependency, which returns the usual 401 response. This keeps public login
    and registration usable while protecting every mutation made with a session.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await call_next(request)

        from backend.auth.sessions import COOKIE_NAME, get_session

        session_id = request.cookies.get(COOKIE_NAME)
        session = get_session(session_id) if session_id else None
        if session:
            provided = request.headers.get("X-CSRF-Token")
            if not provided:
                return JSONResponse(
                    {"detail": "Missing CSRF token."}, status_code=403
                )
            if not validate_csrf_token(session.get("csrf_token", ""), provided):
                return JSONResponse(
                    {"detail": "Invalid CSRF token."}, status_code=403
                )

        return await call_next(request)
