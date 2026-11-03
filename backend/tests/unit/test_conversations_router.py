from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.tenancy import AuthContext, get_auth_context
from app.main import app
from app.models.base import get_db


class FakeResult:
    def scalar_one_or_none(self) -> None:
        return None


class FakeSession:
    statement = None

    def execute(self, statement: object) -> FakeResult:
        self.statement = statement
        return FakeResult()


@pytest.fixture
def inbox_client() -> Iterator[tuple[TestClient, FakeSession]]:
    db = FakeSession()

    def override_db() -> Iterator[FakeSession]:
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        yield TestClient(app), db
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_auth_context, None)


def test_conversation_lookup_scopes_by_authenticated_tenant(
    inbox_client: tuple[TestClient, FakeSession],
) -> None:
    client, db = inbox_client
    tenant_id = uuid4()
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(
        business_id=tenant_id,
        user_id=uuid4(),
        role="owner",
    )

    response = client.get(f"/v1/conversations/{uuid4()}")

    assert response.status_code == 404
    assert db.statement is not None
    compiled = str(db.statement)
    assert "conversation.business_id" in compiled
    assert "conversation.id" in compiled


def test_operator_cannot_seed_demo_inbox(
    inbox_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = inbox_client
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(
        business_id=uuid4(),
        user_id=uuid4(),
        role="operator",
    )

    response = client.post("/v1/conversations/demo/start")

    assert response.status_code == 403


def test_operator_cannot_read_business_profile(
    inbox_client: tuple[TestClient, FakeSession],
) -> None:
    client, db = inbox_client
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(
        business_id=uuid4(),
        user_id=uuid4(),
        role="operator",
    )

    response = client.get("/v1/businesses/me")

    assert response.status_code == 403
    assert db.statement is None


def test_public_chat_requires_customer_account(
    inbox_client: tuple[TestClient, FakeSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = inbox_client
    origin = settings.CORS_ALLOWED_ORIGINS.split(",")[0].strip()
    monkeypatch.setattr("app.routers.public_store.check_public_rate_limit", lambda *args, **kwargs: None)

    response = client.post(
        "/v1/public/stores/example-store/sessions",
        headers={"Origin": origin, "X-Customer-Request": "1"},
    )

    assert response.status_code == 401


def test_public_chat_mutations_reject_untrusted_browser_origins(
    inbox_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = inbox_client

    response = client.post("/v1/public/stores/example-store/sessions")

    assert response.status_code == 403
