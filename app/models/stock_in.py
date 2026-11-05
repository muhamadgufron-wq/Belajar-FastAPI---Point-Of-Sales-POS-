import uuid 
from datetime import datetime, timezone
from sqlalchemy import func
from sqlmodel import SQLModel, Field

class StockIn(SQLModel, table=True):
    __tablename__ = "stock_in"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id_user: uuid.UUID = Field(foreign_key="user.id")
    supplier: str | None = None
    note: str | None = None
    total_biaya: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column_kwargs={"server_default": func.now()})  

class StockInItem(SQLModel, table=True):
    __tablename__ = "stock_in_item"
    id: int | None = Field(default=None, primary_key=True)
    id_stock_in: uuid.UUID = Field(foreign_key="stock_in.id")
    id_product: int = Field(foreign_key="product.id")
    qty: int
    harga_beli: float
    total: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column_kwargs={"server_default": func.now()})