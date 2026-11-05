from datetime import datetime

from sqlmodel import Field, SQLModel


class ProductCreate(SQLModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Nama produk minimal 1 dan maksimal 100 karakter",
    )
    id_category: int | None = Field(default=None, description="ID Kategori opsional")
    harga_modal: float = Field(ge=0, description="Harga modal tidak boleh negatif")
    harga_jual: float = Field(ge=0, description="Harga jual tidak boleh negatif")
    stock: int = Field(ge=0, description="Stok fisik tidak boleh negatif")
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
    name: str | None = Field(default=None, min_length=1, max_length=100)
    id_category: int | None = None
    harga_modal: float | None = Field(default=None, ge=0)
    harga_jual: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)


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
