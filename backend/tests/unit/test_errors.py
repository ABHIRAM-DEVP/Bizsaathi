"""Unit tests for RFC 7807 problem details error handling."""

import logging

import pytest
from fastapi import APIRouter, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import NotFoundError
from app.core.logging import StructuredJsonFormatter
from app.main import app, unhandled_exception_handler

test_router = APIRouter(prefix="/v1/test-errors")


class DummyInput(BaseModel):
    name: str
    age: int


@test_router.post("/validate")
async def dummy_validate(body: DummyInput) -> dict[str, str]:
    return {"status": "validated"}


@test_router.get("/custom-not-found")
async def dummy_not_found() -> None:
    raise NotFoundError(detail="Custom item not found in repository")


app.include_router(test_router)
client = TestClient(app)


def test_unknown_route_returns_problem_json() -> None:
    """Unknown path returns 404 problem JSON with request_id."""
    response = client.get("/v1/this-path-does-not-exist")
    assert response.status_code == 404
    data = response.json()
    assert data["type"] == "https://bizsaathi.dev/problems/not-found"
    assert data["status"] == 404
    assert "request_id" in data
    assert data["request_id"].startswith("req_")
    assert response.headers.get("X-Request-ID") == data["request_id"]


def test_validation_error_returns_problem_json() -> None:
    """Invalid input returns 422 problem JSON with field error breakdown."""
    response = client.post("/v1/test-errors/validate", json={"name": "test", "age": "not-a-number"})
    assert response.status_code == 422
    data = response.json()
    assert data["type"] == "https://bizsaathi.dev/problems/validation-error"
    assert data["status"] == 422
    assert "request_id" in data
    assert "errors" in data
    assert any(e["field"] == "age" for e in data["errors"])


def test_domain_exception_returns_problem_json() -> None:
    """Domain exception (NotFoundError) returns mapped problem JSON."""
    response = client.get("/v1/test-errors/custom-not-found")
    assert response.status_code == 404
    data = response.json()
    assert data["type"] == "https://bizsaathi.dev/problems/not-found"
    assert data["title"] == "Resource not found"
    assert data["detail"] == "Custom item not found in repository"
    assert "request_id" in data


@pytest.mark.anyio
async def test_unhandled_exception_log_does_not_include_exception_message(caplog) -> None:
    request = Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "server": ("test", 80),
            "client": ("test", 1),
        }
    )
    request.state.request_id = "req_test"
    secret_marker = "database-password-must-not-leak"
    caplog.set_level(logging.ERROR, logger="bizsaathi")

    response = await unhandled_exception_handler(request, RuntimeError(secret_marker))

    assert response.status_code == 500
    assert secret_marker not in caplog.text
    assert caplog.records[-1].exception_type == "RuntimeError"
    formatted_log = StructuredJsonFormatter().format(caplog.records[-1])
    assert '"exception_type": "RuntimeError"' in formatted_log
    assert secret_marker not in formatted_log
