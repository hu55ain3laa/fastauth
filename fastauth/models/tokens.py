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
