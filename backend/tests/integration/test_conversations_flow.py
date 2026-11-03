"""PostgreSQL-backed owner inbox and synthetic demo flow."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import bcrypt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.mock import MockModelClient
from app.core.config import settings
from app.main import app
from app.models.base import get_db
from app.models.domain import (
    Business,
    Conversation,
    Evidence,
    Message,
    Policy,
    Product,
    ProductVariant,
    PublicSession,
)
from app.routers import public_store
from app.services import customer_replies


def test_demo_inbox_is_idempotent_grounded_and_never_sends(
    db_engine,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "ENV", "test")
    monkeypatch.setattr(
        customer_replies,
        "get_model_client",
        lambda **kwargs: MockModelClient(),
    )
    connection = db_engine.connect()
    transaction = connection.begin()
    business_id = uuid4()
    user_id = uuid4()
    fixture_session = Session(bind=connection, join_transaction_mode="create_savepoint")
    product = Product(
        business_id=business_id,
        sku=f"TEST-{uuid4().hex[:8].upper()}",
        name="Synthetic stacking toy",
        description="A test-only product.",
        price_inr="749.00",
        field_sources={"price_inr": {"source": "confirmed"}},
        attributes={"material": "cotton"},
        status="active",
        version=1,
    )
    second_product = Product(
        business_id=business_id,
        sku=f"TEST-{uuid4().hex[:8].upper()}",
        name="Synthetic wooden puzzle",
        description="A wooden puzzle for creative play.",
        price_inr="599.00",
        field_sources={"price_inr": {"source": "confirmed"}},
        attributes={"material": "wood"},
        status="active",
        version=1,
    )
    fixture_session.add(
        Business(
            id=business_id,
            name="Synthetic Shop",
            slug=f"test-{business_id.hex}",
            description="A family shop specializing in handwoven cotton goods.",
        )
    )
    fixture_session.add(
        Policy(
            business_id=business_id,
            kind="returns",
            version=1,
            body="Returns are accepted within 7 days if the item is unused.",
        )
    )
    fixture_session.add_all([product, second_product])
    fixture_session.flush()
    fixture_session.add(
        ProductVariant(
            business_id=business_id,
            product_id=product.id,
            color="Blue",
            size=None,
            stock=7,
            stock_version=1,
        )
    )
    fixture_session.add(
        ProductVariant(
            business_id=business_id,
            product_id=second_product.id,
            color="Natural",
            size=None,
            stock=4,
            stock_version=1,
        )
    )
    fixture_session.commit()
    product_name = product.name
    product_description = product.description
    second_product_name = second_product.name
    second_product_description = second_product.description
    fixture_session.close()

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

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    headers = {"X-Business-ID": str(business_id), "X-User-ID": str(user_id)}
    try:
        test_ip = f"192.0.2.{business_id.int % 254 + 1}"
        origin = settings.CORS_ALLOWED_ORIGINS.split(",")[0].strip()
        customer_headers = {"Origin": origin, "X-Customer-Request": "1"}
        with TestClient(app, client=(test_ip, 50000), headers=customer_headers) as client:
            started = client.post("/v1/conversations/demo/start", headers=headers)
            assert started.status_code == 200
            conversations = started.json()["conversations"]
            assert len(conversations) == 3
            assert [item["status"] for item in conversations] == ["open", "open", "escalated"]
            assert conversations[0]["messages"][-1]["evidence_ids"]

            profile_response = client.get("/v1/businesses/me", headers=headers)
            assert profile_response.status_code == 200
            assert profile_response.json() == {
                "id": str(business_id),
                "name": "Synthetic Shop",
                "slug": f"test-{business_id.hex}",
            }

            repeated = client.post("/v1/conversations/demo/start", headers=headers)
            assert [item["id"] for item in repeated.json()["conversations"]] == [
                item["id"] for item in conversations
            ]

            simulated_customers = []
            for expected_name in ("Synthetic buyer 1", "Synthetic buyer 2", "Synthetic buyer 3"):
                simulation = client.post("/v1/conversations/demo/simulate", headers=headers)
                assert simulation.status_code == 201
                simulated_conversation = simulation.json()["conversation"]
                simulated_customers.append(simulated_conversation["customer_name"])
                latest_customer_message = next(
                    message
                    for message in reversed(simulated_conversation["messages"])
                    if message["sender"] == "customer"
                )
                assert (
                    product_name in latest_customer_message["text"]
                    and product_description in latest_customer_message["text"]
                ) or (
                    second_product_name in latest_customer_message["text"]
                    and second_product_description in latest_customer_message["text"]
                )
                assert expected_name == simulated_conversation["customer_name"]
            assert simulated_customers == [
                "Synthetic buyer 1",
                "Synthetic buyer 2",
                "Synthetic buyer 3",
            ]

            registration = client.post(
                "/v1/public/customer-accounts/register",
                json={
                    "email": f"buyer-{business_id.hex}@example.test",
                    "display_name": "Synthetic customer",
                    "password": "Synthetic-test-password-2026",
                },
            )
            assert registration.status_code == 201
            customer = registration.json()
            suspended_business_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            suspended_business = suspended_business_session.get(Business, business_id)
            assert suspended_business is not None
            suspended_business.status = "suspended"
            suspended_business_session.commit()
            suspended_business_session.close()
            assert client.get(f"/v1/public/stores/test-{business_id.hex}").status_code == 404
            assert client.post(f"/v1/public/stores/test-{business_id.hex}/sessions").status_code == 404
            active_business_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            active_business = active_business_session.get(Business, business_id)
            assert active_business is not None
            active_business.status = "active"
            active_business_session.commit()
            active_business_session.close()

            invalid_login = client.post(
                "/v1/public/customer-accounts/login",
                json={
                    "email": customer["email"],
                    "password": "incorrect-synthetic-password",
                },
            )
            assert invalid_login.status_code == 401
            public_session_response = client.post(
                f"/v1/public/stores/test-{business_id.hex}/sessions",
            )
            assert public_session_response.status_code == 201
            public_session_data = public_session_response.json()
            assert "session_token" not in public_session_data
            assert public_session_data["messages"] == []

            customer_message_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "Can you describe the Synthetic stacking toy?"},
            )
            assert customer_message_response.status_code == 202
            customer_reply = customer_message_response.json()["assistant_message"]
            assert product.description in customer_reply["text"]
            assert customer_reply["evidence_ids"]

            followup_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "What about its price?"},
            )
            assert followup_response.status_code == 202
            followup_reply = followup_response.json()["assistant_message"]
            assert "Synthetic stacking toy" in followup_reply["text"]
            assert "₹749.00" in followup_reply["text"]
            assert followup_reply["evidence_ids"]

            recommendation_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "Can you recommend a cotton product?"},
            )
            assert recommendation_response.status_code == 202
            recommendation_reply = recommendation_response.json()["assistant_message"]
            assert "Synthetic stacking toy" in recommendation_reply["text"]
            assert "material: cotton" in recommendation_reply["text"]
            assert len(recommendation_reply["evidence_ids"]) >= 5

            shop_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "What does this shop sell?"},
            )
            assert shop_response.status_code == 202
            shop_reply = shop_response.json()["assistant_message"]
            assert "Synthetic Shop" in shop_reply["text"]
            assert "handwoven cotton goods" in shop_reply["text"]
            assert len(shop_reply["evidence_ids"]) == 2

            policy_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "What is your return policy?"},
            )
            assert policy_response.status_code == 202
            policy_reply = policy_response.json()["assistant_message"]
            assert "Returns are accepted within 7 days" in policy_reply["text"]
            assert len(policy_reply["evidence_ids"]) == 1

            all_products_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "What all products do you have?"},
            )
            assert all_products_response.status_code == 202
            all_products_reply = all_products_response.json()["assistant_message"]
            assert "Synthetic stacking toy" in all_products_reply["text"]
            assert "Synthetic wooden puzzle" in all_products_reply["text"]
            assert "₹749.00" in all_products_reply["text"]
            assert "₹599.00" in all_products_reply["text"]
            assert len(all_products_reply["evidence_ids"]) == 4

            generic_price_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "What is the price?"},
            )
            assert generic_price_response.status_code == 202
            generic_price_reply = generic_price_response.json()["assistant_message"]
            assert "Synthetic stacking toy" in generic_price_reply["text"]
            assert "Synthetic wooden puzzle" in generic_price_reply["text"]
            assert len(generic_price_reply["evidence_ids"]) == 4

            jeans_product = Product(
                business_id=business_id,
                sku=f"TEST-{uuid4().hex[:8].upper()}",
                name="Classic denim jeans",
                description="Straight-fit denim jeans.",
                price_inr="1499.00",
                field_sources={"price_inr": {"source": "confirmed"}},
                attributes={"material": "denim"},
                status="active",
                version=1,
            )
            fixture_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            fixture_session.add(jeans_product)
            fixture_session.flush()
            fixture_session.add(
                ProductVariant(
                    business_id=business_id,
                    product_id=jeans_product.id,
                    color="Blue",
                    size="M",
                    stock=6,
                    stock_version=1,
                )
            )
            fixture_session.commit()
            fixture_session.close()

            bare_product_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "jeans"},
            )
            assert bare_product_response.status_code == 202
            bare_product_reply = bare_product_response.json()["assistant_message"]
            assert "Classic denim jeans" in bare_product_reply["text"]
            assert "₹1499.00" in bare_product_reply["text"]
            assert bare_product_reply["evidence_ids"]

            jeans_price_response = client.post(
                f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                json={"text": "prices of jeans"},
            )
            assert jeans_price_response.status_code == 202
            jeans_price_reply = jeans_price_response.json()["assistant_message"]
            assert "Classic denim jeans" in jeans_price_reply["text"]
            assert "₹1499.00" in jeans_price_reply["text"]
            assert jeans_price_reply["evidence_ids"]

            evidence_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            evidence_rows = evidence_session.query(Evidence).filter(
                Evidence.id.in_(shop_reply["evidence_ids"] + policy_reply["evidence_ids"])
            ).all()
            evidence_session.close()
            assert {evidence.source_kind for evidence in evidence_rows} == {"business", "policy"}

            resumed_session = client.post(
                f"/v1/public/stores/test-{business_id.hex}/sessions",
            )
            assert resumed_session.status_code == 201
            assert resumed_session.json()["session_id"] == public_session_data["session_id"]
            assert len(resumed_session.json()["messages"]) == 18

            owner_inbox = client.get("/v1/conversations", headers=headers)
            customer_conversation = next(
                item for item in owner_inbox.json()["items"]
                if item["customer_name"] == customer["display_name"]
            )
            assert customer_conversation["unread_count"] == 9
            customer_conversation_detail = client.get(
                f"/v1/conversations/{customer_conversation['id']}",
                headers=headers,
            )
            assert customer_conversation_detail.status_code == 200
            assert customer_conversation_detail.json()["unread_count"] == 0
            expiring_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            expiring_record = expiring_session.get(
                PublicSession,
                UUID(public_session_data["session_id"]),
            )
            assert expiring_record is not None
            expiring_record.expires_at = datetime.now(UTC) - timedelta(minutes=1)
            expiring_session.commit()
            expiring_session.close()
            owner_reply = client.post(
                f"/v1/conversations/{customer_conversation['id']}/reply",
                headers=headers,
                json={"text": "A store owner is here to help."},
            )
            assert owner_reply.status_code == 201
            assert owner_reply.json()["delivery_status"] == "delivered"
            resumed_with_owner_reply = client.post(
                f"/v1/public/stores/test-{business_id.hex}/sessions",
            )
            assert resumed_with_owner_reply.status_code == 201
            assert resumed_with_owner_reply.json()["session_id"] == public_session_data["session_id"]
            assert datetime.fromisoformat(resumed_with_owner_reply.json()["expires_at"]) > datetime.now(UTC)
            assert any(
                message["sender"] == "owner"
                and message["text"] == "A store owner is here to help."
                for message in resumed_with_owner_reply.json()["messages"]
            )
            monkeypatch.setattr(
                public_store,
                "get_session",
                lambda: Session(bind=connection, join_transaction_mode="create_savepoint"),
            )
            stream_updates = public_store._read_session_updates(
                UUID(public_session_data["session_id"])
            )
            assert any(
                message["sender"] == "owner"
                and message["text"] == "A store owner is here to help."
                for message in stream_updates["messages"]
            )

            duplicate_registration = client.post(
                "/v1/public/customer-accounts/register",
                json={
                    "email": customer["email"],
                    "display_name": "Another customer",
                    "password": "Another-synthetic-password-2026",
                },
            )
            assert duplicate_registration.status_code == 409

            other_ip = f"198.51.100.{business_id.int % 254 + 1}"
            other_customer = TestClient(
                app,
                client=(other_ip, 50001),
                headers=customer_headers,
            )
            try:
                other_registration = other_customer.post(
                    "/v1/public/customer-accounts/register",
                    json={
                        "email": f"other-{business_id.hex}@example.test",
                        "display_name": "Other synthetic customer",
                        "password": "Other-synthetic-password-2026",
                    },
                )
                assert other_registration.status_code == 201
                cross_account_message = other_customer.post(
                    f"/v1/public/sessions/{public_session_data['session_id']}/messages",
                    json={"text": "What is the price?"},
                )
                assert cross_account_message.status_code == 401
            finally:
                other_customer.close()

            conversation_id = conversations[0]["id"]
            simulated = client.post(
                f"/v1/conversations/{conversation_id}/demo-messages",
                headers=headers,
                json={"text": "What is the price?"},
            )
            assert simulated.status_code == 201
            assert "₹749.00" in simulated.json()["conversation"]["messages"][-1]["text"]
            assert simulated.json()["conversation"]["messages"][-1]["evidence_ids"]

            draft = client.post(
                f"/v1/conversations/{conversation_id}/reply",
                headers=headers,
                json={"text": "Thanks; I will follow up."},
            )
            assert draft.status_code == 201
            assert draft.json()["delivery_status"] == "not_sent"

            other_tenant = client.get(
                f"/v1/conversations/{conversation_id}",
                headers={"X-Business-ID": str(uuid4()), "X-User-ID": str(uuid4())},
            )
            assert other_tenant.status_code == 404

            session_token = "integration-test-token"
            previous_activity = datetime.now(UTC) - timedelta(days=1)
            public_session = PublicSession(
                business_id=business_id,
                customer_account_id=UUID(customer["id"]),
                token_hash=bcrypt.hashpw(session_token.encode(), bcrypt.gensalt()),
                status="escalated",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
            fixture_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            fixture_session.add(public_session)
            fixture_session.flush()
            public_conversation = Conversation(
                business_id=business_id,
                public_session_id=public_session.id,
                status="escalated",
                source="public",
                updated_at=previous_activity,
            )
            fixture_session.add(public_conversation)
            fixture_session.commit()
            public_session_id = public_session.id
            public_conversation_id = public_conversation.id
            fixture_session.close()

            escalated_message = client.post(
                f"/v1/public/sessions/{public_session_id}/messages",
                json={"text": "Can you still help me with the Synthetic stacking toy price?"},
            )
            assert escalated_message.status_code == 202
            assert escalated_message.json()["escalated"] is True
            assert escalated_message.json()["assistant_message"] is not None
            assert "₹749.00" in escalated_message.json()["assistant_message"]["text"]
            assert escalated_message.json()["assistant_message"]["evidence_ids"]

            fixture_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            fixture_session.add_all(
                [
                    Message(
                        business_id=business_id,
                        conversation_id=public_conversation_id,
                        role="customer",
                        body="Can you tell me the price again?",
                        evidence_ids=[],
                    ),
                    Message(
                        business_id=business_id,
                        conversation_id=public_conversation_id,
                        role="customer",
                        body="Is it available?",
                        evidence_ids=[],
                    ),
                ]
            )
            fixture_session.commit()
            fixture_session.close()

            resumed_escalated_session = client.post(
                f"/v1/public/stores/test-{business_id.hex}/sessions",
            )
            assert resumed_escalated_session.status_code == 201
            assert resumed_escalated_session.json()["session_id"] == str(public_session_id)
            recovered_messages = resumed_escalated_session.json()["messages"]
            assert len(recovered_messages) == 5
            assert [message["sender"] for message in recovered_messages[-3:]] == [
                "customer",
                "customer",
                "assistant",
            ]
            assert recovered_messages[-1]["sender"] == "assistant"
            assert recovered_messages[-1]["evidence_ids"]
            repeated_resume = client.post(
                f"/v1/public/stores/test-{business_id.hex}/sessions",
            )
            assert len(repeated_resume.json()["messages"]) == 5
            verify_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            try:
                updated_conversation = verify_session.get(Conversation, public_conversation_id)
                assert updated_conversation is not None
                assert updated_conversation.updated_at > previous_activity
            finally:
                verify_session.close()

            closed_session = PublicSession(
                business_id=business_id,
                customer_account_id=UUID(customer["id"]),
                token_hash=None,
                status="open",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
            fixture_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            fixture_session.add(closed_session)
            fixture_session.flush()
            closed_conversation = Conversation(
                business_id=business_id,
                public_session_id=closed_session.id,
                status="closed",
                source="public",
            )
            fixture_session.add(closed_conversation)
            fixture_session.commit()
            closed_session_id = closed_session.id
            closed_conversation_id = closed_conversation.id
            fixture_session.close()

            closed_response = client.post(
                f"/v1/public/sessions/{closed_session_id}/messages",
                json={"text": "What is the price?"},
            )
            assert closed_response.status_code == 409
            verify_closed_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            try:
                assert (
                    verify_closed_session.query(Message)
                    .filter(Message.conversation_id == closed_conversation_id)
                    .count()
                    == 0
                )
            finally:
                verify_closed_session.close()

            closed_status_session = PublicSession(
                business_id=business_id,
                customer_account_id=UUID(customer["id"]),
                token_hash=None,
                status="closed",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
            fixture_session = Session(bind=connection, join_transaction_mode="create_savepoint")
            fixture_session.add(closed_status_session)
            fixture_session.flush()
            closed_status_conversation = Conversation(
                business_id=business_id,
                public_session_id=closed_status_session.id,
                status="closed",
                source="public",
            )
            fixture_session.add(closed_status_conversation)
            fixture_session.commit()
            closed_status_session_id = closed_status_session.id
            closed_status_conversation_id = closed_status_conversation.id
            fixture_session.close()

            closed_status_response = client.post(
                f"/v1/public/sessions/{closed_status_session_id}/messages",
                json={"text": "What is the price?"},
            )
            assert closed_status_response.status_code == 409
            verify_closed_status = Session(bind=connection, join_transaction_mode="create_savepoint")
            try:
                assert (
                    verify_closed_status.query(Message)
                    .filter(Message.conversation_id == closed_status_conversation_id)
                    .count()
                    == 0
                )
            finally:
                verify_closed_status.close()

            recovered_session = client.post(
                f"/v1/public/stores/test-{business_id.hex}/sessions",
            )
            assert recovered_session.status_code == 201
            assert recovered_session.json()["session_id"] != str(closed_session_id)
            recovered_reply = client.post(
                f"/v1/public/sessions/{recovered_session.json()['session_id']}/messages",
                json={"text": "What is the price?"},
            )
            assert recovered_reply.status_code == 202
            assert recovered_reply.json()["assistant_message"] is not None
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override
        transaction.rollback()
        connection.close()
