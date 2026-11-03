"""Tenant-scoped owner inbox and development-only conversation simulation."""

import base64
import binascii
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.tenancy import AuthContext, require_owner_role
from app.models.base import get_db
from app.models.domain import (
    AuditEvent,
    Conversation,
    Message,
    Product,
    PublicSession,
)
from app.schemas.conversations import (
    ConversationDetailResponse,
    ConversationListItem,
    ConversationListResponse,
    ConversationMessageResponse,
    ConversationReplyResponse,
    ConversationSource,
    ConversationStatus,
    ConversationTextRequest,
    DemoMessageResponse,
    DemoStartResponse,
    MessageRole,
)
from app.services.customer_replies import generate_grounded_reply
from app.services.demo_seed import seed_demo_inbox

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _encode_cursor(conversation: Conversation) -> str:
    value = f"{conversation.updated_at.isoformat()}|{conversation.id}"
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        decoded = base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True).decode("utf-8")
        timestamp, conversation_id = decoded.split("|", maxsplit=1)
        parsed_timestamp = datetime.fromisoformat(timestamp)
        if parsed_timestamp.tzinfo is None:
            raise ValueError
        return parsed_timestamp, UUID(conversation_id)
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise HTTPException(status_code=422, detail="Invalid conversation cursor.") from exc


def _message_response(message: Message) -> ConversationMessageResponse:
    sender: MessageRole
    if message.role == "assistant":
        sender = "agent"
    elif message.role == "customer":
        sender = "customer"
    elif message.role == "owner":
        sender = "owner"
    elif message.role == "system":
        sender = "system"
    else:
        raise ValueError(f"Unsupported persisted message role: {message.role}")
    return ConversationMessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender=sender,
        text=message.body,
        evidence_ids=message.evidence_ids,
        created_at=message.created_at,
    )


def _list_item(
    conversation: Conversation,
    last_message: str | None = None,
    unread_count: int = 0,
) -> ConversationListItem:
    status_value: ConversationStatus
    if conversation.status == "open":
        status_value = "open"
    elif conversation.status == "escalated":
        status_value = "escalated"
    elif conversation.status == "closed":
        status_value = "closed"
    else:
        raise ValueError(f"Unsupported persisted conversation status: {conversation.status}")

    source_value: ConversationSource
    if conversation.source == "public":
        source_value = "public"
    elif conversation.source == "demo":
        source_value = "demo"
    else:
        raise ValueError(f"Unsupported persisted conversation source: {conversation.source}")

    return ConversationListItem(
        id=conversation.id,
        business_id=conversation.business_id,
        status=status_value,
        source=source_value,
        customer_name=conversation.customer_label or "Customer",
        escalation_reason=conversation.escalation_reason,
        last_message=last_message,
        unread_count=unread_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _detail(db: Session, conversation: Conversation) -> ConversationDetailResponse:
    messages = db.execute(
        select(Message)
        .where(
            Message.business_id == conversation.business_id,
            Message.conversation_id == conversation.id,
        )
        .order_by(Message.created_at, Message.id)
    ).scalars().all()
    latest_message = messages[-1].body if messages else None
    unread_count = sum(
        message.role == "customer" and message.read_by_owner_at is None
        for message in messages
    )
    return ConversationDetailResponse(
        **_list_item(conversation, latest_message, unread_count).model_dump(),
        messages=[_message_response(message) for message in messages],
    )


def _get_tenant_conversation(db: Session, business_id: UUID, conversation_id: UUID) -> Conversation:
    conversation = db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.business_id == business_id,
        )
    ).scalar_one_or_none()
    if conversation is None:
        raise NotFoundError(f"Conversation {conversation_id} not found.")
    return conversation


def _append_assistant_reply(
    db: Session,
    conversation: Conversation,
    customer_text: str,
    *,
    include_demo_products: bool,
) -> Message:
    reply = generate_grounded_reply(
        db,
        business_id=conversation.business_id,
        message=customer_text,
        include_demo_products=include_demo_products,
    )
    message = Message(
        business_id=conversation.business_id,
        conversation_id=conversation.id,
        role="assistant",
        body=reply.text,
        evidence_ids=reply.evidence_ids or [],
    )
    db.add(message)
    if reply.escalation_reason:
        conversation.status = "escalated"
        conversation.escalation_reason = reply.escalation_reason
        db.add(
            AuditEvent(
                business_id=conversation.business_id,
                actor_type="agent",
                action="customer_message_escalated",
                entity_type="conversation",
                entity_id=str(conversation.id),
                detail={"reason": reply.escalation_reason},
            )
        )
    conversation.updated_at = datetime.now(UTC)
    return message


