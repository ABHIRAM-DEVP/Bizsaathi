"""Job schemas for async processing status tracking."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    """Async background task state and progress."""

    id: UUID = Field(description="Unique job ID")
    business_id: UUID = Field(description="Owner tenant ID")
    kind: str = Field(description="Workflow kind")
    status: str = Field(description="Current status (queued, running, awaiting_approval, succeeded, blocked, failed)")
    progress_step: int = Field(default=0, description="Current step index")
    progress_total: int = Field(default=0, description="Total expected steps")
    result_ref: dict[str, Any] | None = Field(default=None, description="Result summary or output pointers")
    error_code: str | None = Field(default=None, description="Error code if failed")
    error_message: str | None = Field(default=None, description="Human explanation if failed")
    created_at: datetime = Field(description="Timestamp job was enqueued")
    started_at: datetime | None = Field(default=None, description="Timestamp processing started")
    finished_at: datetime | None = Field(default=None, description="Timestamp processing ended")
