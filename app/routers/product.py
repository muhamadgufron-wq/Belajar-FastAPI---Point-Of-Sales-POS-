from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead, ProductListResponse, ProductResponse, ProductUpdate

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/", response_model=ProductRead, summary="Tambah product baru")
def create_products(products_in: ProductCreate, session: Session = Depends(get_session)):
    product = Product.model_validate(products_in)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product



@router.get("/", response_model=ProductListResponse, summary="Ambil semua product")
def read_products(
    id_category: int | None = None, 
    session: Session = Depends(get_session)):
    statement = select(Product).where(Product.is_active == True)
    if id_category is not None:
        statement = statement.where(Product.id_category == id_category)
    product = session.exec(statement).all()
    return {
        "message": "Berhasil mengambil data product",
        "data": product,
    }


@router.get("/{product_id}", response_model=ProductResponse, summary="Ambil product berdasarkan ID")
def read_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product tidak ditemukan")
    return {
        "message": "Berhasil mengambil data product",
        "data": product,
    }

@router.patch("/{product_id}", response_model=ProductResponse, summary="Update product berdasarkan ID")
def update_product(product_id: int, product_in: ProductUpdate, session: Session = Depends(get_session)):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product tidak ditemukan")
    product_data = product_in.model_dump(exclude_unset=True)
    db_product.sqlmodel_update(product_data)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return {
        "message": "Berhasil mengupdate data product",
        "data": db_product,
    }

@router.delete("/{product_id}", summary="Hapus product berdasarkan ID")
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product tidak ditemukan!")
    product.is_active = False
    session.add(product)
    session.commit()
    return {
        "message": "Berhasil menghapus data product",
    }