import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel

class StockInItemCreate(SQLModel):
    id_product: int = Field(gt=0, description="ID produk harus valid")
    qty: int = Field(gt=0, description="Jumlah barang masuk harus minimal 1")
    harga_beli: float = Field(ge=0, description="Harga beli tidak boleh negatif")

class StockInCreate(SQLModel):
    supplier: str | None = None
    note: str | None = None
    items: list[StockInItemCreate] = Field(min_length=1, description="Daftar kulakan minimal 1 barang")

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