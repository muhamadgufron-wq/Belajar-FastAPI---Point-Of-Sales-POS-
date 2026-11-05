from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.routers import (
    auth_router,
    category_router,
    product_router,
    transaction_router,
    report_router,
    stock_in_router,
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

# Konfigurasi CORS (Cross-Origin Resource Sharing)
# Whitelist domain frontend yang diizinkan mengakses backend
origins = [
    "http://localhost:5173",  # Frontend Vite / React / Vue
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # Frontend Next.js
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrasi Router
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(category_router)
app.include_router(transaction_router)
app.include_router(report_router)
app.include_router(stock_in_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "app": "Warung Umi Neneng - POS API",
        "status": "online",
        "docs_url": "/docs",
    }
