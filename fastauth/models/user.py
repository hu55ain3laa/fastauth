from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel

from fastauth.models.role import RoleRead


class UserRole(SQLModel, table=True):
    """Association table for many-to-many relationship between users and roles."""
    __tablename__ = "user_role"

    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)


class User(SQLModel, table=True):
    """Base user model for database operations."""
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    hashed_password: str
    disabled: bool = Field(default=False)
    email_verified: bool = Field(default=False)
    # Bumped to invalidate all previously issued tokens ("logout everywhere")
    token_version: int = Field(default=0)


class UserRead(BaseModel):
    """Pydantic model for user data that can be exposed to clients."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    disabled: bool
    email_verified: bool = False


class UserReadWithRoles(UserRead):
    """Pydantic model for user data including roles."""
    roles: List[RoleRead] = []


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
