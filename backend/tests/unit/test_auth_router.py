"""Tests for development-only local account registration and logout."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import settings
from app.main import app
from app.models.base import get_db
from app.models.domain import AppUser, Business

SIGNING_SECRET = "local-test-signing-secret-with-at-least-32-bytes"


class FakeSession:
    def __init__(self) -> None:
        self.records: list[object] = []

    def add_all(self, records: list[object]) -> None:
        self.records.extend(records)

    def flush(self) -> None:
        pass


@pytest.fixture
def local_auth_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, FakeSession]]:
    db = FakeSession()
    monkeypatch.setattr(settings, "ENV", "dev")
    monkeypatch.setattr(settings, "SECRET_KEY", SecretStr(SIGNING_SECRET))

    def override_get_db() -> Iterator[FakeSession]:
        yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)
    yield TestClient(app), db


def test_registration_creates_isolated_business_and_owner_session(
    local_auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, db = local_auth_client

    response = client.post(
        "/v1/auth/local/register",
        json={
            "owner_name": "Asha Rao",
            "business_name": "Asha's Toys",
            "email": "asha@example.com",
            "password": "secure-local-password",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["display_name"] == "Asha Rao"
    assert body["user"]["role"] == "owner"
    assert body["business"]["name"] == "Asha's Toys"
    assert body["business"]["slug"].startswith("asha-s-toys-")
    assert len(db.records) == 2
    business, user = db.records
    assert isinstance(business, Business)
    assert isinstance(user, AppUser)
    assert user.business_id == business.id
    assert user.phone_e164 is None
    assert user.identity_type == "local_dev"
    assert user.local_email == "asha@example.com"
    assert user.local_password_hash
    assert business.slug.startswith("asha-s-toys-")

    cookie = response.headers["set-cookie"]
    assert "bizsaathi_session=" in cookie
    assert "httponly" in cookie.lower()
    assert "samesite=strict" in cookie.lower()
    assert "path=/" in cookie.lower()
    assert "max-age=34560000" in cookie.lower()
    assert "expires=" not in cookie.lower()
    assert "expires_at" not in body
    assert "bizsaathi_session" not in body


def test_local_registration_is_forbidden_outside_development(
    local_auth_client: tuple[TestClient, FakeSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, db = local_auth_client
    monkeypatch.setattr(settings, "ENV", "prod")

    response = client.post(
        "/v1/auth/local/register",
        json={
            "owner_name": "Asha Rao",
            "business_name": "Asha Toys",
            "email": "asha@example.com",
            "password": "secure-local-password",
        },
    )

    assert response.status_code == 403
    assert db.records == []


def test_local_login_is_forbidden_outside_development(
    local_auth_client: tuple[TestClient, FakeSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, db = local_auth_client
    monkeypatch.setattr(settings, "ENV", "prod")

    response = client.post(
        "/v1/auth/local/login",
        json={"email": "asha@example.com", "password": "secure-local-password"},
    )

    assert response.status_code == 403
    assert db.records == []


def test_registration_rejects_unexpected_credentials(
    local_auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, db = local_auth_client

    response = client.post(
        "/v1/auth/local/register",
        json={
            "owner_name": "Asha Rao",
            "business_name": "Asha Toys",
            "email": "asha@example.com",
            "password": "secure-local-password",
            "unexpected": "not-accepted",
        },
    )

    assert response.status_code == 422
    assert db.records == []


def test_logout_clears_session_cookie(
    local_auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = local_auth_client

    response = client.post("/v1/auth/logout")

    assert response.status_code == 204
    assert "bizsaathi_session=" in response.headers["set-cookie"]
    assert "max-age=0" in response.headers["set-cookie"].lower()
