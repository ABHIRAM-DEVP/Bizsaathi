"""Tenant-scoped operational metrics from persisted jobs and graph events."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import case, extract, func, select
from sqlalchemy.orm import Session

from app.models.domain import Job, JobEvent
from app.schemas.metrics import (
    AgentMetricsResponse,
    ModelUsageMetrics,
    NodeMetrics,
    WorkflowLatencyMetrics,
)

_JOB_STATUSES = (
    "queued",
    "running",
    "awaiting_approval",
    "succeeded",
    "blocked",
    "failed",
    "cancelled",
)
_TERMINAL_STATUSES = ("succeeded", "blocked", "failed", "cancelled")


def get_agent_metrics(
    db: Session,
    *,
    business_id: UUID,
    window_days: int,
) -> AgentMetricsResponse:
    """Return measured job and node metrics for one tenant and bounded time window."""
    since = datetime.now(UTC) - timedelta(days=window_days)
    status_rows = db.execute(
        select(
            Job.status,
            func.count(Job.id),
            func.coalesce(func.sum(Job.model_calls), 0),
        )
        .where(Job.business_id == business_id, Job.created_at >= since)
        .group_by(Job.status)
    ).all()

    jobs_by_status = {status: 0 for status in _JOB_STATUSES}
    total_jobs = 0
    model_calls = 0
    for job_status, count, calls in status_rows:
        jobs_by_status[job_status] = count
        total_jobs += count
        model_calls += calls

    node_rows = db.execute(
        select(
            JobEvent.node,
            func.count(JobEvent.id),
            func.sum(case((JobEvent.event == "error", 1), else_=0)),
            func.percentile_cont(0.5).within_group(JobEvent.duration_ms),
            func.percentile_cont(0.95).within_group(JobEvent.duration_ms),
        )
        .join(
            Job,
            (Job.id == JobEvent.job_id) & (Job.business_id == JobEvent.business_id),
        )
        .where(
            Job.business_id == business_id,
            JobEvent.business_id == business_id,
            Job.created_at >= since,
            JobEvent.node.not_in(("system", "pipeline", "reconciler")),
            JobEvent.event.in_(("step_finished", "error")),
            JobEvent.duration_ms.is_not(None),
        )
        .group_by(JobEvent.node)
    ).all()
    nodes = [
        NodeMetrics(
            node=node,
            execution_count=count,
            error_count=error_count or 0,
            p50_ms=float(p50_ms) if p50_ms is not None else None,
            p95_ms=float(p95_ms) if p95_ms is not None else None,
        )
        for node, count, error_count, p50_ms, p95_ms in node_rows
    ]

    duration_ms = extract("epoch", Job.finished_at - Job.started_at) * 1000
    latency_row = db.execute(
        select(
            func.percentile_cont(0.5).within_group(duration_ms),
            func.percentile_cont(0.95).within_group(duration_ms),
        ).where(
            Job.business_id == business_id,
            Job.created_at >= since,
            Job.started_at.is_not(None),
            Job.finished_at.is_not(None),
        )
    ).one()
    p50_ms, p95_ms = latency_row

    terminal_jobs = sum(jobs_by_status[status] for status in _TERMINAL_STATUSES)
    success_rate = jobs_by_status["succeeded"] / terminal_jobs if terminal_jobs else None
    return AgentMetricsResponse(
        window_days=window_days,
        generated_at=datetime.now(UTC),
        total_jobs=total_jobs,
        jobs_by_status=jobs_by_status,
        success_rate=success_rate,
        workflow_latency_ms=WorkflowLatencyMetrics(
            p50=float(p50_ms) if p50_ms is not None else None,
            p95=float(p95_ms) if p95_ms is not None else None,
        ),
        model_usage=ModelUsageMetrics(model_calls=model_calls),
        nodes=nodes,
    )
