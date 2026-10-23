import uuid
from sqlmodel import SQLModel
from datetime import datetime

class TransactionItemCreate(SQLModel):
    id_product: int
    quantity: int

class TransactionCreate(SQLModel):
    uang_bayar: float
    tipe_pembayaran: str = "CASH"
    items: list[TransactionItemCreate]

class TransactionItemRead(SQLModel):
    id: int
    id_product: int
    quantity: int
    harga_produk: float
    total: float

class TransactionRead(SQLModel):
    id: uuid.UUID
    id_user: uuid.UUID
    total_transaksi: float
    uang_bayar: float
    uang_kembali: float
    tipe_pembayaran: str
    created_at: datetime
    items: list[TransactionItemRead]  = []

class TransactionListResponse(SQLModel):
    message: str = "Berhasil mengambil data transaksi"
    data: list[TransactionRead]

class TransactionResponse(SQLModel):
    message: str = "Berhasil mengambil data transaksi"
    data: TransactionRead