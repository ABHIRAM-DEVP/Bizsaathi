"""PostgreSQL integration coverage for local-account tenancy."""

from collections.abc import Iterator
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.base import get_db
from app.models.domain import Business
from app.repositories.product import ProductRepository

SIGNING_SECRET = "local-test-signing-secret-with-at-least-32-bytes"


def test_registered_tenant_cannot_read_another_tenants_product(db_engine, monkeypatch) -> None:
    connection = db_engine.connect()
    transaction = connection.begin()

    def override_get_db() -> Iterator[Session]:
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    monkeypatch.setattr(settings, "ENV", "dev")
    monkeypatch.setattr(settings, "SECRET_KEY", SecretStr(SIGNING_SECRET))
    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)

    try:
        with TestClient(app) as client:
            previous_registration = client.post(
                "/v1/auth/local/register",
                json={
                    "owner_name": "Previous Owner",
                    "business_name": "Previous Local Shop",
                    "email": "previous@example.com",
                    "password": "previous-account-pass",
                },
            )
            assert previous_registration.status_code == 201
            previous_business_id = previous_registration.json()["business"]["id"]

            registration = client.post(
                "/v1/auth/local/register",
                json={
                    "owner_name": "Integration Owner",
                    "business_name": "Integration Shop",
                    "email": "owner@example.com",
                    "password": "integration-account-pass",
                },
            )
            assert registration.status_code == 201
            registered_business_id = registration.json()["business"]["id"]
            registered_business_slug = registration.json()["business"]["slug"]
            assert registered_business_id != previous_business_id

            profile_response = client.get(
                "/v1/businesses/me",
                headers={"X-Demo-Account": "demo-owner"},
            )
            assert profile_response.status_code == 200
            assert profile_response.json()["id"] == registered_business_id
            assert profile_response.json()["slug"] == registered_business_slug

            client.cookies.clear()
            invalid_login = client.post(
                "/v1/auth/local/login",
                json={"email": "owner@example.com", "password": "wrong-password"},
            )
            assert invalid_login.status_code == 401
            assert "bizsaathi_session" not in client.cookies

            login = client.post(
                "/v1/auth/local/login",
                json={"email": " OWNER@EXAMPLE.COM ", "password": "integration-account-pass"},
            )
            assert login.status_code == 200
            assert login.json()["business"]["id"] == registered_business_id
            assert "bizsaathi_session" in client.cookies
            profile_after_login = client.get(
                "/v1/businesses/me",
                headers={"X-Demo-Account": "demo-owner"},
            )
            assert profile_after_login.status_code == 200
            assert profile_after_login.json()["id"] == registered_business_id

            copied_session_token = client.cookies.get("bizsaathi_session")
            assert copied_session_token is not None
            logout = client.post("/v1/auth/logout")
            assert logout.status_code == 204
            client.cookies.set("bizsaathi_session", copied_session_token)
            revoked_session = client.get(
                "/v1/businesses/me",
                headers={"X-Demo-Account": "demo-owner"},
            )
            assert revoked_session.status_code == 401

            client.cookies.clear()
            missing_session_response = client.get(
                "/v1/businesses/me",
                headers={
                    "X-Demo-Account": "demo-owner",
                    "X-Local-Account-Required": "true",
                },
            )
            assert missing_session_response.status_code == 401

            other_business_id = uuid4()
            with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
                db.add(
                    Business(
                        id=other_business_id,
                        name="Other Tenant",
                        slug=f"other-tenant-{other_business_id.hex[:12]}",
                    )
                )
                db.flush()
                product = ProductRepository(session=db, business_id=other_business_id).create(
                    sku="OTHER-001",
                    name="Other tenant product",
                    price_inr=Decimal("100.00"),
                )
                product_id = product.id
                assert product.business_id == other_business_id
                db.commit()

            assert registered_business_id != str(other_business_id)
            response = client.get(f"/v1/products/{product_id}")

            assert response.status_code == 404
    finally:
        transaction.rollback()
        connection.close()
