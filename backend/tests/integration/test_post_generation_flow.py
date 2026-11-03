"""Post-generation API flow with a rollback-only synthetic catalog fixture."""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.base import get_db, get_sync_engine
from app.models.domain import Approval, AppUser, Business, Proposal


def test_catalog_to_mock_post_flow_is_tenant_scoped_and_rollback_only(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MEDIA_STORAGE_PATH", str(tmp_path))
    engine = get_sync_engine()
    connection = engine.connect()
    transaction = connection.begin()
    business_id = uuid4()
    user_id = uuid4()
    test_session = Session(bind=connection, join_transaction_mode="create_savepoint")
    test_session.add(Business(id=business_id, name="Synthetic Demo Shop", slug=f"demo-{business_id.hex}"))
    test_session.add(
        AppUser(
            id=user_id,
            business_id=business_id,
            phone_e164=f"+1555{business_id.int % 100000000:08d}",
            role="owner",
            display_name="Synthetic Test Owner",
        )
    )
    test_session.commit()
    test_session.close()

    def override_get_db():
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    headers = {"X-Business-ID": str(business_id), "X-User-ID": str(user_id)}
    try:
        with TestClient(app) as client:
            product_response = client.post(
                "/v1/products",
                headers=headers,
                json={
                    "name": "Synthetic Sample Toy",
                    "description": "Owner-confirmed synthetic description",
                    "price_inr": "1.00",
                    "stock": 1,
                },
            )
            assert product_response.status_code == 201
            product = product_response.json()
            clear_description_response = client.patch(
                f"/v1/products/{product['id']}",
                headers={**headers, "If-Match": str(product["version"])},
                json={"description": None},
            )
            assert clear_description_response.status_code == 200
            product = clear_description_response.json()
            assert product["description"] is None

            dashboard_response = client.get("/v1/dashboard", headers=headers)
            assert dashboard_response.status_code == 200
            dashboard = dashboard_response.json()
            assert dashboard["pending_approvals"] == 0
            assert dashboard["open_escalations"] == 0
            assert dashboard["low_stock"] == [
                {
                    "id": product["id"],
                    "sku": product["sku"],
                    "name": product["name"],
                    "price_inr": "1.00",
                    "status": "active",
                    "stock_total": 1,
                    "thumbnail_url": None,
                }
            ]

            proposal_id = uuid4()
            approval_id = uuid4()
            proposal_payload = {
                "fields": {"name": "Approved Synthetic Toy", "price_inr": "2.00", "stock": 2},
                "seller_confirmed_fields": ["price_inr", "stock"],
            }
            test_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            test_session.add(
                Proposal(
                    id=proposal_id,
                    business_id=business_id,
                    root_id=uuid4(),
                    type="product_create",
                    version=1,
                    payload=proposal_payload,
                    status="pending",
                )
            )
            test_session.flush()
            test_session.add(
                Approval(
                    id=approval_id,
                    business_id=business_id,
                    proposal_id=proposal_id,
                    type="product_create",
                    status="pending",
                    warnings=[],
                    risk="low",
                    side_effect={"description": "Create confirmed catalog product", "reversible": True},
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                )
            )
            test_session.commit()
            test_session.close()

            pending_response = client.get("/v1/approvals?status_filter=pending", headers=headers)
            assert pending_response.status_code == 200
            pending = pending_response.json()
            approval = next(item for item in pending if item["id"] == str(approval_id))
            assert approval["diff"] == proposal_payload
            approve_response = client.post(
                f"/v1/approvals/{approval_id}/approve",
                headers={**headers, "Idempotency-Key": f"{approval_id}:1:approve"},
                json={"expected_proposal_version": 1},
            )
            assert approve_response.status_code == 200
            assert approve_response.json()["execution"]["status"] == "succeeded"
            remaining_approvals = client.get("/v1/approvals?status_filter=pending", headers=headers)
            assert remaining_approvals.status_code == 200
            assert all(item["id"] != str(approval_id) for item in remaining_approvals.json())

            upload_ticket_response = client.post(
                "/v1/uploads",
                headers=headers,
                json={
                    "kind": "photo",
                    "filename": "toy.jpg",
                    "mime": "image/jpeg",
                    "size_bytes": 3,
                    "product_id": product["id"],
                },
            )
            assert upload_ticket_response.status_code == 201
            upload_ticket = upload_ticket_response.json()
            upload_url = urlsplit(upload_ticket["upload_url"])
            upload_response = client.put(
                upload_ticket["upload_url"],
                content=b"\xff\xd8\xff",
                headers={"Content-Type": "image/jpeg"},
            )
            assert upload_response.status_code == 204
            image_response = client.get(
                f"/v1/uploads/products/{product['id']}/image",
                headers=headers,
            )
            assert image_response.status_code == 200
            assert image_response.content == b"\xff\xd8\xff"
            assert image_response.headers["cache-control"] == "private, no-store"
            assert upload_url.path.endswith(f"/uploads/{upload_ticket['media_id']}/content")

            draft_response = client.post(
                f"/v1/posts/generate/{product['id']}",
                headers=headers,
                json={"channel": "instagram", "language": "en"},
            )
            assert draft_response.status_code == 201
            draft = draft_response.json()
            assert draft["provenance"]["mode"] == "mock"
            assert "Synthetic Sample Toy" in draft["text"]
            assert draft["claims"][0]["verdict"] == "unverified"
            assert all(claim["evidence_ids"] for claim in draft["claims"][1:])

            check_response = client.post(
                f"/v1/posts/{draft['id']}/claim-check",
                headers=headers,
                json={"version": draft["version"]},
            )
            assert check_response.status_code == 200
            assert check_response.json()["overall"] == "needs_owner"

            edit_response = client.patch(
                f"/v1/posts/{draft['id']}",
                headers={**headers, "If-Match": str(draft["version"])},
                json={"text": "This toy is completely safe for every infant."},
            )
            assert edit_response.status_code == 200
            edited_draft = edit_response.json()
            empty_check_response = client.post(
                f"/v1/posts/{draft['id']}/claim-check",
                headers=headers,
                json={"version": edited_draft["version"]},
            )
            assert empty_check_response.status_code == 200
            assert empty_check_response.json()["claims"] == []
            assert empty_check_response.json()["overall"] == "needs_owner"
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override
        transaction.rollback()
        connection.close()
