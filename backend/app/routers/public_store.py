"""Public store and customer chat endpoints (EP-E01 to EP-E08)."""

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Annotated, AsyncGenerator, Literal, TypedDict
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base import get_db, get_session
from app.models.domain import (
    AuditEvent,
    Business,
    Conversation,
    Message,
    Product,
    ProductVariant,
    PublicSession,
)
from app.schemas.customer_accounts import (
    CustomerAccountLoginRequest,
    CustomerAccountRegisterRequest,
    CustomerAccountResponse,
)
from app.services.customer_accounts import (
    get_authenticated_customer,
    login_customer_account,
    logout_customer_account,
    register_customer_account,
    validate_customer_request_origin,
)
from app.services.customer_replies import generate_grounded_reply
from app.services.public_rate_limits import check_public_rate_limit

router = APIRouter(prefix="/public", tags=["public"])


# --- Schemas ---


class PublicProduct(BaseModel):
    """Public-safe product representation."""

    id: UUID
    name: str
    price_inr: str
    in_stock: bool
    image_url: str | None = None


class PublicBusiness(BaseModel):
    """Public-safe business representation."""

    name: str
    slug: str
    description: str | None = None


class StoreResponse(BaseModel):
    """Response for EP-E01 GET /public/stores/{slug}."""

    business: PublicBusiness
    products: list[PublicProduct]


class PublicChatHistoryMessage(BaseModel):
    id: UUID
    sender: Literal["customer", "assistant", "owner"]
    text: str
    evidence_ids: list[UUID]


class SessionResponse(BaseModel):
    """Response for EP-E02 POST /public/stores/{slug}/sessions."""

    session_id: UUID
    expires_at: datetime
    disclosure: str
    messages: list[PublicChatHistoryMessage] = Field(default_factory=list)


class MessageRequest(BaseModel):
    """Request for EP-E03 POST /public/sessions/{id}/messages."""

    text: str = Field(..., min_length=1, max_length=1000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text is not just whitespace."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message text cannot be empty")
        return cleaned


class AssistantMessageResponse(BaseModel):
    id: UUID
    text: str
    evidence_ids: list[UUID]
    created_at: datetime


class MessageResponse(BaseModel):
    """Response for EP-E03 POST /public/sessions/{id}/messages."""

    message_id: UUID
    assistant_message: AssistantMessageResponse
    escalated: bool = False


class SessionUpdateMessage(TypedDict):
    message_id: str
    sender: Literal["assistant", "owner"]
    text: str
    evidence_ids: list[str]
    created_at: str


class SessionUpdates(TypedDict):
    status: str
    escalation_reason: str | None
    messages: list[SessionUpdateMessage]


def _session_response(
    db: Session,
    session: PublicSession,
    business: Business,
) -> SessionResponse:
    conversation = db.execute(
        select(Conversation).where(
            Conversation.public_session_id == session.id,
            Conversation.business_id == session.business_id,
        )
    ).scalar_one()
    messages = list(
        db.execute(
            select(Message)
            .where(
                Message.business_id == session.business_id,
                Message.conversation_id == conversation.id,
                Message.role.in_(("customer", "assistant", "owner")),
            )
            .order_by(Message.created_at, Message.id)
        )
        .scalars()
        .all()
    )
    history_messages: list[PublicChatHistoryMessage] = []
    for message in messages:
        if message.role == "customer":
            sender: Literal["customer", "assistant", "owner"] = "customer"
        elif message.role == "assistant":
            sender = "assistant"
        elif message.role == "owner":
            sender = "owner"
        else:
            continue
        history_messages.append(
            PublicChatHistoryMessage(
                id=message.id,
                sender=sender,
                text=message.body,
                evidence_ids=message.evidence_ids,
            )
        )
    return SessionResponse(
        session_id=session.id,
        expires_at=session.expires_at,
        disclosure=f"You are chatting with the catalog assistant for {business.name}",
        messages=history_messages,
    )


