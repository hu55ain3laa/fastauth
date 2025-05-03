from typing import Optional, List, Any
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship


class UserRole(SQLModel, table=True):
    """Association table for many-to-many relationship between users and roles."""
    __tablename__ = "user_role"
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)


class User(SQLModel, table=True):
    """Base user model for database operations."""
    __tablename__ = "user"
    
    id: int = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    hashed_password: str
    disabled: bool = Field(default=False)


class UserRead(BaseModel):
    """Pydantic model for user data that can be exposed to clients."""
    id: int
    username: str
    email: str
    disabled: bool
    
    class Config:
        from_attributes = True


class UserReadWithRoles(UserRead):
    """Pydantic model for user data including roles."""
    roles: List[Any] = []
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Pydantic model for user creation requests."""
    username: str
    email: str
    password: str


class UserUpdate(BaseModel):
    """Pydantic model for user update requests."""
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserDelete(BaseModel):
    """Pydantic model for user deletion requests."""
    username: str


class UserLogin(BaseModel):
    """Pydantic model for user login requests."""
    username: str
    password: str


class UserLogout(BaseModel):
    """Pydantic model for user logout requests."""
    username: str


class UserEnable(BaseModel):
    """Pydantic model for enabling a user."""
    username: str
    disabled: bool = False


class UserDisable(BaseModel):
    """Pydantic model for disabling a user."""
    username: str
    disabled: bool = True
