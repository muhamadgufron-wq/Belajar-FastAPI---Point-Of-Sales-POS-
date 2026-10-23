from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead, CategoryListResponse, CategoryResponse, CategoryUpdate

router = APIRouter(
    prefix="/category",
    tags=["Categories"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/", response_model=CategoryRead, summary="Tambah kategori baru")
def create_categories(categories_in: CategoryCreate, session: Session = Depends(get_session)):
    category = Category.model_validate(categories_in)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.get("/", response_model=CategoryListResponse, summary="Ambil semua kategori")
def read_categories(session: Session = Depends(get_session)):
    category = session.exec(select(Category)).all()
    return {
        "message": "Berhasil mengambil data kategori",
        "data": category,
    }

@router.get("/{category_id}", response_model=CategoryResponse, summary="Ambil kategori berdasarkan ID")
def read_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori tidak ditemukan")
    return {
        "message": "Berhasil mengambil data kategori",
        "data": category,
    }

@router.patch("/{category_id}", response_model=CategoryResponse, summary="Update kategori berdasarkan ID")
def update_category(category_id: int, category_in: CategoryUpdate, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori tidak ditemukan")
    category_data = category_in.model_dump(exclude_unset=True)
    category.sqlmodel_update(category_data)
    session.add(category)
    session.commit()
    session.refresh(category)
    return {
        "message": "Berhasil mengupdate data kategori",
        "data": category,
    }

@router.delete("/{category_id}", summary="Hapus kategori berdasarkan ID")
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori tidak ditemukan!")
    # category.is_active = False
    session.delete(category)
    session.commit()
    return {
        "message": "Berhasil menghapus data kategori",
    }