from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.tenancy import AuthContext, get_auth_context
from app.main import app
from app.models.base import get_db


class FakeResult:
    def scalars(self) -> "FakeResult":
        return self

    def all(self) -> list[object]:
        return []


class FakeSession:
    statement: object | None = None

    def execute(self, statement: object) -> FakeResult:
        self.statement = statement
        return FakeResult()


@pytest.fixture
def orders_client() -> Iterator[tuple[TestClient, FakeSession]]:
    db = FakeSession()

    def override_db() -> Iterator[FakeSession]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(
        business_id=uuid4(),
        user_id=uuid4(),
        role="owner",
    )
    try:
        yield TestClient(app), db
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_auth_context, None)


def test_order_list_query_is_tenant_scoped(orders_client: tuple[TestClient, FakeSession]) -> None:
    client, db = orders_client

    response = client.get("/v1/orders")

    assert response.status_code == 200
    assert response.json() == []
    assert db.statement is not None
    assert "customer_order.business_id" in str(db.statement)


def test_order_list_rejects_unknown_status(orders_client: tuple[TestClient, FakeSession]) -> None:
    client, _ = orders_client

    response = client.get("/v1/orders?status=UNKNOWN")

    assert response.status_code == 422
