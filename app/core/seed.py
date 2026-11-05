import argparse
import sys
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.security import hash_password
from app.models.category import Category
from app.models.user import User


def seed_owner(
    session: Session,
    username: str = settings.FIRST_SUPERUSER_USERNAME,
    password: str = settings.FIRST_SUPERUSER_PASSWORD,
) -> User:
    """Membuat akun OWNER perdana jika belum ada di database (Idempotent)."""
    user = session.exec(select(User).where(User.username == username)).first()
    if user:
        print(f"[INFO] User '{username}' sudah ada di database (Role: {user.role}). Lewati.")
        return user

    print(f"[SEED] Membuat akun OWNER baru: '{username}'...")
    new_owner = User(
        username=username,
        password=hash_password(password),
        role="OWNER",
        is_active=True,
    )
    session.add(new_owner)
    session.commit()
    session.refresh(new_owner)
    print(f"[SUCCESS] Akun OWNER '{username}' berhasil dibuat!")
    return new_owner


def seed_default_categories(session: Session) -> list[Category]:
    """Menambahkan kategori default toko jika belum ada."""
    default_categories = [
        {"name": "Sembako", "description": "Kebutuhan pokok seperti beras, minyak goreng, gula, tepung"},
        {"name": "Minuman", "description": "Air mineral, teh kemasan, kopi, dan aneka minuman dingin"},
        {"name": "Makanan Ringan", "description": "Snack, keripik, biskuit, dan mie instan"},
        {"name": "Bumbu Dapur", "description": "Garam, penyedap rasa, kecap, dan aneka bumbu masakan"},
    ]
    created_categories = []

    for cat_data in default_categories:
        existing = session.exec(
            select(Category).where(Category.name == cat_data["name"])
        ).first()
        if not existing:
            cat = Category(name=cat_data["name"], description=cat_data["description"])
            session.add(cat)
            created_categories.append(cat)
            print(f"[SEED] Kategori '{cat_data['name']}' ditambahkan.")

    if created_categories:
        session.commit()
        print(f"[SUCCESS] {len(created_categories)} kategori default berhasil disimpan.")
    else:
        print("[INFO] Kategori default sudah lengkap di database.")

    return created_categories


def run_seeder(
    username: str = settings.FIRST_SUPERUSER_USERNAME,
    password: str = settings.FIRST_SUPERUSER_PASSWORD,
    with_categories: bool = True,
):
    """Menjalankan proses seeding secara menyeluruh."""
    print("=" * 55)
    print("  🌱 WARUNG UMI NENENG - DATABASE SEEDER")
    print("=" * 55)
    # Pastikan tabel database sudah terbentuk
    init_db()

    with Session(engine) as session:
        seed_owner(session, username=username, password=password)
        if with_categories:
            seed_default_categories(session)

    print("=" * 55)
    print("  ✅ SEEDING SELESAI DENGAN SUKSES!")
    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(
        description="Database seeder untuk inisialisasi akun OWNER perdana dan data awal POS."
    )
    parser.add_argument(
        "--username",
        type=str,
        default=settings.FIRST_SUPERUSER_USERNAME,
        help=f"Username untuk akun OWNER (default dari .env atau '{settings.FIRST_SUPERUSER_USERNAME}')",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=settings.FIRST_SUPERUSER_PASSWORD,
        help="Password untuk akun OWNER (minimal 6 karakter)",
    )
    parser.add_argument(
        "--no-categories",
        action="store_true",
        help="Hanya buat user OWNER tanpa menambahkan kategori default",
    )

    args = parser.parse_args()

    if len(args.password) < 6:
        print("[ERROR] Password minimal 6 karakter sesuai standar keamanan!")
        sys.exit(1)

    run_seeder(
        username=args.username,
        password=args.password,
        with_categories=not args.no_categories,
    )


if __name__ == "__main__":
    main()