def _recover_unanswered_customer_message(
    db: Session,
    session: PublicSession,
    conversation: Conversation,
) -> None:
    messages = list(
        db.execute(
            select(Message)
            .where(
                Message.business_id == session.business_id,
                Message.conversation_id == conversation.id,
                Message.role.in_(("customer", "assistant", "owner")),
            )
            .order_by(Message.created_at, Message.id)
        )
        .scalars()
        .all()
    )
    pending_start = len(messages)
    while pending_start > 0 and messages[pending_start - 1].role == "customer":
        pending_start -= 1
    if pending_start == len(messages):
        return

    pending_messages = messages[pending_start:]
    recovery_prompt = "\n".join(
        f"Unanswered customer message {index}: {message.body}"
        for index, message in enumerate(pending_messages, start=1)
    )
    if len(recovery_prompt) > 8000:
        reply_text = (
            "I found several earlier messages that did not receive a reply. "
            "To make sure I answer accurately, please resend your key questions together in one message."
        )
        evidence_ids: list[UUID] = []
        escalation_reason = None
    else:
        reply = generate_grounded_reply(
            db,
            business_id=session.business_id,
            message=recovery_prompt,
            history=[
                f"{message.role}: {message.body}"
                for message in messages[max(0, pending_start - 8):pending_start]
            ],
        )
        reply_text = reply.text
        evidence_ids = reply.evidence_ids or []
        escalation_reason = reply.escalation_reason
    db.add(
        Message(
            business_id=session.business_id,
            conversation_id=conversation.id,
            role="assistant",
            body=reply_text,
            evidence_ids=evidence_ids,
        )
    )
    conversation.updated_at = datetime.now(UTC)
    if escalation_reason:
        conversation.status = "escalated"
        conversation.escalation_reason = escalation_reason
        session.status = "escalated"
    db.add(
        AuditEvent(
            business_id=session.business_id,
            actor_type="agent",
            action="customer_reply_recovered",
            entity_type="conversation",
            entity_id=str(conversation.id),
            detail={"message_ids": [str(message.id) for message in pending_messages]},
        )
    )
    db.flush()


