"""Authentication schemas for request/response validation."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema with password only."""

    password: str = Field(..., description="Authentication password")


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class AuthStatusResponse(BaseModel):
    """Authentication status response schema."""

    authenticated: bool = Field(..., description="Whether the user is authenticated")
    message: str = Field(..., description="Status message")
