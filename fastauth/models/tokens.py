from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Pydantic model for token response."""
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Pydantic model for token payload data."""
    username: Optional[str] = None
    token_type: Optional[str] = None
    exp: Optional[int] = None


class RefreshRequest(BaseModel):
    """Pydantic model for token refresh requests."""
    refresh_token: str


class PasswordForgotRequest(BaseModel):
    """Pydantic model for requesting a password reset token."""
    email: str


class PasswordResetRequest(BaseModel):
    """Pydantic model for resetting a password with a reset token."""
    token: str
    new_password: str


class PasswordChangeRequest(BaseModel):
    """Pydantic model for a logged-in user changing their own password."""
    current_password: str
    new_password: str


class EmailVerifyRequest(BaseModel):
    """Pydantic model for confirming an email verification token."""
    token: str
