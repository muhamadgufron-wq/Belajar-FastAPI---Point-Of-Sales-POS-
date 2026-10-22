from sqlmodel import SQLModel


class ItemCreate(SQLModel):
    name: str
    description: str | None = None
    price: float


class ItemRead(SQLModel):
    id: int
    name: str
    description: str | None = None
    price: float
