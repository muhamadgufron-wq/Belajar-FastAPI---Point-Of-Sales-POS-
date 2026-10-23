from datetime import datetime
from sqlmodel import SQLModel

class CategoryCreate(SQLModel):
    name: str
    description: str | None = None

class CategoryRead(SQLModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

class CategoryUpdate(SQLModel):
    name: str | None = None
    description: str | None = None

class CategoryListResponse(SQLModel):
    message: str = "Berhasil mengambil data category"
    data: list[CategoryRead]

class CategoryResponse(SQLModel):
    message: str = "Berhasil mengambil data category"
    data: CategoryRead