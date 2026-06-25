from typing import Optional
from sqlmodel import SQLModel, Field


class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    author: str
    year: Optional[int] = None
    stock: int = Field(default=0)


class BookCreate(SQLModel):
    title: str
    author: str
    year: Optional[int] = None
    stock: int = 0


# Para PATCH: todos los campos opcionales (actualizas solo lo que mandas)
class BookUpdate(SQLModel):
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    stock: Optional[int] = None