@router.get("", response_model=ConversationListResponse, summary="List tenant conversations (EP-F01)")
def list_conversations(
    status_filter: Annotated[Literal["open", "escalated", "closed"] | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> ConversationListResponse:
    filters = [Conversation.business_id == auth.business_id]
    if status_filter:
        filters.append(Conversation.status == status_filter)
    if cursor:
        timestamp, conversation_id = _decode_cursor(cursor)
        filters.append(
            or_(
                Conversation.updated_at < timestamp,
                and_(Conversation.updated_at == timestamp, Conversation.id < conversation_id),
            )
        )

    last_message = (
        select(Message.body)
        .where(
            Message.business_id == Conversation.business_id,
            Message.conversation_id == Conversation.id,
        )
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
        .scalar_subquery()
    )
    unread_count = (
        select(func.count(Message.id))
        .where(
            Message.business_id == Conversation.business_id,
            Message.conversation_id == Conversation.id,
            Message.role == "customer",
            Message.read_by_owner_at.is_(None),
        )
        .scalar_subquery()
    )
    rows = db.execute(
        select(Conversation, last_message.label("last_message"), unread_count.label("unread_count"))
        .where(*filters)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .limit(limit + 1)
    ).all()
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = _encode_cursor(page[-1][0]) if has_more and page else None
    return ConversationListResponse(
        items=[_list_item(conversation, last_text, unread) for conversation, last_text, unread in page],
        next_cursor=next_cursor,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse, summary="Get tenant conversation (EP-F02)")
def get_conversation(
    conversation_id: UUID,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> ConversationDetailResponse:
    conversation = _get_tenant_conversation(db, auth.business_id, conversation_id)
    unread_messages = db.execute(
        select(Message).where(
            Message.business_id == auth.business_id,
            Message.conversation_id == conversation.id,
            Message.role == "customer",
            Message.read_by_owner_at.is_(None),
        )
    ).scalars().all()
    read_at = datetime.now(UTC)
    for message in unread_messages:
        message.read_by_owner_at = read_at
    if unread_messages:
        db.flush()
    return _detail(db, conversation)


@router.post(
    "/demo/start",
    response_model=DemoStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Start or resume synthetic inbox demo",
)
def start_demo(
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> DemoStartResponse:
    if settings.ENV not in ("dev", "test"):
        raise ForbiddenError(detail="Synthetic inbox data is available only in development and test.")
    conversations = seed_demo_inbox(db, auth.business_id)
    return DemoStartResponse(conversations=[_detail(db, conversation) for conversation in conversations])


@router.post(
    "/{conversation_id}/demo-messages",
    response_model=DemoMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a synthetic customer message to a demo thread",
)
def send_demo_message(
    conversation_id: UUID,
    body: ConversationTextRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> DemoMessageResponse:
    if settings.ENV not in ("dev", "test"):
        raise ForbiddenError(detail="Synthetic inbox data is available only in development and test.")
    conversation = _get_tenant_conversation(db, auth.business_id, conversation_id)
    if conversation.source != "demo":
        raise NotFoundError(f"Demo conversation {conversation_id} not found.")
    if conversation.status == "closed":
        raise ForbiddenError(detail="Closed conversations cannot receive demo messages.")

    db.add(
        Message(
            business_id=conversation.business_id,
            conversation_id=conversation.id,
            role="customer",
            body=body.text.strip(),
            evidence_ids=[],
        )
    )
    conversation.updated_at = datetime.now(UTC)
    if conversation.status == "escalated":
        db.flush()
        return DemoMessageResponse(
            conversation=_detail(db, conversation),
            automated_reply=False,
            escalation=True,
        )

    _append_assistant_reply(
        db,
        conversation,
        body.text,
        include_demo_products=True,
    )
    db.flush()
    return DemoMessageResponse(
        conversation=_detail(db, conversation),
        automated_reply=conversation.status == "open",
        escalation=conversation.status == "escalated",
    )


@router.post(
    "/demo/simulate",
    response_model=DemoMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add the next synthetic customer message",
)
def simulate_next_demo_message(
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> DemoMessageResponse:
    if settings.ENV not in ("dev", "test"):
        raise ForbiddenError(detail="Synthetic inbox data is available only in development and test.")

    conversations = db.execute(
        select(Conversation)
        .where(
            Conversation.business_id == auth.business_id,
            Conversation.source == "demo",
        )
        .order_by(Conversation.created_at, Conversation.id)
    ).scalars().all()
    if len(conversations) != 3:
        raise ConflictError(detail="Start the three-customer synthetic inbox demo before simulating messages.")

    customer_message_count = db.execute(
        select(func.count(Message.id))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Message.business_id == auth.business_id,
            Conversation.business_id == auth.business_id,
            Conversation.source == "demo",
            Message.role == "customer",
        )
    ).scalar_one()
    conversation = conversations[customer_message_count % len(conversations)]
    product = db.execute(
        select(Product)
        .where(Product.business_id == auth.business_id, Product.status == "active")
        .order_by(Product.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    product_name = product.name if product else "your product"
    description = " ".join((product.description or "").split()) if product else ""
    description_excerpt = description[:180].rstrip()
    if len(description) > len(description_excerpt):
        description_excerpt += "…"
    description_context = (
        f' Your listing describes it as “{description_excerpt}”.'
        if description_excerpt
        else ""
    )
    sample_messages = (
        (
            f"Hi! I came across the photo of {product_name}.{description_context} "
            "Could you tell me a little more about the product before I decide?"
        ),
        (
            f"Hello, I am interested in {product_name}.{description_context} "
            "Does the listing have any other details about how it is made or used?"
        ),
        (
            f"Hi there! I noticed {product_name} in your product pictures.{description_context} "
            "Could you help me understand which details are confirmed in the listing?"
        ),
    )
    customer_text = sample_messages[customer_message_count % len(sample_messages)]
    db.add(
        Message(
            business_id=auth.business_id,
            conversation_id=conversation.id,
            role="customer",
            body=customer_text,
            evidence_ids=[],
        )
    )
    conversation.updated_at = datetime.now(UTC)
    if conversation.status != "escalated":
        _append_assistant_reply(
            db,
            conversation,
            customer_text,
            include_demo_products=True,
        )
    db.flush()
    return DemoMessageResponse(
        conversation=_detail(db, conversation),
        automated_reply=conversation.status == "open",
        escalation=conversation.status == "escalated",
    )


@router.post(
    "/{conversation_id}/reply",
    response_model=ConversationReplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send an owner reply to the customer in-app",
)
def send_owner_reply(
    conversation_id: UUID,
    body: ConversationTextRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> ConversationReplyResponse:
    conversation = _get_tenant_conversation(db, auth.business_id, conversation_id)
    if conversation.status == "closed":
        raise ForbiddenError(detail="Closed conversations cannot receive replies.")
    delivery_status: Literal["delivered", "not_sent"] = "not_sent"
    if conversation.source == "public":
        public_session = db.execute(
            select(PublicSession)
            .where(
                PublicSession.id == conversation.public_session_id,
                PublicSession.business_id == auth.business_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if public_session is None or public_session.status in {"closed", "blocked"}:
            raise ForbiddenError(detail="The customer's chat session is no longer available.")
        public_session.expires_at = datetime.now(UTC) + timedelta(hours=24)
        delivery_status = "delivered"
    message = Message(
        business_id=conversation.business_id,
        conversation_id=conversation.id,
        role="owner",
        body=body.text.strip(),
        evidence_ids=[],
    )
    db.add(message)
    conversation.updated_at = datetime.now(UTC)
    db.add(
        AuditEvent(
            business_id=auth.business_id,
            actor_type="user",
            actor_id=str(auth.user_id),
            action=(
                "conversation_reply_delivered"
                if delivery_status == "delivered"
                else "conversation_reply_draft_saved"
            ),
            entity_type="conversation",
            entity_id=str(conversation.id),
            detail={"delivery_status": delivery_status},
        )
    )
    db.flush()
    return ConversationReplyResponse(
        **_message_response(message).model_dump(),
        delivery_status=delivery_status,
    )
