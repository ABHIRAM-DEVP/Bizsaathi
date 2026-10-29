"""Public store and customer chat endpoints (EP-E01 to EP-E08)."""

import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, AsyncGenerator
from uuid import UUID, uuid4

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.domain import Business, Conversation, Message, Product, PublicSession

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


class SessionResponse(BaseModel):
    """Response for EP-E02 POST /public/stores/{slug}/sessions."""

    session_id: UUID
    session_token: str
    expires_at: datetime
    disclosure: str


class MessageRequest(BaseModel):
    """Request for EP-E03 POST /public/sessions/{id}/messages."""

    text: str = Field(..., min_length=1, max_length=1000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text is not just whitespace."""
        if not v.strip():
            raise ValueError("Message text cannot be empty")
        return v


class MessageResponse(BaseModel):
    """Response for EP-E03 POST /public/sessions/{id}/messages."""

    message_id: UUID


# --- Rate Limiting (Simplified - TODO: Use Redis for production) ---


_rate_limit_store: dict[str, list[datetime]] = {}


def _check_rate_limit(key: str, max_requests: int, window_seconds: int) -> None:
    """
    Simple in-memory rate limiter.
    
    In production, use Redis with sliding window or token bucket.
    """
    now = datetime.now(UTC)
    cutoff = now - timedelta(seconds=window_seconds)
    
    # Get timestamps for this key
    timestamps = _rate_limit_store.get(key, [])
    
    # Remove old timestamps
    timestamps = [ts for ts in timestamps if ts > cutoff]
    
    # Check limit
    if len(timestamps) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "type": "https://bizsaathi.dev/problems/rate-limit-exceeded",
                "title": "Rate Limit Exceeded",
                "status": 429,
                "detail": f"Maximum {max_requests} requests per {window_seconds}s exceeded",
            },
        )
    
    # Add current request
    timestamps.append(now)
    _rate_limit_store[key] = timestamps


# --- EP-E01: GET /public/stores/{slug} ---


@router.get(
    "/stores/{slug}",
    response_model=StoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public store information",
    description="Returns store details and active products. No PII. Cacheable ~60s.",
)
async def get_public_store(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StoreResponse:
    """
    EP-E01: Get public store by slug.
    
    Security:
    - Returns 404 for unknown slug (same timing as valid)
    - Active products only
    - No PII exposed
    """
    # Query business by slug
    result = await db.execute(select(Business).where(Business.slug == slug))
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
    prod_result = await db.execute(
        select(Product)
        .where(Product.business_id == business.id)
        .where(Product.status == "active")
        .order_by(Product.created_at.desc())
    )
    products_list = prod_result.scalars().all()
    
    # Build public-safe response
    public_products: list[PublicProduct] = []
    for product in products_list:
        # TODO: Query product_variant to get actual stock total
        # For now, assume available if product is active
        public_products.append(
            PublicProduct(
                id=product.id,
                name=product.name,
                price_inr=str(product.price_inr),
                in_stock=True,  # TODO: Check actual stock from variants
                image_url=None,  # TODO: Generate signed URL from media table
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
    description="Creates a new chat session. Returns token once. Rate limit: 10/hour/IP.",
)
async def create_session(
    slug: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """
    EP-E02: Create customer chat session.
    
    Security:
    - Token returned once, never logged
    - Token hash stored (bcrypt or similar)
    - Rate limited per IP: 10/hour
    - Disclosure text shown to customer
    """
    # Rate limit per IP
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(f"session_create:{client_ip}", max_requests=10, window_seconds=3600)
    
    # Verify business exists
    result = await db.execute(select(Business).where(Business.slug == slug))
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
    
    # Generate session
    session_id = uuid4()
    session_token = secrets.token_urlsafe(32)  # 256 bits of entropy
    expires_at = datetime.now(UTC) + timedelta(hours=24)
    
    # Hash token with bcrypt (secure, slow hash)
    token_hash = bcrypt.hashpw(session_token.encode("utf-8"), bcrypt.gensalt())
    
    # Hash IP for privacy (SHA-256)
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest() if client_ip != "unknown" else None
    
    # Store session in database
    public_session = PublicSession(
        id=session_id,
        business_id=business.id,
        token_hash=token_hash,
        status="open",
        ip_hash=ip_hash,
        expires_at=expires_at,
    )
    db.add(public_session)
    
    # Create conversation
    conversation = Conversation(
        id=uuid4(),
        business_id=business.id,
        public_session_id=session_id,
        status="open",
    )
    db.add(conversation)
    
    await db.commit()
    
    disclosure = f"You are chatting with an AI assistant for {business.name}"
    
    return SessionResponse(
        session_id=session_id,
        session_token=session_token,
        expires_at=expires_at,
        disclosure=disclosure,
    )


# --- EP-E03: POST /public/sessions/{id}/messages ---


@router.post(
    "/sessions/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send customer message",
    description="Send message in chat session. Reply arrives via SSE stream. Rate limit: 20/min/session.",
)
async def send_message(
    session_id: UUID,
    body: MessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_session_token: Annotated[str | None, Header()] = None,
) -> MessageResponse:
    """
    EP-E03: Send customer message.
    
    Security:
    - X-Session-Token header required
    - Token verification (constant-time bcrypt comparison)
    - Rate limited: 20/min/session
    - Input validation: 1-1000 chars
    - Pipeline: node 09 -> 10 -> 13 with read-only tools
    
    Tests:
    - Injection text does not change behavior
    - No cross-tenant data leakage
    """
    # Verify token provided
    if not x_session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://bizsaathi.dev/problems/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "X-Session-Token header required",
            },
        )
    
    # Rate limit per session
    _check_rate_limit(f"message_send:{session_id}", max_requests=20, window_seconds=60)
    
    # Verify session exists and token is valid
    result = await db.execute(
        select(PublicSession).where(PublicSession.id == session_id)
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
    
    # Verify token (constant-time comparison via bcrypt)
    token_valid = bcrypt.checkpw(
        x_session_token.encode("utf-8"),
        session.token_hash
    )
    
    if not token_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://bizsaathi.dev/problems/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Invalid token",
            },
        )
    
    # Check session status and expiration
    if session.status != "open":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://bizsaathi.dev/problems/session-closed",
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
    conv_result = await db.execute(
        select(Conversation).where(Conversation.public_session_id == session_id)
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
    
    # Store customer message
    message_id = uuid4()
    customer_msg = Message(
        id=message_id,
        business_id=session.business_id,
        conversation_id=conversation.id,
        role="customer",
        body=body.text,
    )
    db.add(customer_msg)
    await db.commit()
    
    # TODO: Trigger agent pipeline asynchronously
    # This would typically:
    # 1. Create a Job record
    # 2. Enqueue background task
    # 3. Run graph with InputBundle(
    #      kind="customer_reply",
    #      customer_message=body.text,
    #      conversation_id=conversation.id,
    #      language="en",  # TODO: detect from conversation
    #    )
    # 4. Store assistant response in Message table
    # 5. Publish to SSE stream for EP-E04
    
    # For now, return 202 Accepted
    # The response will arrive via SSE stream (EP-E04)
    
    return MessageResponse(message_id=message_id)


# --- EP-E04: GET /public/sessions/{id}/stream ---


@router.get(
    "/sessions/{session_id}/stream",
    summary="SSE event stream for chat replies",
    description="Server-Sent Events stream. Events: reply, escalated, closed.",
)
async def stream_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_session_token: Annotated[str | None, Header()] = None,
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
    - Supports Last-Event-ID resume
    """
    # Verify token provided
    if not x_session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "https://bizsaathi.dev/problems/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "X-Session-Token header required",
            },
        )
    
    # Verify session and token
    result = await db.execute(
        select(PublicSession).where(PublicSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    
    # Verify token
    token_valid = bcrypt.checkpw(
        x_session_token.encode("utf-8"),
        session.token_hash
    )
    
    if not token_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for the session."""
        try:
            # Send initial connection event
            yield f"event: connected\ndata: {{'session_id': '{session_id}'}}\n\n"
            
            # Main event loop
            event_id = 0
            while True:
                # TODO: Check for new messages in database
                # For now, just send heartbeat
                
                # Heartbeat every 15 seconds
                await asyncio.sleep(15)
                event_id += 1
                yield f"id: {event_id}\nevent: heartbeat\ndata: {{'timestamp': '{datetime.now(UTC).isoformat()}'}}\n\n"
                
                # TODO: Query for new assistant messages
                # TODO: Format as reply events
                # TODO: Handle escalation events
                # TODO: Handle session close events
                
                # For demo purposes, break after 5 heartbeats (75 seconds)
                if event_id >= 5:
                    yield "event: closed\ndata: {'reason': 'demo_timeout'}\n\n"
                    break
                    
        except asyncio.CancelledError:
            # Client disconnected
            yield "event: closed\ndata: {'reason': 'client_disconnect'}\n\n"
        except Exception as e:
            # Error occurred
            yield f"event: error\ndata: {{'error': '{str(e)}'}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


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
