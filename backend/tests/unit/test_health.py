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


def test_health_ready_eph02() -> None:
    """EP-H02 GET /v1/health/ready returns 200 with checks."""
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
