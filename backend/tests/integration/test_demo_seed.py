from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import InvalidStateError
from app.models.domain import Business, Conversation, Evidence, Media, Message, Product, ProductVariant
from app.services.demo_seed import seed_demo_catalog, seed_demo_data, seed_demo_inbox


def test_demo_seed_refuses_non_development_environment(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENV", "prod")
    session = Mock(spec=Session)

    with pytest.raises(InvalidStateError, match="only be seeded when ENV=dev"):
        seed_demo_data(session)

    session.execute.assert_not_called()


def test_demo_catalog_and_inbox_seed_is_idempotent(db_engine, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "ENV", "dev")
    monkeypatch.setattr(settings, "MEDIA_STORAGE_PATH", str(tmp_path))

    def reject_model_client(**kwargs) -> None:
        pytest.fail("Demo inbox seeding must not request a model client.")

    monkeypatch.setattr("app.services.customer_replies.get_model_client", reject_model_client)
    business_id = uuid4()
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        session.add(Business(id=business_id, name="Synthetic Fixture Shop", slug=f"fixture-{business_id.hex}"))
        session.flush()

        assert seed_demo_catalog(session, business_id) == {"products_created": 5, "images_created": 5}
        conversations = seed_demo_inbox(session, business_id)
        assert len(conversations) == 3
        session.flush()

        assert session.scalar(select(func.count()).select_from(Product).where(Product.business_id == business_id)) == 5
        assert (
            session.scalar(select(func.count()).select_from(ProductVariant).where(
                ProductVariant.business_id == business_id
            ))
            == 5
        )
        assert session.scalar(select(func.count()).select_from(Media).where(Media.business_id == business_id)) == 5
        assert (
            session.scalar(select(func.count()).select_from(Conversation).where(
                Conversation.business_id == business_id
            ))
            == 3
        )
        assert session.scalar(select(func.count()).select_from(Message).where(Message.business_id == business_id)) == 6
        conversation_by_label = {item.customer_label: item for item in conversations}
        assistant_messages = {
            message.conversation_id: message
            for message in session.scalars(
                select(Message).where(
                    Message.business_id == business_id,
                    Message.role == "assistant",
                )
            ).all()
        }
        price_conversation = conversation_by_label["Synthetic buyer 1"]
        stock_conversation = conversation_by_label["Synthetic buyer 2"]
        refund_conversation = conversation_by_label["Synthetic buyer 3"]
        assert assistant_messages[price_conversation.id].evidence_ids
        assert assistant_messages[stock_conversation.id].evidence_ids
        assert "listed at ₹" in assistant_messages[price_conversation.id].body
        assert refund_conversation.status == "escalated"
        assert not assistant_messages[refund_conversation.id].evidence_ids
        assert session.scalar(
            select(func.count()).select_from(Evidence).where(Evidence.business_id == business_id)
        ) == 4

        product = session.scalar(select(Product).where(Product.business_id == business_id))
        assert product is not None
        product.name = "Seller-edited product"
        session.flush()
        assert seed_demo_catalog(session, business_id) == {"products_created": 0, "images_created": 0}
        assert product.name == "Seller-edited product"
        assert len(seed_demo_inbox(session, business_id)) == 3
        session.flush()

        assert session.scalar(select(func.count()).select_from(Product).where(Product.business_id == business_id)) == 5
        assert (
            session.scalar(select(func.count()).select_from(Conversation).where(
                Conversation.business_id == business_id
            ))
            == 3
        )
    finally:
        session.close()
        transaction.rollback()
        connection.close()
