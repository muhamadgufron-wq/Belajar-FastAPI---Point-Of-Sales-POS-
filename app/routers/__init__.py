from app.routers.auth import router as auth_router
from app.routers.category import router as category_router
from app.routers.product import router as product_router
from app.routers.transaction import router as transaction_router
from app.routers.report import router as report_router

__all__ = [
    "auth_router",
    "product_router",
    "category_router",
    "transaction_router",
    "report_router",
]
