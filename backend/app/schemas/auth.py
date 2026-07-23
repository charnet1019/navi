"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    """Authentication response without exposing JWTs to JavaScript."""
    message: str = "ok"


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1, max_length=100)
