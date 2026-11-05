from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import require_roles
from app.models.product import Product
from app.models.transaction import Transaction, TransactionItem
from app.schemas.report import ReportSummary, ReportSummaryResponse, TopProduct

router = APIRouter(
    prefix="/reports",
    tags=["Reports & Analytics"],
    dependencies=[Depends(require_roles(["OWNER"]))],
)


@router.get(
    "/summary",
    response_model=ReportSummaryResponse,
    summary="Ambil report summary dengan filter tanggal",
)
def get_report_summary(
    start_date: date | None = Query(
        default=None,
        description="Filter tanggal awal (format: YYYY-MM-DD, contoh: 2026-11-01)",
    ),
    end_date: date | None = Query(
        default=None,
        description="Filter tanggal akhir (format: YYYY-MM-DD, contoh: 2026-11-05)",
    ),
    session: Session = Depends(get_session),
):
    """
    Mengambil ringkasan performa toko (omzet, laba bersih, volume transaksi, dan top 5 produk).
    Mendukung filter berdasarkan rentang tanggal `start_date` sampai `end_date` (WIB).
    Jika dikosongkan, akan menampilkan data akumulasi keseluruhan (all-time).
    """
    # Validasi: tanggal mulai tidak boleh melebihi tanggal akhir
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tanggal awal tidak boleh lewat dari tanggal akhir",
        )

    # Siapkan filter kondisi: hanya transaksi yang berstatus COMPLETED
    wib = ZoneInfo("Asia/Jakarta")
    conditions = [Transaction.status == "COMPLETED"]

    if start_date:
        start_dt = datetime.combine(start_date, time.min, tzinfo=wib)
        conditions.append(Transaction.created_at >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date, time.max, tzinfo=wib)
        conditions.append(Transaction.created_at <= end_dt)

    # 1. Hitung total transaksi
    total_transaksi = session.exec(
        select(func.count(Transaction.id)).where(*conditions)
    ).one() or 0

    # 2. Hitung total omset
    total_omset = session.exec(
        select(func.coalesce(func.sum(Transaction.total_transaksi), 0.0)).where(*conditions)
    ).one()

    # 3. Hitung total pcs produk terjual
    total_produk_terjual = session.exec(
        select(func.coalesce(func.sum(TransactionItem.quantity), 0))
        .join(Transaction, Transaction.id == TransactionItem.id_transaction)
        .where(*conditions)
    ).one()

    # 4. Hitung total profit bersih: (harga_jual - harga_modal) * quantity
    total_profit = session.exec(
        select(
            func.coalesce(
                func.sum(
                    (TransactionItem.harga_produk - Product.harga_modal)
                    * TransactionItem.quantity
                ),
                0.0,
            )
        )
        .join(Product, Product.id == TransactionItem.id_product)
        .join(Transaction, Transaction.id == TransactionItem.id_transaction)
        .where(*conditions)
    ).one()

    # 5. Hitung top 5 produk terlaris
    top_produk_query = (
        select(
            Product.id,
            Product.name,
            func.sum(TransactionItem.quantity).label("total_terjual"),
            func.sum(TransactionItem.total).label("total_pendapatan"),
        )
        .join(TransactionItem, Product.id == TransactionItem.id_product)
        .join(Transaction, Transaction.id == TransactionItem.id_transaction)
        .where(*conditions)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(TransactionItem.quantity).desc())
        .limit(5)
    )
    top_rows = session.exec(top_produk_query).all()

    top_produk_list = [
        TopProduct(
            id_product=row[0],
            nama_produk=row[1],
            total_terjual=row[2],
            total_pendapatan=row[3],
        )
        for row in top_rows
    ]

    # Gabungkan semua hasil ke dalam response
    report_summary = ReportSummary(
        start_date=start_date,
        end_date=end_date,
        total_omset=float(round(total_omset)),
        total_profit=float(round(total_profit)),
        total_transaksi=total_transaksi,
        total_produk_terjual=total_produk_terjual,
        top_produk=top_produk_list,
    )

    return {
        "message": "Berhasil mengambil data report summary",
        "data": report_summary,
    }
