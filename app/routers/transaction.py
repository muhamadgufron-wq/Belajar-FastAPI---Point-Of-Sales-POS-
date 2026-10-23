import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.product import Product
from app.models.transaction import Transaction, TransactionItem
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionItemRead,
    TransactionListResponse,
    TransactionRead,
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
