from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.errors import UnauthenticatedError
from app.core.tenancy import AuthContext, get_auth_context
from app.main import app
from app.models.base import get_db


class FakeResult:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows

    def all(self) -> list[tuple]:
        return self._rows

    def one(self) -> tuple:
        return self._rows[0]


class FakeSession:
    def __init__(self) -> None:
        self.statements: list[object] = []

    def execute(self, statement: object) -> FakeResult:
        self.statements.append(statement)
        if len(self.statements) == 1:
            return FakeResult(
                [
                    ("succeeded", 2, 3),
                    ("failed", 1, 1),
                    ("awaiting_approval", 1, 0),
                ]
            )
        if len(self.statements) == 2:
            return FakeResult([("draft_post", 3, 1, 45.0, 80.0)])
        return FakeResult([(100.0, 500.0)])


@pytest.fixture
def metrics_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, FakeSession]]:
    db = FakeSession()

    def override_db() -> Iterator[FakeSession]:
        yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_db)
    monkeypatch.setitem(
        app.dependency_overrides,
        get_auth_context,
        lambda: AuthContext(business_id=uuid4(), user_id=uuid4(), role="owner"),
    )
    yield TestClient(app), db


def test_agent_metrics_return_measured_tenant_scoped_values(
    metrics_client: tuple[TestClient, FakeSession],
) -> None:
    client, db = metrics_client

    response = client.get("/v1/metrics/agents?days=30")

    assert response.status_code == 200
    body = response.json()
    assert body["total_jobs"] == 4
    assert body["jobs_by_status"]["succeeded"] == 2
    assert body["jobs_by_status"]["awaiting_approval"] == 1
    assert body["success_rate"] == pytest.approx(2 / 3)
    assert body["model_usage"] == {
        "model_calls": 4,
        "input_tokens": None,
        "output_tokens": None,
        "estimated_cost_usd": None,
    }
    assert body["workflow_latency_ms"] == {"p50": 100.0, "p95": 500.0}
    assert body["nodes"] == [
        {
            "node": "draft_post",
            "execution_count": 3,
            "error_count": 1,
            "p50_ms": 45.0,
            "p95_ms": 80.0,
        }
    ]
    assert len(db.statements) == 3
    assert all("business_id" in str(statement) for statement in db.statements)


def test_agent_metrics_allow_operator_read_access(
    metrics_client: tuple[TestClient, FakeSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, db = metrics_client
    monkeypatch.setitem(
        app.dependency_overrides,
        get_auth_context,
        lambda: AuthContext(business_id=uuid4(), user_id=uuid4(), role="operator"),
    )

    response = client.get("/v1/metrics/agents")

    assert response.status_code == 200
    assert len(db.statements) == 3


def test_agent_metrics_reject_public_access(
    metrics_client: tuple[TestClient, FakeSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, db = metrics_client
    monkeypatch.setitem(
        app.dependency_overrides,
        get_auth_context,
        lambda: AuthContext(business_id=uuid4(), user_id=uuid4(), role="public"),
    )

    response = client.get("/v1/metrics/agents")

    assert response.status_code == 403
    assert not db.statements


def test_agent_metrics_require_authentication(
    metrics_client: tuple[TestClient, FakeSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, db = metrics_client

    def reject_auth() -> AuthContext:
        raise UnauthenticatedError(detail="Authentication required")

    monkeypatch.setitem(app.dependency_overrides, get_auth_context, reject_auth)

    response = client.get("/v1/metrics/agents")

    assert response.status_code == 401
    assert not db.statements


def test_agent_metrics_validate_window_days(
    metrics_client: tuple[TestClient, FakeSession],
) -> None:
    client, db = metrics_client

    response = client.get("/v1/metrics/agents?days=0")

    assert response.status_code == 422
    assert not db.statements
