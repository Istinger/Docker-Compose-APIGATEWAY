from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    book_id: int = Field(index=True)
    quantity: int = Field(default=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrderCreate(SQLModel):
    user_id: int
    book_id: int
    quantity: int = 1


class OrderUpdate(SQLModel):
    quantity: Optional[int] = None