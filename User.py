from typing import Optional
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    hashed_password: str
    disabled: bool = Field(default=False)

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    disabled: bool
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserDelete(BaseModel):    
    username: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserLogout(BaseModel):
    username: str

class UserEnable(BaseModel):
    username: str
    disabled: bool = True

class UserDisable(BaseModel):
    username: str
    disabled: bool = False