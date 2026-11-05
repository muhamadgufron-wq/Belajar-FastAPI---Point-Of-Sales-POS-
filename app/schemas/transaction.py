import uuid
from sqlmodel import SQLModel, Field
from datetime import datetime

class TransactionItemCreate(SQLModel):
    id_product: int = Field(gt=0, description="ID produk harus valid")
    quantity: int = Field(gt=0, description="Jumlah beli harus minimal 1")

class TransactionCreate(SQLModel):
    uang_bayar: float = Field(ge=0, description="Uang bayar tidak boleh bernilai negatif")
    tipe_pembayaran: str = Field(default="CASH")
    items: list[TransactionItemCreate] = Field(min_length=1, description="Keranjang belanja minimal 1 barang")

class TransactionCancelRequest(SQLModel):
    reason: str | None = Field(default=None, description="Alasan pembatalan transaksi")

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
    status: str = "COMPLETED"
    alasan_pembatalan: str | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    items: list[TransactionItemRead] = []

class TransactionListResponse(SQLModel):
    message: str = "Berhasil mengambil data transaksi"
    data: list[TransactionRead]

class TransactionResponse(SQLModel):
    message: str = "Berhasil mengambil data transaksi"
    data: TransactionRead

class TransactionReceiptRead(SQLModel):
    id_transaction: uuid.UUID
    store_name: str = "Warung Umi Neneng"
    kasir: str
    status: str
    created_at: datetime
    total_transaksi: float
    uang_bayar: float
    uang_kembali: float
    receipt_text: str

class TransactionReceiptResponse(SQLModel):
    message: str = "Berhasil membuat format struk belanja"
    data: TransactionReceiptRead
