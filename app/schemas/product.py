from datetime import datetime
from sqlmodel import SQLModel


class ProductCreate(SQLModel):
    name: str
    id_category: int | None = None
    harga_modal: float
    harga_jual: float
    stock: int
    is_active: bool = True


class ProductRead(SQLModel):
    id: int
    id_category: int | None = None
    name: str
    harga_modal: float
    harga_jual: float
    stock: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class ProductUpdate(SQLModel):
    name: str | None = None
    id_category: int | None = None
    harga_modal: float | None = None
    harga_jual: float | None = None
    stock: int | None = None


class PaginationMeta(SQLModel):
    total_data: int
    total_page: int
    page: int
    limit: int


class ProductListResponse(SQLModel):
    message: str = "Berhasil mengambil data product"
    data: list[ProductRead]
    meta: PaginationMeta


class ProductResponse(SQLModel):
    message: str = "Berhasil mengambil data product"
    data: ProductRead
