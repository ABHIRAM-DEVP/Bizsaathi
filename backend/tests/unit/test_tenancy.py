"""Unit tests for tenancy and authentication dependency."""

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import settings
from app.core.dev_sessions import create_dev_session_token
from app.core.tenancy import AuthContext, require_tenant
from app.main import app
from app.models.base import get_db
from app.models.domain import AppUser

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


class FakeResult:
    def __init__(self, value: AppUser | None) -> None:
        self.value = value

    def scalar_one_or_none(self) -> AppUser | None:
        return self.value


class FakeSession:
    user: AppUser | None = None

    def execute(self, _statement: object) -> FakeResult:
        return FakeResult(self.user)


@pytest.fixture(autouse=True)
def use_fake_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeSession]:
    db = FakeSession()
    client.cookies.clear()

    def override_get_db() -> Iterator[FakeSession]:
        yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)
    yield db
    client.cookies.clear()


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


def test_signed_dev_session_provides_its_active_persisted_tenant(
    monkeypatch: pytest.MonkeyPatch,
    use_fake_database: FakeSession,
) -> None:
    monkeypatch.setattr(settings, "ENV", "dev")
    monkeypatch.setattr(settings, "SECRET_KEY", SecretStr("local-test-signing-secret-with-at-least-32-bytes"))
    user_id = "00000000-0000-0000-0000-000000000021"
    business_id = "00000000-0000-0000-0000-000000000022"
    use_fake_database.user = AppUser(
        id=UUID(user_id),
        business_id=UUID(business_id),
        role="owner",
        display_name="Local Owner",
        identity_type="local_dev",
        local_session_version=0,
    )
    token = create_dev_session_token(
        user_id,
        business_id,
        "local-test-signing-secret-with-at-least-32-bytes",
    )

    client.cookies.set("bizsaathi_session", token)
    response = client.get("/v1/test-tenancy/protected")

    assert response.status_code == 200
    assert response.json() == {
        "business_id": business_id,
        "user_id": user_id,
        "role": "owner",
        "is_dev_stub": "False",
    }


def test_signed_dev_session_rejects_missing_persisted_identity(
    monkeypatch: pytest.MonkeyPatch,
    use_fake_database: FakeSession,
) -> None:
    monkeypatch.setattr(settings, "ENV", "dev")
    monkeypatch.setattr(settings, "SECRET_KEY", SecretStr("local-test-signing-secret-with-at-least-32-bytes"))
    token = create_dev_session_token(
        "00000000-0000-0000-0000-000000000021",
        "00000000-0000-0000-0000-000000000022",
        "local-test-signing-secret-with-at-least-32-bytes",
    )

    client.cookies.set("bizsaathi_session", token)
    response = client.get(
        "/v1/test-tenancy/protected",
        headers={"X-Demo-Account": "demo-owner"},
    )

    assert response.status_code == 401


def test_invalid_dev_session_does_not_fall_back_to_demo_headers(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENV", "dev")

    client.cookies.set("bizsaathi_session", "not-a-signed-session")
    response = client.get(
        "/v1/test-tenancy/protected",
        headers={"X-Demo-Account": "demo-owner"},
    )

    assert response.status_code == 401


def test_missing_local_session_returns_sign_in_message_not_cookie_error() -> None:
    response = client.get(
        "/v1/test-tenancy/protected",
        headers={"X-Local-Account-Required": "true"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Sign in to your local account to continue."


def test_logout_revokes_copied_local_session(
    monkeypatch: pytest.MonkeyPatch,
    use_fake_database: FakeSession,
) -> None:
    monkeypatch.setattr(settings, "ENV", "dev")
    monkeypatch.setattr(settings, "SECRET_KEY", SecretStr("local-test-signing-secret-with-at-least-32-bytes"))
    user_id = UUID("00000000-0000-0000-0000-000000000031")
    business_id = UUID("00000000-0000-0000-0000-000000000032")
    use_fake_database.user = AppUser(
        id=user_id,
        business_id=business_id,
        role="owner",
        display_name="Local Owner",
        identity_type="local_dev",
        local_session_version=0,
    )
    token = create_dev_session_token(
        user_id,
        business_id,
        "local-test-signing-secret-with-at-least-32-bytes",
        session_version=0,
    )
    client.cookies.set("bizsaathi_session", token)

    logout_response = client.post("/v1/auth/logout")

    assert logout_response.status_code == 204
    client.cookies.set("bizsaathi_session", token)
    protected_response = client.get("/v1/test-tenancy/protected")

    assert protected_response.status_code == 401
