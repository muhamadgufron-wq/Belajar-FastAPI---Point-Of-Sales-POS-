import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import require_roles
from app.models.product import Product
from app.models.stock_in import StockIn, StockInItem
from app.models.user import User
from app.schemas.stock_in import (
    StockInCreate,
    StockInItemRead,
    StockInListResponse,
    StockInRead,
    StockInResponse,
)

router = APIRouter(
    prefix="/inventory/stock-in",
    tags=["Inventory - Stock In"],
    dependencies=[Depends(require_roles(["OWNER"]))],
)


# 1. PENCATATAN STOK MASUK / KULAKAN (KHUSUS OWNER)
@router.post(
    "/",
    response_model=StockInResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Catat stok masuk / kulakan baru",
)
def create_stock_in(
    stock_in_data: StockInCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["OWNER"])),
):
    """
    Mencatat faktur kulakan baru, menambah stok barang secara otomatis,
    dan menghitung ulang harga modal menggunakan metode Moving Average (Rupiah utuh).
    """
    if not stock_in_data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daftar barang kulakan tidak boleh kosong",
        )

    new_stock_in = StockIn(
        id_user=current_user.id,
        supplier=stock_in_data.supplier,
        note=stock_in_data.note,
    )

    total_biaya = 0.0
    db_items: list[StockInItem] = []

    for item_in in stock_in_data.items:
        if item_in.qty <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Jumlah barang (qty) untuk produk ID {item_in.id_product} harus lebih dari 0",
            )
        if item_in.harga_beli < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Harga beli untuk produk ID {item_in.id_product} tidak boleh negatif",
            )

        product = session.get(Product, item_in.id_product)
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produk ID {item_in.id_product} tidak ditemukan atau nonaktif",
            )

        # === LOGIKA MOVING AVERAGE (RATA-RATA TERTINGBANG) ===
        if product.stock <= 0:
            # Jika stok lama habis atau minus, modal langsung pakai harga beli terbaru
            product.harga_modal = float(item_in.harga_beli)
        else:
            # Hitung rata-rata tertimbang
            total_nilai_modal = (product.stock * product.harga_modal) + (item_in.qty * item_in.harga_beli)
            total_stok_baru = product.stock + item_in.qty
            # Bulatkan ke Rupiah utuh
            product.harga_modal = float(round(total_nilai_modal / total_stok_baru))

        # Tambahkan stok fisik barang
        product.stock += item_in.qty
        session.add(product)

        # Hitung subtotal nota
        subtotal = item_in.qty * item_in.harga_beli
        total_biaya += subtotal

        db_item = StockInItem(
            id_stock_in=new_stock_in.id,
            id_product=item_in.id_product,
            qty=item_in.qty,
            harga_beli=item_in.harga_beli,
            total=subtotal,
        )
        db_items.append(db_item)

    # Simpan header faktur dan rincian item dalam 1 transaksi atomic (ACID)
    new_stock_in.total_biaya = total_biaya
    session.add(new_stock_in)
    for item in db_items:
        session.add(item)

    session.commit()
    session.refresh(new_stock_in)
    for item in db_items:
        session.refresh(item)

    return StockInResponse(
        message="Stok masuk berhasil dicatat dan modal produk diperbarui",
        data=StockInRead(
            id=new_stock_in.id,
            id_user=new_stock_in.id_user,
            supplier=new_stock_in.supplier,
            note=new_stock_in.note,
            total_biaya=new_stock_in.total_biaya,
            created_at=new_stock_in.created_at,
            items=[
                StockInItemRead(
                    id=item.id,
                    id_product=item.id_product,
                    qty=item.qty,
                    harga_beli=item.harga_beli,
                    total=item.total,
                    created_at=item.created_at,
                )
                for item in db_items
            ],
        ),
    )


# 2. MELIHAT SELURUH RIWAYAT KULAKAN (KHUSUS OWNER)
@router.get(
    "/",
    response_model=StockInListResponse,
    summary="Melihat seluruh riwayat stok masuk",
)
def get_all_stock_in(
    session: Session = Depends(get_session),
):
    """Melihat daftar seluruh faktur kulakan yang pernah dicatat."""
    stock_ins = session.exec(select(StockIn).order_by(StockIn.created_at.desc())).all()

    result: list[StockInRead] = []
    for s in stock_ins:
        items = session.exec(select(StockInItem).where(StockInItem.id_stock_in == s.id)).all()
        result.append(
            StockInRead(
                id=s.id,
                id_user=s.id_user,
                supplier=s.supplier,
                note=s.note,
                total_biaya=s.total_biaya,
                created_at=s.created_at,
                items=[
                    StockInItemRead(
                        id=it.id,
                        id_product=it.id_product,
                        qty=it.qty,
                        harga_beli=it.harga_beli,
                        total=it.total,
                        created_at=it.created_at,
                    )
                    for it in items
                ],
            )
        )

    return StockInListResponse(
        message="Berhasil mengambil riwayat stok masuk",
        data=result,
    )


# 3. MELIHAT RINCIAN 1 FAKTUR KULAKAN (KHUSUS OWNER)
@router.get(
    "/{id}",
    response_model=StockInResponse,
    summary="Melihat detail 1 faktur stok masuk",
)
def get_stock_in_detail(
    id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """Melihat rincian produk dalam satu faktur kulakan."""
    stock_in = session.get(StockIn, id)
    if not stock_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faktur stok masuk dengan ID {id} tidak ditemukan",
        )

    items = session.exec(select(StockInItem).where(StockInItem.id_stock_in == stock_in.id)).all()

    return StockInResponse(
        message="Berhasil mengambil detail stok masuk",
        data=StockInRead(
            id=stock_in.id,
            id_user=stock_in.id_user,
            supplier=stock_in.supplier,
            note=stock_in.note,
            total_biaya=stock_in.total_biaya,
            created_at=stock_in.created_at,
            items=[
                StockInItemRead(
                    id=it.id,
                    id_product=it.id_product,
                    qty=it.qty,
                    harga_beli=it.harga_beli,
                    total=it.total,
                    created_at=it.created_at,
                )
                for it in items
            ],
        ),
    )
