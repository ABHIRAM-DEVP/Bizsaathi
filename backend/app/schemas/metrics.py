"""Response schemas for tenant-scoped operational metrics."""

from datetime import datetime

from pydantic import BaseModel, Field


class ModelUsageMetrics(BaseModel):
    """Recorded call totals; token and billing data stay unknown until provided."""

    model_calls: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None


class NodeMetrics(BaseModel):
    """Observed execution/error counts and duration distribution for a graph node."""

    node: str
    execution_count: int
    error_count: int
    p50_ms: float | None = None
    p95_ms: float | None = None


class WorkflowLatencyMetrics(BaseModel):
    """Observed end-to-end job duration distribution in milliseconds."""

    p50: float | None = None
    p95: float | None = None


class AgentMetricsResponse(BaseModel):
    """Tenant-scoped workflow metrics over a bounded time window."""

    window_days: int = Field(ge=1, le=90)
    generated_at: datetime
    total_jobs: int
    jobs_by_status: dict[str, int]
    success_rate: float | None = Field(
        description="Succeeded jobs divided by terminal jobs; null when no jobs have finished."
    )
    workflow_latency_ms: WorkflowLatencyMetrics
    model_usage: ModelUsageMetrics
    nodes: list[NodeMetrics]