@router.post(
    "/customer-accounts/register",
    response_model=CustomerAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a customer account",
    dependencies=[Depends(validate_customer_request_origin)],
)
def register_customer(
    body: CustomerAccountRegisterRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerAccountResponse:
    client_ip = request.client.host if request.client else "unknown"
    check_public_rate_limit(f"customer_register:{client_ip}", max_requests=5, window_seconds=3600)
    return register_customer_account(db, response, body)


@router.post(
    "/customer-accounts/login",
    response_model=CustomerAccountResponse,
    summary="Sign in to a customer account",
    dependencies=[Depends(validate_customer_request_origin)],
)
def login_customer(
    body: CustomerAccountLoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerAccountResponse:
    client_ip = request.client.host if request.client else "unknown"
    check_public_rate_limit(f"customer_login:{client_ip}", max_requests=10, window_seconds=900)
    return login_customer_account(db, response, body)


@router.get(
    "/customer-accounts/me",
    response_model=CustomerAccountResponse,
    summary="Get the signed-in customer account",
)
def get_customer_account(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerAccountResponse:
    client_ip = request.client.host if request.client else "unknown"
    check_public_rate_limit(f"customer_profile:{client_ip}", max_requests=60, window_seconds=60)
    account = get_authenticated_customer(request, db)
    return CustomerAccountResponse(id=account.id, email=account.email, display_name=account.display_name)


@router.post(
    "/customer-accounts/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out of a customer account",
    dependencies=[Depends(validate_customer_request_origin)],
)
def logout_customer(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    check_public_rate_limit(f"customer_logout:{client_ip}", max_requests=30, window_seconds=60)
    logout_customer_account(request, response, db)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


# --- EP-E01: GET /public/stores/{slug} ---


@router.get(
    "/stores/{slug}",
    response_model=StoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public store information",
    description="Returns store details and active products. No PII. Cacheable ~60s.",
)
def get_public_store(
    slug: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> StoreResponse:
    """
    EP-E01: Get public store by slug.
    
    Security:
    - Returns 404 for unknown slug (same timing as valid)
    - Active products only
    - No PII exposed
    """
    client_ip = request.client.host if request.client else "unknown"
    check_public_rate_limit(f"store_read:{client_ip}", max_requests=120, window_seconds=60)

    # Query business by slug
    result = db.execute(
        select(Business).where(
            Business.slug == slug,
            Business.status == "active",
        )
    )
    business = result.scalar_one_or_none()
    
    if not business:
        # Same timing as valid request (constant-time lookup)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://bizsaathi.dev/problems/store-not-found",
                "title": "Store Not Found",
                "status": 404,
                "detail": f"Store with slug '{slug}' not found",
            },
        )
    
    # Query active products for this business
    prod_result = db.execute(
        select(Product, func.coalesce(func.sum(ProductVariant.stock), 0))
        .outerjoin(
            ProductVariant,
            (ProductVariant.product_id == Product.id)
            & (ProductVariant.business_id == Product.business_id),
        )
        .where(Product.business_id == business.id)
        .where(Product.status == "active")
        .group_by(Product.id)
        .order_by(Product.created_at.desc())
    )
    products_list = prod_result.all()
    
    # Build public-safe response
    public_products: list[PublicProduct] = []
    for product, stock in products_list:
        if product.attributes.get("demo_only"):
            continue
        public_products.append(
            PublicProduct(
                id=product.id,
                name=product.name,
                price_inr=str(product.price_inr),
                in_stock=stock > 0,
                image_url=None,
            )
        )
    
    return StoreResponse(
        business=PublicBusiness(
            name=business.name,
            slug=business.slug,
            description=business.description,
        ),
        products=public_products,
    )


# --- EP-E02: POST /public/stores/{slug}/sessions ---


@router.post(
    "/stores/{slug}/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer chat session",
    description="Creates or resumes an authenticated customer chat session.",
    dependencies=[Depends(validate_customer_request_origin)],
)
def create_session(
    slug: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> SessionResponse:
    """
    EP-E02: Create or resume the signed-in customer's store chat session.
    """
    # Rate limit per IP
    client_ip = request.client.host if request.client else "unknown"
    check_public_rate_limit(f"session_create:{client_ip}", max_requests=10, window_seconds=3600)
    customer_account = get_authenticated_customer(request, db)
    
    # Verify business exists
    result = db.execute(
        select(Business).where(
            Business.slug == slug,
            Business.status == "active",
        )
    )
    business = result.scalar_one_or_none()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://bizsaathi.dev/problems/store-not-found",
                "title": "Store Not Found",
                "status": 404,
                "detail": f"Store with slug '{slug}' not found",
            },
        )
    
    now = datetime.now(UTC)
    existing_session = db.execute(
        select(PublicSession)
        .join(
            Conversation,
            (Conversation.public_session_id == PublicSession.id)
            & (Conversation.business_id == PublicSession.business_id),
        )
        .where(
            PublicSession.business_id == business.id,
            PublicSession.customer_account_id == customer_account.id,
            PublicSession.status.in_(("open", "escalated")),
            PublicSession.expires_at > now,
            Conversation.status.in_(("open", "escalated")),
        )
        .order_by(PublicSession.created_at.desc())
        .limit(1)
        .with_for_update(of=Conversation)
    ).scalar_one_or_none()
    if existing_session is not None:
        conversation = db.execute(
            select(Conversation)
            .where(
                Conversation.public_session_id == existing_session.id,
                Conversation.business_id == business.id,
            )
            .with_for_update()
        ).scalar_one()
        _recover_unanswered_customer_message(db, existing_session, conversation)
        return _session_response(db, existing_session, business)

    session_id = uuid4()
    expires_at = datetime.now(UTC) + timedelta(hours=24)
    # Hash IP for privacy (SHA-256)
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest() if client_ip != "unknown" else None
    
    # Store session in database
    public_session = PublicSession(
        id=session_id,
        business_id=business.id,
        customer_account_id=customer_account.id,
        token_hash=None,
        status="open",
        ip_hash=ip_hash,
        expires_at=expires_at,
    )
    db.add(public_session)
    db.flush()
    
    # Create conversation
    conversation = Conversation(
        id=uuid4(),
        business_id=business.id,
        public_session_id=session_id,
        status="open",
        source="public",
        customer_label=customer_account.display_name,
    )
    db.add(conversation)
    db.flush()
    return SessionResponse(
        session_id=session_id,
        expires_at=expires_at,
        disclosure=f"You are chatting with the catalog assistant for {business.name}",
        messages=[],
    )


# --- EP-E03: POST /public/sessions/{id}/messages ---


@router.post(
    "/sessions/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send customer message",
    description="Store a message and return a catalog-grounded reply or escalation. Rate limit: 20/min/session.",
    dependencies=[Depends(validate_customer_request_origin)],
)
def send_message(
    session_id: UUID,
    body: MessageRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    """
    EP-E03: Store a customer message and run the catalog-grounded chat workflow.
    """
    client_ip = request.client.host if request.client else "unknown"
    check_public_rate_limit(f"customer_message_ip:{client_ip}", max_requests=60, window_seconds=60)
    customer_account = get_authenticated_customer(request, db)

    # Rate limit per session
    check_public_rate_limit(
        f"message_send:{customer_account.id}",
        max_requests=20,
        window_seconds=60,
    )
    
    result = db.execute(
        select(PublicSession).where(
            PublicSession.id == session_id,
            PublicSession.customer_account_id == customer_account.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://bizsaathi.dev/problems/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Invalid session",
            },
        )
    
    # Check session status and expiration
    if session.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://bizsaathi.dev/problems/session-closed",
                "title": "Session Closed",
                "status": status.HTTP_409_CONFLICT,
                "detail": "This chat was closed. Start a new chat to continue.",
            },
        )
    if session.status not in {"open", "escalated"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://bizsaathi.dev/problems/session-not-available",
                "title": "Session Closed",
                "status": 403,
                "detail": f"Session status is {session.status}",
            },
        )
    
    if session.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://bizsaathi.dev/problems/session-expired",
                "title": "Session Expired",
                "status": 401,
                "detail": "Session has expired",
            },
        )
    
    # Get conversation for this session
    conv_result = db.execute(
        select(Conversation).where(
            Conversation.public_session_id == session_id,
            Conversation.business_id == session.business_id,
        )
    )
    conversation = conv_result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://bizsaathi.dev/problems/conversation-not-found",
                "title": "Conversation Not Found",
                "status": 404,
                "detail": "No conversation found for this session",
            },
        )

    if conversation.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://bizsaathi.dev/problems/conversation-closed",
                "title": "Conversation Closed",
                "status": status.HTTP_409_CONFLICT,
                "detail": "This chat was closed. Start a new chat to continue.",
            },
        )

    recent_messages = db.execute(
        select(Message.role, Message.body)
        .where(
            Message.business_id == session.business_id,
            Message.conversation_id == conversation.id,
            Message.role.in_(("customer", "assistant", "owner")),
        )
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(8)
    ).all()
    conversation_history = [
        f"{message.role}: {message.body}"
        for message in reversed(recent_messages)
    ]
    
    # Store customer message
    message_id = uuid4()
    customer_msg = Message(
        id=message_id,
        business_id=session.business_id,
        conversation_id=conversation.id,
        role="customer",
        body=body.text,
        evidence_ids=[],
    )
    db.add(customer_msg)
    db.add(
        AuditEvent(
            business_id=session.business_id,
            actor_type="public",
            actor_id=str(customer_account.id),
            action="customer_inquiry_received",
            entity_type="conversation",
            entity_id=str(conversation.id),
            detail={"message_id": str(message_id), "source": "public_chat"},
        )
    )
    conversation.updated_at = datetime.now(UTC)

    reply = generate_grounded_reply(
        db,
        business_id=session.business_id,
        message=body.text,
        history=conversation_history,
    )
    assistant = Message(
        business_id=session.business_id,
        conversation_id=conversation.id,
        role="assistant",
        body=reply.text,
        evidence_ids=reply.evidence_ids or [],
    )
    db.add(assistant)
    if reply.escalation_reason:
        conversation.status = "escalated"
        conversation.escalation_reason = reply.escalation_reason
        session.status = "escalated"
        db.add(
            AuditEvent(
                business_id=session.business_id,
                actor_type="agent",
                action="customer_message_escalated",
                entity_type="conversation",
                entity_id=str(conversation.id),
                detail={"reason": reply.escalation_reason},
            )
        )
    db.flush()
    assistant_response = AssistantMessageResponse(
        id=assistant.id,
        text=assistant.body,
        evidence_ids=assistant.evidence_ids,
        created_at=assistant.created_at,
    )

    db.flush()
    return MessageResponse(
        message_id=message_id,
        assistant_message=assistant_response,
        escalated=session.status == "escalated" or conversation.status == "escalated",
    )


