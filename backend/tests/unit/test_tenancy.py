"""Unit tests for tenancy and authentication dependency."""

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.tenancy import AuthContext, require_tenant
from app.main import app

tenancy_router = APIRouter(prefix="/v1/test-tenancy")


@tenancy_router.get("/protected")
async def protected_endpoint(ctx: AuthContext = Depends(require_tenant)) -> dict[str, str]:
    return {
        "business_id": str(ctx.business_id),
        "user_id": str(ctx.user_id),
        "role": ctx.role,
        "is_dev_stub": str(ctx.is_dev_stub),
    }


app.include_router(tenancy_router)
client = TestClient(app)


def test_dev_stub_in_dev_env() -> None:
    """In dev/test environment, unauthenticated request returns labelled dev stub."""
    original_env = settings.ENV
    try:
        settings.ENV = "dev"
        response = client.get("/v1/test-tenancy/protected")
        assert response.status_code == 200
        data = response.json()
        assert data["is_dev_stub"] == "True"
        assert data["role"] == "owner"
    finally:
        settings.ENV = original_env


def test_unauthenticated_in_prod_env() -> None:
    """In prod environment, unauthenticated request returns 401 Problem JSON."""
    original_env = settings.ENV
    try:
        settings.ENV = "prod"
        response = client.get("/v1/test-tenancy/protected")
        assert response.status_code == 401
        data = response.json()
        assert data["type"] == "https://bizsaathi.dev/problems/unauthenticated"
        assert data["status"] == 401
        assert "request_id" in data
    finally:
        settings.ENV = original_env
