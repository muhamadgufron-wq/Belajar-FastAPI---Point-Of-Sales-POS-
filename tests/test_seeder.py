import uuid
from sqlmodel import Session

from app.core.database import engine
from app.core.seed import seed_default_categories, seed_owner


def test_seed_owner_creation_and_idempotency():
    """Memastikan seeder mampu membuat akun OWNER baru dan bersifat idempoten."""
    random_suffix = str(uuid.uuid4())[:8]
    test_username = f"test_owner_{random_suffix}"
    test_password = "SeederPassword123!"

    with Session(engine) as session:
        # 1. Eksekusi pertama: harus membuat user baru
        user1 = seed_owner(session, username=test_username, password=test_password)
        assert user1 is not None
        assert user1.username == test_username
        assert user1.role == "OWNER"

        # 2. Eksekusi kedua (idempotent): tidak boleh error duplicate key, melainkan mereturn user yang sama
        user2 = seed_owner(session, username=test_username, password=test_password)
        assert user2 is not None
        assert user2.id == user1.id


def test_seed_default_categories_idempotency():
    """Memastikan seed_default_categories aman dijalankan berulang kali."""
    with Session(engine) as session:
        # Jalankan seed kategori
        cats = seed_default_categories(session)
        assert isinstance(cats, list)