# --- EP-E04: GET /public/sessions/{id}/stream ---


@router.get(
    "/sessions/{session_id}/stream",
    summary="SSE event stream for chat replies",
    description="Server-Sent Events stream. Events: reply, escalated, closed.",
)
async def stream_session(
    session_id: UUID,
    request: Request,
) -> StreamingResponse:
    """
    EP-E04: SSE stream for session events.
    
    Event types:
    - reply: {text, product_ids[]}
    - escalated: {message}
    - closed: {}
    
    Security:
    - Token verification on connect
    - Only public-safe references (product ids, no PII)
    - Heartbeat every 15s
    - Emits sanitized catalog replies and escalation events
    """
    token_db = get_session()
    try:
        client_ip = request.client.host if request.client else "unknown"
        check_public_rate_limit(f"session_stream:{client_ip}", max_requests=10, window_seconds=3600)
        account = get_authenticated_customer(request, token_db)
        session = token_db.execute(
            select(PublicSession).where(
                PublicSession.id == session_id,
                PublicSession.customer_account_id == account.id,
            )
        ).scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid customer chat session.",
            )
        if session.status not in {"open", "escalated"} or session.expires_at < datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session is closed or expired.")
    finally:
        token_db.close()

    async def event_generator() -> AsyncGenerator[str, None]:
        """Poll this session's sanitized store replies and escalation state."""
        yield f"event: connected\ndata: {json.dumps({'session_id': str(session_id)})}\n\n"
        seen_message_ids: set[str] = set()
        escalation_sent = False
        last_heartbeat = datetime.now(UTC)
        event_id = 0
        while True:
            updates = await asyncio.to_thread(_read_session_updates, session_id)
            for update in updates["messages"]:
                if update["message_id"] in seen_message_ids:
                    continue
                seen_message_ids.add(update["message_id"])
                event_id += 1
                yield (
                    f"id: {event_id}\nevent: reply\n"
                    f"data: {json.dumps(update, ensure_ascii=False)}\n\n"
                )

            if updates["status"] == "escalated" and not escalation_sent:
                escalation_sent = True
                event_id += 1
                yield (
                    f"id: {event_id}\nevent: escalated\n"
                    f"data: {json.dumps({'message': updates['escalation_reason']})}\n\n"
                )
            elif updates["status"] in {"closed", "blocked"}:
                yield f"event: closed\ndata: {json.dumps({'status': updates['status']})}\n\n"
                break

            now = datetime.now(UTC)
            if (now - last_heartbeat).total_seconds() >= 15:
                yield f"event: heartbeat\ndata: {json.dumps({'timestamp': now.isoformat()})}\n\n"
                last_heartbeat = now
            await asyncio.sleep(2)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def _read_session_updates(session_id: UUID) -> SessionUpdates:
    """Read public-safe events in a short-lived, session-scoped DB transaction."""
    db = get_session()
    try:
        session = db.execute(
            select(PublicSession).where(PublicSession.id == session_id)
        ).scalar_one_or_none()
        if session is None or session.expires_at < datetime.now(UTC):
            return {"status": "closed", "escalation_reason": None, "messages": []}
        if session.status in {"closed", "blocked"}:
            return {"status": session.status, "escalation_reason": None, "messages": []}
        conversation = db.execute(
            select(Conversation).where(
                Conversation.public_session_id == session_id,
                Conversation.business_id == session.business_id,
            )
        ).scalar_one_or_none()
        if conversation is None:
            return {"status": "closed", "escalation_reason": None, "messages": []}
        messages = db.execute(
            select(Message.id, Message.role, Message.body, Message.evidence_ids, Message.created_at)
            .where(
                Message.business_id == conversation.business_id,
                Message.conversation_id == conversation.id,
                Message.role.in_(("assistant", "owner")),
            )
            .order_by(Message.created_at, Message.id)
        ).all()
        return {
            "status": conversation.status,
            "escalation_reason": conversation.escalation_reason,
            "messages": [
                {
                    "message_id": str(message.id),
                    "sender": message.role,
                    "text": message.body,
                    "evidence_ids": [str(evidence_id) for evidence_id in message.evidence_ids],
                    "created_at": message.created_at.isoformat(),
                }
                for message in messages
            ],
        }
    finally:
        db.close()


# --- EP-E05, EP-E06: Phone verification (FUTURE) ---


@router.post(
    "/sessions/{session_id}/verify-phone/send",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Send phone verification OTP (FUTURE)",
)
async def send_phone_verification(session_id: UUID) -> dict:
    """EP-E05: FUTURE - Send phone verification OTP."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "type": "https://bizsaathi.dev/problems/not-implemented",
            "title": "Not Implemented",
            "status": 501,
            "detail": "Phone verification not yet implemented",
        },
    )


@router.post(
    "/sessions/{session_id}/verify-phone/verify",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Verify phone OTP (FUTURE)",
)
async def verify_phone(session_id: UUID) -> dict:
    """EP-E06: FUTURE - Verify phone OTP."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "type": "https://bizsaathi.dev/problems/not-implemented",
            "title": "Not Implemented",
            "status": 501,
            "detail": "Phone verification not yet implemented",
        },
    )
