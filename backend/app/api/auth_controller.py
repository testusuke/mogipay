"""Authentication controller for login/logout endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies.auth import get_current_user
from app.schemas.auth import AuthStatusResponse, LoginRequest, TokenResponse
from app.utils.auth import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, response: Response):
    """Login endpoint with password-only authentication.

    Args:
        request: Login request with password
        response: FastAPI response object to set cookies

    Returns:
        TokenResponse: JWT access token

    Raises:
        HTTPException: If password is invalid
    """
    # Verify password
    if not verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_CREDENTIALS",
                "message": "パスワードが正しくありません",
                "details": {"reason": "password verification failed"},
            },
        )

    # Create JWT token
    access_token = create_access_token(data={"sub": "authenticated"})

    # Set httpOnly cookie (7 days expiration)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Prevent XSS attacks
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",  # CSRF protection
        max_age=604800,  # 7 days in seconds
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/logout")
def logout(response: Response):
    """Logout endpoint that clears the authentication cookie.

    Args:
        response: FastAPI response object to clear cookies

    Returns:
        dict: Logout success message
    """
    # Clear the access_token cookie
    response.delete_cookie(key="access_token")

    return {"message": "ログアウトしました"}


@router.get("/me", response_model=AuthStatusResponse)
def get_auth_status(current_user: dict = Depends(get_current_user)):
    """Get current authentication status.

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        AuthStatusResponse: Authentication status
    """
    return AuthStatusResponse(
        authenticated=True, message="認証済みです"
    )
