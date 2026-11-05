import uuid
from datetime import datetime
from sqlmodel import SQLModel

class StockInItemCreate(SQLModel):
    id_product: int
    qty: int
    harga_beli: float

class StockInCreate(SQLModel):
    supplier: str | None = None
    note: str | None = None
    items: list[StockInItemCreate]

class StockInItemRead(SQLModel):
    id: int
    id_product: int
    qty: int
    harga_beli: float
    total: float
    created_at: datetime

class StockInRead(SQLModel):
    id: uuid.UUID
    id_user: uuid.UUID
    supplier: str | None = None
    note: str | None = None
    total_biaya: float
    created_at: datetime
    items: list[StockInItemRead]

class StockInResponse(SQLModel):
    message: str = "Berhasil mengambil data stock masuk"
    data: StockInRead

class StockInListResponse(SQLModel):
    message: str = "Berhasil mengambil data riwayat stock masuk"
    data: list[StockInRead]