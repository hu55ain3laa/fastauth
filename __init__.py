# Import from modular structure
from fastauth.core.auth import FastAuth, OAuth2PasswordBearerWithCookie
from fastauth.models.user import User, UserCreate, UserRead, UserUpdate, UserDelete, UserLogin
from fastauth.models.tokens import Token, TokenData

__version__ = "0.2.0"
__all__ = [
    "FastAuth",
    "OAuth2PasswordBearerWithCookie",
    "User",
    "Token",
    "TokenData",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserDelete",
    "UserLogin"
]