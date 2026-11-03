"""Owner inbox and synthetic demo conversation schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

ConversationStatus = Literal["open", "escalated", "closed"]
ConversationSource = Literal["public", "demo"]
MessageRole = Literal["customer", "agent", "owner", "system"]


class ConversationMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender: MessageRole
    text: str
    evidence_ids: list[UUID]
    created_at: datetime


class ConversationListItem(BaseModel):
    id: UUID
    business_id: UUID
    status: ConversationStatus
    source: ConversationSource
    customer_name: str
    escalation_reason: str | None = None
    last_message: str | None = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationListItem]
    next_cursor: str | None = None


class ConversationDetailResponse(ConversationListItem):
    messages: list[ConversationMessageResponse]


class ConversationTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Text cannot be empty.")
        return cleaned


class ConversationReplyResponse(ConversationMessageResponse):
    delivery_status: Literal["delivered", "not_sent"] = "not_sent"


class DemoStartResponse(BaseModel):
    conversations: list[ConversationDetailResponse]
    label: Literal["synthetic_demo"] = "synthetic_demo"


class DemoMessageResponse(BaseModel):
    conversation: ConversationDetailResponse
    automated_reply: bool
    escalation: bool
