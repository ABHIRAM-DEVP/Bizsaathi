"""Typed state definition for LangGraph workflow execution."""

from typing import Any, TypedDict
from uuid import UUID

from app.agents.models import ContextBundle, InputBundle, PolicyDecision, TaskPlan


class GraphState(TypedDict, total=False):
    """Execution state passed between LangGraph nodes."""

    business_id: UUID
    job_id: UUID
    task_plan: TaskPlan
    input_bundle: InputBundle
    context_bundle: ContextBundle
    policy_decision: PolicyDecision | None
    model_calls: int
    max_model_calls: int
    retry_count: int
    max_retries: int
    trace_events: list[dict[str, Any]]
    extracted_fields: dict[str, Any]
    conflicts: list[dict[str, Any]]
    uncertainties: list[dict[str, Any]]
    proposal_id: UUID | None
    proposal_payload: dict[str, Any] | None
    result: dict[str, Any] | None
    error_code: str | None
    error_message: str | None
    status: str
    verification_failed: bool
    critique: dict[str, Any]
