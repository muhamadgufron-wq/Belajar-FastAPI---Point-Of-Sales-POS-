from sqlmodel import SQLModel


class TopProduct(SQLModel):
    id_product: int
    nama_produk: str
    total_terjual: int
    total_pendapatan: float

class ReportSummary(SQLModel):
    total_omset: float
    total_profit: float
    total_transaksi: int
    total_produk_terjual: int
    top_produk: list[TopProduct]

class ReportSummaryResponse(SQLModel):
    message: str = "Berhasil mengambil data report summary"
    data: ReportSummary