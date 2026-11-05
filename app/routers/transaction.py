import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user, require_roles
from app.models.product import Product
from app.models.transaction import Transaction, TransactionItem
from app.models.user import User
from app.schemas.transaction import (
    TransactionCancelRequest,
    TransactionCreate,
    TransactionItemRead,
    TransactionListResponse,
    TransactionRead,
    TransactionReceiptRead,
    TransactionReceiptResponse,
    TransactionResponse,
)

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    dependencies=[Depends(get_current_user)],
)


# 1. CHECKOUT TRANSAKSI BARU (KASIR)
@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout transaksi baru",
)
def create_transaction(
    trans_in: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Proses transaksi checkout kasir: validasi stok, potong stok otomatis, dan simpan struk."""
    # Validasi 1: Keranjang belanja tidak boleh kosong
    if not trans_in.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keranjang belanja tidak boleh kosong",
        )

    # Inisialisasi data transaksi
    new_transaction = Transaction(
        id_user=current_user.id,
        tipe_pembayaran=trans_in.tipe_pembayaran,
        uang_bayar=trans_in.uang_bayar,
        status="COMPLETED",
    )

    total_transaksi = 0.0
    db_items: list[TransactionItem] = []

    # Validasi 2 & Hitung Barang:
    for item_in in trans_in.items:
        product = session.get(Product, item_in.id_product)

        # Cek ketersediaan produk
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produk ID {item_in.id_product} tidak ditemukan atau nonaktif",
            )

        # Cek kecukupan stok
        if product.stock < item_in.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stok produk '{product.name}' tidak mencukupi (sisa: {product.stock}, diminta: {item_in.quantity})",
            )

        # Hitung subtotal dan kurangi stok produk
        subtotal = product.harga_jual * item_in.quantity
        total_transaksi += subtotal
        product.stock -= item_in.quantity
        session.add(product)

        # Siapkan item transaksi
        trans_item = TransactionItem(
            id_transaction=new_transaction.id,
            id_product=product.id,
            quantity=item_in.quantity,
            harga_produk=product.harga_jual,
            total=subtotal,
        )
        db_items.append(trans_item)

    # Validasi 3: Cek kecukupan uang bayar
    if trans_in.uang_bayar < total_transaksi:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uang bayar kurang! Total belanja: Rp {total_transaksi:,.0f}, Uang diserahkan: Rp {trans_in.uang_bayar:,.0f}",
        )

    # Hitung uang kembali
    new_transaction.total_transaksi = total_transaksi
    new_transaction.uang_kembali = trans_in.uang_bayar - total_transaksi

    # Simpan transaksi dan semua itemnya (ACID)
    session.add(new_transaction)
    for db_item in db_items:
        session.add(db_item)
    session.commit()
    session.refresh(new_transaction)

    # Susun respon struk nota lengkap
    response_data = TransactionRead(
        id=new_transaction.id,
        id_user=new_transaction.id_user,
        total_transaksi=new_transaction.total_transaksi,
        uang_bayar=new_transaction.uang_bayar,
        uang_kembali=new_transaction.uang_kembali,
        tipe_pembayaran=new_transaction.tipe_pembayaran,
        status=new_transaction.status,
        alasan_pembatalan=new_transaction.alasan_pembatalan,
        cancelled_at=new_transaction.cancelled_at,
        created_at=new_transaction.created_at,
        items=[
            TransactionItemRead(
                id=item.id,
                id_product=item.id_product,
                quantity=item.quantity,
                harga_produk=item.harga_produk,
                total=item.total,
            )
            for item in db_items
        ],
    )

    return {
        "message": "Transaksi berhasil disimpan",
        "data": response_data,
    }


# 2. RIWAYAT SEMUA TRANSAKSI
@router.get(
    "/",
    response_model=TransactionListResponse,
    summary="Ambil riwayat semua transaksi",
)
def read_transactions(session: Session = Depends(get_session)):
    """Mengambil seluruh riwayat transaksi yang pernah dibuat oleh kasir."""
    transactions = session.exec(
        select(Transaction).order_by(Transaction.created_at.desc())
    ).all()

    result = []
    for trx in transactions:
        items = session.exec(
            select(TransactionItem).where(
                TransactionItem.id_transaction == trx.id
            )
        ).all()
        result.append(
            TransactionRead(
                id=trx.id,
                id_user=trx.id_user,
                total_transaksi=trx.total_transaksi,
                uang_bayar=trx.uang_bayar,
                uang_kembali=trx.uang_kembali,
                tipe_pembayaran=trx.tipe_pembayaran,
                status=trx.status,
                alasan_pembatalan=trx.alasan_pembatalan,
                cancelled_at=trx.cancelled_at,
                created_at=trx.created_at,
                items=[
                    TransactionItemRead(
                        id=i.id,
                        id_product=i.id_product,
                        quantity=i.quantity,
                        harga_produk=i.harga_produk,
                        total=i.total,
                    )
                    for i in items
                ],
            )
        )

    return {
        "message": "Berhasil mengambil riwayat transaksi",
        "data": result,
    }


# 3. DETAIL 1 TRANSAKSI (STRUK NOTA) BY ID
@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Ambil detail 1 transaksi/struk",
)
def read_transaction(
    transaction_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """Mencari satu data transaksi spesifik beserta rincian itemnya berdasarkan ID struk."""
    trx = session.get(Transaction, transaction_id)
    if not trx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi tidak ditemukan",
        )

    items = session.exec(
        select(TransactionItem).where(TransactionItem.id_transaction == trx.id)
    ).all()

    response_data = TransactionRead(
        id=trx.id,
        id_user=trx.id_user,
        total_transaksi=trx.total_transaksi,
        uang_bayar=trx.uang_bayar,
        uang_kembali=trx.uang_kembali,
        tipe_pembayaran=trx.tipe_pembayaran,
        status=trx.status,
        alasan_pembatalan=trx.alasan_pembatalan,
        cancelled_at=trx.cancelled_at,
        created_at=trx.created_at,
        items=[
            TransactionItemRead(
                id=i.id,
                id_product=i.id_product,
                quantity=i.quantity,
                harga_produk=i.harga_produk,
                total=i.total,
            )
            for i in items
        ],
    )

    return {
        "message": "Berhasil mengambil data transaksi",
        "data": response_data,
    }


# 4. PEMBATALAN / CANCEL TRANSAKSI (KHUSUS OWNER)
@router.post(
    "/{transaction_id}/cancel",
    response_model=TransactionResponse,
    summary="Batalkan transaksi dan kembalikan stok produk (Khusus Owner)",
    dependencies=[Depends(require_roles(["OWNER"]))],
)
def cancel_transaction(
    transaction_id: uuid.UUID,
    cancel_data: TransactionCancelRequest | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["OWNER"])),
):
    """
    Membatalkan transaksi penjualan yang sudah terjadi:
    1. Mengubah status transaksi menjadi 'CANCELLED'.
    2. Mengembalikan kuantitas stok produk ke katalog secara otomatis.
    3. Mencatat waktu pembatalan dan alasan pembatalan.
    Hanya dapat dilakukan oleh pengguna dengan role 'OWNER'.
    """
    trx = session.get(Transaction, transaction_id)
    if not trx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi tidak ditemukan",
        )

    if trx.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaksi ini sudah dibatalkan sebelumnya",
        )

    # 1. Ambil seluruh item dalam transaksi ini
    items = session.exec(
        select(TransactionItem).where(TransactionItem.id_transaction == trx.id)
    ).all()

    # 2. Kembalikan stok untuk setiap produk terkait
    for item in items:
        product = session.get(Product, item.id_product)
        if product:
            product.stock += item.quantity
            session.add(product)

    # 3. Update status transaksi
    trx.status = "CANCELLED"
    trx.cancelled_at = datetime.now(timezone.utc)
    trx.alasan_pembatalan = (
        cancel_data.reason if cancel_data and cancel_data.reason else "Dibatalkan oleh Owner"
    )
    session.add(trx)

    # 4. Commit perubahan stok dan transaksi secara atomic (ACID)
    session.commit()
    session.refresh(trx)

    response_data = TransactionRead(
        id=trx.id,
        id_user=trx.id_user,
        total_transaksi=trx.total_transaksi,
        uang_bayar=trx.uang_bayar,
        uang_kembali=trx.uang_kembali,
        tipe_pembayaran=trx.tipe_pembayaran,
        status=trx.status,
        alasan_pembatalan=trx.alasan_pembatalan,
        cancelled_at=trx.cancelled_at,
        created_at=trx.created_at,
        items=[
            TransactionItemRead(
                id=i.id,
                id_product=i.id_product,
                quantity=i.quantity,
                harga_produk=i.harga_produk,
                total=i.total,
            )
            for i in items
        ],
    )

    return {
        "message": "Transaksi berhasil dibatalkan dan stok produk telah dikembalikan",
        "data": response_data,
    }


# HELPER FORMAT STRUK THERMAL KASIR (LEBAR 32 KARAKTER)
def build_receipt_text(
    trx: Transaction,
    items: list[TransactionItem],
    cashier_username: str,
    product_names: dict[int, str],
) -> str:
    wib = ZoneInfo("Asia/Jakarta")
    created_at_wib = trx.created_at.astimezone(wib).strftime("%d/%m/%Y %H:%M WIB")
    w = 32

    def format_row(left: str, right: str) -> str:
        space = w - len(left) - len(right)
        return left + " " * max(space, 1) + right

    lines = [
        "=" * w,
        "WARUNG UMI NENENG".center(w),
        "Jl. Sembako Barokah No. 12".center(w),
        "Telp: 0812-3456-7890".center(w),
        "=" * w,
        f"No. Struk : TRX-{str(trx.id)[:8].upper()}",
        f"Tanggal   : {created_at_wib}",
        f"Kasir     : {cashier_username}",
        f"Metode    : {trx.tipe_pembayaran}",
        f"Status    : {trx.status}",
        "-" * w,
    ]

    for item in items:
        p_name = product_names.get(item.id_product, f"Produk #{item.id_product}")
        lines.append(p_name[:w])
        detail_qty = f"  {item.quantity} x {item.harga_produk:,.0f}".replace(",", ".")
        subtotal_str = f"{item.total:,.0f}".replace(",", ".")
        lines.append(format_row(detail_qty, subtotal_str))

    lines.extend([
        "-" * w,
        format_row("Total Belanja", f"Rp {trx.total_transaksi:,.0f}".replace(",", ".")),
        format_row("Tunai (Bayar)", f"Rp {trx.uang_bayar:,.0f}".replace(",", ".")),
        format_row("Kembalian", f"Rp {trx.uang_kembali:,.0f}".replace(",", ".")),
    ])

    if trx.status == "CANCELLED":
        cancelled_at_wib = (
            trx.cancelled_at.astimezone(wib).strftime("%d/%m/%Y %H:%M WIB")
            if trx.cancelled_at
            else "-"
        )
        lines.extend([
            "=" * w,
            "*** TRANSAKSI DIBATALKAN ***".center(w),
            f"Alasan : {trx.alasan_pembatalan or '-'}",
            f"Waktu  : {cancelled_at_wib}",
        ])

    lines.extend([
        "=" * w,
        "Terima Kasih Atas Kunjungan Anda".center(w),
        "Barang yang sudah dibeli".center(w),
        "tidak dapat dikembalikan".center(w),
        "=" * w,
    ])

    return "\n".join(lines)


# 5. CETAK STRUK KASIR (JSON DTO & TEXT STRUK)
@router.get(
    "/{transaction_id}/receipt",
    response_model=TransactionReceiptResponse,
    summary="Ambil format struk belanja kasir",
)
def get_transaction_receipt(
    transaction_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """Menghasilkan format struk kasir profesional (siap cetak printer thermal 58mm)."""
    trx = session.get(Transaction, transaction_id)
    if not trx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi tidak ditemukan",
        )

    # Ambil kasir pelayan transaksi
    cashier = session.get(User, trx.id_user)
    cashier_username = cashier.username if cashier else "Kasir"

    # Ambil items dan nama produknya
    items = session.exec(
        select(TransactionItem).where(TransactionItem.id_transaction == trx.id)
    ).all()

    product_names = {}
    for it in items:
        prod = session.get(Product, it.id_product)
        product_names[it.id_product] = prod.name if prod else f"Produk #{it.id_product}"

    receipt_str = build_receipt_text(trx, items, cashier_username, product_names)

    return TransactionReceiptResponse(
        message="Berhasil membuat format struk belanja",
        data=TransactionReceiptRead(
            id_transaction=trx.id,
            store_name="Warung Umi Neneng",
            kasir=cashier_username,
            status=trx.status,
            created_at=trx.created_at,
            total_transaksi=trx.total_transaksi,
            uang_bayar=trx.uang_bayar,
            uang_kembali=trx.uang_kembali,
            receipt_text=receipt_str,
        ),
    )


# 6. CETAK STRUK KASIR LANGSUNG (RAW PLAIN TEXT)
@router.get(
    "/{transaction_id}/receipt/print",
    response_class=PlainTextResponse,
    summary="Cetak langsung struk kasir dalam format raw text",
)
def print_transaction_receipt(
    transaction_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """
    Mengembalikan format teks struk murni (MIME type text/plain)
    yang siap dikirim langsung ke printer kasir thermal Bluetooth / USB.
    """
    trx = session.get(Transaction, transaction_id)
    if not trx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaksi tidak ditemukan",
        )

    cashier = session.get(User, trx.id_user)
    cashier_username = cashier.username if cashier else "Kasir"

    items = session.exec(
        select(TransactionItem).where(TransactionItem.id_transaction == trx.id)
    ).all()

    product_names = {}
    for it in items:
        prod = session.get(Product, it.id_product)
        product_names[it.id_product] = prod.name if prod else f"Produk #{it.id_product}"

    receipt_str = build_receipt_text(trx, items, cashier_username, product_names)
    return PlainTextResponse(content=receipt_str, media_type="text/plain; charset=utf-8")
