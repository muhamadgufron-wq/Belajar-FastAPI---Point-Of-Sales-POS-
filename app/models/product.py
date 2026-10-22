from sqlmodel import Field, SQLModel
from datetime import datetime, timezone
from sqlalchemy import func


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    harga_modal: float
    harga_jual: float
    stock: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column_kwargs={"server_default": func.now()})
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()})