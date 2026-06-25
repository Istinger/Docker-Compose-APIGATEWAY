from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    active: bool = Field(default=True)


class UserCreate(SQLModel):
    name: str
    email: str
    active: bool = True


class UserUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None