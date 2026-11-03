from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.product import Product
from app.models.transaction import Transaction, TransactionItem
from app.schemas.report import ReportSummary, ReportSummaryResponse, TopProduct
from app.dependencies import require_roles

router = APIRouter(
    prefix="/reports",
    tags=["Reports & Analytics"],
    dependencies=[Depends(require_roles(["OWNER"]))],
)


@router.get(
    "/summary",
    response_model=ReportSummaryResponse,
    summary="Ambil report summary",
)
def get_report_summary(session: Session = Depends(get_session)):
    # 1. Hitung total transaksi
    total_transaksi = session.exec(select(func.count(Transaction.id))).one() or 0

    # 2. Hitung total omset
    total_omset = session.exec(
        select(func.coalesce(func.sum(Transaction.total_transaksi), 0.0))
    ).one()

    # 3. Hitung total pcs produk terjual
    total_produk_terjual = session.exec(
        select(func.coalesce(func.sum(TransactionItem.quantity), 0))
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
        ).join(Product, Product.id == TransactionItem.id_product)
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
        total_omset=total_omset,
        total_profit=total_profit,
        total_transaksi=total_transaksi,
        total_produk_terjual=total_produk_terjual,
        top_produk=top_produk_list,
    )

    return {
        "message": "Berhasil mengambil data report summary",
        "data": report_summary,
    }
