"""API routers package."""

from app.routers.approvals import router as approvals_router
from app.routers.health import router as health_router
from app.routers.jobs import router as jobs_router
from app.routers.posts import router as posts_router
from app.routers.products import router as products_router
from app.routers.uploads import router as uploads_router

__all__ = [
    "health_router",
    "jobs_router",
    "uploads_router",
    "products_router",
    "approvals_router",
    "posts_router",
]
