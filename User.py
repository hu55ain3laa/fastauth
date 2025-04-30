# This is a compatibility layer to support existing imports
# These models are re-exported from the modular structure

from fastauth.models.user import (
    User, 
    UserRead, 
    UserCreate, 
    UserUpdate, 
    UserDelete, 
    UserLogin,
    UserLogout,
    UserEnable,
    UserDisable
)
from fastauth.models.tokens import Token, TokenData

# For backward compatibility
__all__ = [
    "User",
    "UserRead",
    "UserCreate",
    "UserUpdate",
    "UserDelete",
    "UserLogin",
    "UserLogout",
    "UserEnable",
    "UserDisable",
    "Token",
    "TokenData"
]
