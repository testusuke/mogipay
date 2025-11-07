"""Authentication dependencies for FastAPI endpoints."""

from typing import Optional

from fastapi import Cookie, HTTPException, status

from app.utils.auth import verify_token


def get_current_user(access_token: Optional[str] = Cookie(None)) -> dict:
    """Dependency to get the current authenticated user from cookie.

    Args:
        access_token: JWT token from cookie

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "認証が必要です",
                "details": {"reason": "access_token cookie not found"},
            },
        )

    payload = verify_token(access_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": "無効な認証トークンです",
                "details": {"reason": "token verification failed"},
            },
        )

    return payload
