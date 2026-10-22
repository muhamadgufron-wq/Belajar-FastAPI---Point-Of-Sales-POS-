from sqlmodel import SQLModel
from datetime import datetime

class ProductCreate(SQLModel):
    name: str
    harga_modal: float
    harga_jual: float
    stock: int
    is_active: bool = True

class ProductRead(SQLModel):
    id: int
    name: str
    harga_modal: float
    harga_jual: float
    stock: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class ProductUpdate(SQLModel):
    name: str | None = None
    harga_modal: float | None = None
    harga_jual: float | None = None
    stock: int | None = None
    is_active: bool | None = None

class ProductListResponse(SQLModel):
    message: str = "Berhasil mengambil data product"
    data: list[ProductRead]

class ProductResponse(SQLModel):
    message: str = "Berhasil mengambil data product"
    data: ProductRead

