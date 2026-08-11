from typing import Optional

from sqlmodel import Field, SQLModel


class Role(SQLModel, table=True):
    """Role model for role-based authorization."""
    __tablename__ = "role"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None


class RoleCreate(SQLModel):
    """Pydantic model for role creation requests."""
    name: str
    description: Optional[str] = None


class RoleRead(SQLModel):
    """Pydantic model for role data that can be exposed to clients."""
    id: int
    name: str
    description: Optional[str] = None


class RoleUpdate(SQLModel):
    """Pydantic model for role update requests."""
    name: Optional[str] = None
    description: Optional[str] = None
