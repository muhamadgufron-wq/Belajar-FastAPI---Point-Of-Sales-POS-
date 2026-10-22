from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.database import get_session
from app.dependencies import get_current_user
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemRead

# Proteksi seluruh endpoint di bawah /items agar wajib autentikasi (Bearer Token)
router = APIRouter(
    prefix="/items",
    tags=["Items"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", response_model=ItemRead, summary="Tambah item baru")
def create_item(item_in: ItemCreate, session: Session = Depends(get_session)):
    """Membuat item baru (Khusus User yang sudah login)."""
    item = Item.model_validate(item_in)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/", response_model=list[ItemRead], summary="Ambil semua item")
def read_items(session: Session = Depends(get_session)):
    """Mengambil semua daftar item dari PostgreSQL (Khusus User yang sudah login)."""
    items = session.exec(select(Item)).all()
    return items
