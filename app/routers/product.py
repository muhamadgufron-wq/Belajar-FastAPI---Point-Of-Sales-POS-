import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.product import Product
from app.schemas.product import (
    PaginationMeta,
    ProductCreate,
    ProductListResponse,
    ProductRead,
    ProductResponse,
    ProductUpdate,
)
from app.dependencies import require_roles

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/", response_model=ProductRead, summary="Tambah product baru", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["OWNER"]))])
def create_products(
    products_in: ProductCreate, session: Session = Depends(get_session)
):
    product = Product.model_validate(products_in)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.get("/", response_model=ProductListResponse, summary="Ambil semua product")
def read_products(
    page: int = Query(default=1, ge=1, description="Halaman data yang ingin diambil"),
    limit: int = Query(default=10, ge=1, le=100, description="Jumlah data per halaman"),
    search: str | None = Query(default=None, description="Kata kunci pencarian product"),
    id_category: int | None = Query(default=None, description="Filter berdasarkan kategori"),
    session: Session = Depends(get_session),
):
    # 1. Kumpulkan kondisi filter (kondisi dasar: hanya barang aktif)
    conditions = [Product.is_active == True]
    if id_category is not None:
        conditions.append(Product.id_category == id_category)
    if search:
        conditions.append(Product.name.ilike(f"%{search}%"))

    # 2. Hitung total data yang cocok & total halaman
    count_statement = select(func.count(Product.id)).where(*conditions)
    total_data = session.exec(count_statement).one() or 0
    total_page = math.ceil(total_data / limit) if total_data > 0 else 1

    # 3. Ambil data dengan OFFSET & LIMIT
    offset = (page - 1) * limit
    statement = (
        select(Product)
        .where(*conditions)
        .order_by(Product.id.desc())
        .offset(offset)
        .limit(limit)
    )
    products = session.exec(statement).all()

    # 4. Return respon lengkap dengan meta pagination
    return {
        "message": "Berhasil mengambil data product",
        "data": products,
        "meta": {
            "page": page,
            "limit": limit,
            "total_data": total_data,
            "total_page": total_page,
        },
    }


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Ambil product berdasarkan ID",
)
def read_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product tidak ditemukan",
        )
    return {
        "message": "Berhasil mengambil data product",
        "data": product,
    }


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product berdasarkan ID",
    dependencies=[Depends(require_roles(["OWNER"]))],
    status_code=status.HTTP_200_OK,
)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    session: Session = Depends(get_session),
):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product tidak ditemukan",
        )
    product_data = product_in.model_dump(exclude_unset=True)
    db_product.sqlmodel_update(product_data)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return {
        "message": "Berhasil mengupdate data product",
        "data": db_product,
    }


@router.delete("/{product_id}", summary="Hapus product berdasarkan ID", status_code=status.HTTP_200_OK, dependencies=[Depends(require_roles(["OWNER"]))])
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product tidak ditemukan!",
        )
    product.is_active = False
    session.add(product)
    session.commit()
    return {
        "message": "Berhasil menghapus data product",
    }
