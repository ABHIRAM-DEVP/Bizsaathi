"""Unit tests for EP-H01 and EP-H02 health endpoints and request ID tracking."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_eph01() -> None:
    """EP-H01 GET /v1/health returns 200 with {status: 'ok'}."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


def test_health_ready_eph02(monkeypatch) -> None:
    """EP-H02 GET /v1/health/ready verifies PostgreSQL before returning ready."""
    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, statement):
            assert str(statement) == "SELECT 1"

    class Engine:
        def connect(self):
            return Connection()

        def dispose(self):
            pass

    monkeypatch.setattr("app.routers.health.get_sync_engine", Engine)
    response = client.get("/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["db"] == "ok"
    assert "X-Request-ID" in response.headers


def test_request_id_echo() -> None:
    """Incoming X-Request-ID header is echoed back on response."""
    custom_id = "req_custom_trace_12345"
    response = client.get("/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch) -> None:
    """The API must not report ready when PostgreSQL cannot be reached."""
    from sqlalchemy.exc import OperationalError

    class Connection:
        def __enter__(self):
            raise OperationalError("SELECT 1", {}, Exception("offline"))

        def __exit__(self, *_args):
            return None

    class Engine:
        def connect(self):
            return Connection()

        def dispose(self):
            pass

    monkeypatch.setattr("app.routers.health.get_sync_engine", Engine)
    response = client.get("/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "unready"
    assert response.json()["checks"]["db"] == "unreachable"


def test_api_allows_configured_frontend_origin() -> None:
    """Browser preflight is allowed from the local frontend origin only."""
    response = client.options(
        "/v1/posts",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
