from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.models.domain import Business, Job, JobEvent
from app.services.metrics import get_agent_metrics


def test_agent_metrics_aggregate_observed_jobs_and_nodes_by_tenant(db_session) -> None:
    now = datetime.now(UTC)
    tenant_a = Business(name="Metrics A", slug=f"metrics-a-{uuid4().hex[:8]}")
    tenant_b = Business(name="Metrics B", slug=f"metrics-b-{uuid4().hex[:8]}")
    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    succeeded = Job(
        business_id=tenant_a.id,
        kind="post_generate",
        status="succeeded",
        model_calls=2,
        created_at=now,
        started_at=now - timedelta(milliseconds=100),
        finished_at=now,
    )
    failed = Job(
        business_id=tenant_a.id,
        kind="post_generate",
        status="failed",
        model_calls=1,
        created_at=now,
        started_at=now - timedelta(milliseconds=300),
        finished_at=now,
    )
    other_tenant_job = Job(
        business_id=tenant_b.id,
        kind="post_generate",
        status="succeeded",
        model_calls=20,
        created_at=now,
        started_at=now - timedelta(seconds=1),
        finished_at=now,
    )
    db_session.add_all([succeeded, failed, other_tenant_job])
    db_session.flush()
    db_session.add_all(
        [
            JobEvent(
                business_id=tenant_a.id,
                job_id=succeeded.id,
                seq=1,
                node="draft_post",
                event="step_finished",
                duration_ms=10,
            ),
            JobEvent(
                business_id=tenant_a.id,
                job_id=failed.id,
                seq=1,
                node="draft_post",
                event="error",
                duration_ms=30,
                error_code="node.failed",
            ),
            JobEvent(
                business_id=tenant_b.id,
                job_id=other_tenant_job.id,
                seq=1,
                node="draft_post",
                event="step_finished",
                duration_ms=100,
            ),
        ]
    )
    db_session.flush()

    metrics = get_agent_metrics(db_session, business_id=tenant_a.id, window_days=30)

    assert metrics.total_jobs == 2
    assert metrics.jobs_by_status["succeeded"] == 1
    assert metrics.jobs_by_status["failed"] == 1
    assert metrics.success_rate == 0.5
    assert metrics.model_usage.model_calls == 3
    assert metrics.model_usage.input_tokens is None
    assert metrics.model_usage.estimated_cost_usd is None
    assert metrics.workflow_latency_ms.p50 == 200
    assert metrics.workflow_latency_ms.p95 == 290
    assert len(metrics.nodes) == 1
    assert metrics.nodes[0].node == "draft_post"
    assert metrics.nodes[0].execution_count == 2
    assert metrics.nodes[0].error_count == 1
    assert metrics.nodes[0].p50_ms == 20
    assert metrics.nodes[0].p95_ms == 29
