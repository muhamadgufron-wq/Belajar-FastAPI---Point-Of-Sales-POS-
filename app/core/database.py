from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)


def init_db():
    """Mengimpor semua model agar terdaftar di SQLModel metadata sebelum create_all."""
    from app.models.item import Item  # noqa: F401
    from app.models.user import User  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency injection untuk database session."""
    with Session(engine) as session:
        yield session
