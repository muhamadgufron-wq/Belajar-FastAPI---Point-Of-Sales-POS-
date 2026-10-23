import uuid
from datetime import datetime, timezone
from sqlalchemy import func
from sqlmodel import SQLModel, Field

class Transaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id_user: uuid.UUID = Field(foreign_key="user.id")
    total_transaksi: float = Field(default=0.0)
    uang_bayar: float = Field(default=0.0)
    uang_kembali: float = Field(default=0.0)
    tipe_pembayaran: str = Field(default="CASH")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column_kwargs={"server_default": func.now()})

class TransactionItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    id_transaction: uuid.UUID = Field(foreign_key="transaction.id")
    id_product: int = Field(foreign_key="product.id")
    quantity: int
    harga_produk: float
    total: float