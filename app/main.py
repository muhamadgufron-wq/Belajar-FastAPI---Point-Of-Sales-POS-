from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import init_db
from app.routers import (
    auth_router,
    category_router,
    product_router,
    transaction_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inisialisasi tabel database saat server start
    init_db()
    yield


app = FastAPI(
    title="Point Of Sales API",
    description="Backend REST API Point of Sale (POS) dengan FastAPI, SQLModel, dan PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)

# Registrasi Router
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(category_router)
app.include_router(transaction_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "app": "Warung Umi Neneng - POS API",
        "status": "online",
        "docs_url": "/docs",
    }
