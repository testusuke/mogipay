"""Authentication utilities for JWT token management."""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

# Load configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-please-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "mogipay2024")


def verify_password(password: str) -> bool:
    """Verify the provided password against the configured AUTH_PASSWORD.

    Args:
        password: The password to verify

    Returns:
        bool: True if password matches, False otherwise
    """
    return password == AUTH_PASSWORD


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: The payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token to verify

    Returns:
        Optional[dict]: Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
