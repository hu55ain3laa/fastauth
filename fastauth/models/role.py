from typing import List, Optional, Any
from sqlmodel import SQLModel, Field, Relationship


class Role(SQLModel, table=True):
    """Role model for role-based authorization."""
    __tablename__ = "role"
    
    id: int = Field(primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    
    # The relationship with users is handled by the backref in the User model


class RoleCreate(SQLModel):
    """Pydantic model for role creation requests."""
    name: str
    description: Optional[str] = None


class RoleRead(SQLModel):
    """Pydantic model for role data that can be exposed to clients."""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class RoleUpdate(SQLModel):
    """Pydantic model for role update requests."""
    name: Optional[str] = None
    description: Optional[str] = None
