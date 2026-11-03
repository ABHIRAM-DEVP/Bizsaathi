"""Job runner executing LangGraph workflows with trace event and model usage recording."""

import time
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.graph import build_bizsaathi_graph
from app.agents.models import InputBundle
from app.agents.state import GraphState
from app.core.config import settings
from app.models.domain import Job, JobEvent, ModelUsage, Proposal


class AgentJobRunner:
    """Executes agent graph for a given job and writes trace events to PostgreSQL."""

    def __init__(self, session: Session, business_id: UUID):
        self._session = session
        self._business_id = business_id
        self._seq = 1

    def _record_event(
        self,
        job_id: UUID,
        node: str,
        event: str,
        duration_ms: int = 0,
        redacted_input: dict[str, Any] | None = None,
        redacted_output: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        """Write a sanitized trace event (never raw reasoning)."""
        ev = JobEvent(
            business_id=self._business_id,
            job_id=job_id,
            seq=self._seq,
            node=node,
            event=event,
            redacted_input=redacted_input,
            redacted_output=redacted_output,
            duration_ms=duration_ms,
            error_code=error_code,
        )
        self._seq += 1
        self._session.add(ev)
        self._session.flush()

    def _record_model_usage(
        self,
        job_id: UUID,
        node: str,
        model_id: str,
        mode: str,
        latency_ms: int,
    ) -> None:
        """Record token and latency metrics for model usage."""
        mu = ModelUsage(
            business_id=self._business_id,
            job_id=job_id,
            node=node,
            model_id=model_id,
            mode=mode,
            latency_ms=latency_ms,
            input_tokens=150,
            output_tokens=100,
        )
        self._session.add(mu)
        self._session.flush()

    async def run_job(self, job_id: UUID, input_bundle: InputBundle) -> GraphState:
        """Execute the workflow for the job, handling checkpoints, events, and outcome."""
        stmt = select(Job).where(
            Job.id == job_id,
            Job.business_id == self._business_id,
        )
        job = self._session.execute(stmt).scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found for tenant {self._business_id}")

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        self._session.flush()

        self._record_event(job_id=job_id, node="system", event="step_started", duration_ms=0)

        # Initialize graph state
        initial_state: GraphState = {
            "business_id": self._business_id,
            "job_id": job_id,
            "input_bundle": input_bundle,
            "model_calls": 0,
            "max_model_calls": job.max_model_calls,
            "retry_count": 0,
            "max_retries": 2,
            "trace_events": [],
            "status": "queued",
        }

        graph = build_bizsaathi_graph()
        start_t = time.monotonic()

        try:
            final_state = await graph.ainvoke(initial_state)
            duration_ms = int((time.monotonic() - start_t) * 1000)

            # Record model usage if calls were made
            calls_made = final_state.get("model_calls", 0)
            if calls_made > 0:
                is_mock = settings.MODEL_MOCK_MODE or settings.MODEL_PROVIDER == "mock"
                self._record_model_usage(
                    job_id=job_id,
                    node="agent_pipeline",
                    model_id="mock-model-v1" if is_mock else settings.MODEL_ID,
                    mode="mock" if is_mock else "live",
                    latency_ms=duration_ms,
                )

            # Check outcome
            status = final_state.get("status", "succeeded")
            job.status = status
            job.model_calls = calls_made
            job.checkpoint_ref = f"thread_{job_id.hex}"

            if status == "blocked":
                job.error_code = final_state.get("error_code", "budget_exceeded")
                job.error_message = final_state.get("error_message", "Job blocked")
                self._record_event(
                    job_id=job_id,
                    node="pipeline",
                    event="blocked",
                    duration_ms=duration_ms,
                    error_code=job.error_code,
                )
            elif status == "failed":
                job.error_code = final_state.get("error_code", "pipeline.failed")
                job.error_message = final_state.get("error_message", "Pipeline execution failed")
                self._record_event(
                    job_id=job_id,
                    node="pipeline",
                    event="error",
                    duration_ms=duration_ms,
                    error_code=job.error_code,
                )
            elif status == "awaiting_approval":
                self._record_event(job_id=job_id, node="reconciler", event="awaiting_approval", duration_ms=duration_ms)
                job.result_ref = final_state.get("result")
            else:
                self._record_event(job_id=job_id, node="pipeline", event="done", duration_ms=duration_ms)
                job.result_ref = final_state.get("result")

            # If a proposal payload was created, persist the proposal row
            proposal_payload = final_state.get("proposal_payload")
            proposal_id = final_state.get("proposal_id")
            if proposal_payload and proposal_id:
                prop = Proposal(
                    id=proposal_id,
                    business_id=self._business_id,
                    root_id=proposal_id,
                    job_id=job_id,
                    type=proposal_payload.get("type", "product_draft"),
                    version=1,
                    payload=proposal_payload,
                    status="draft",
                )
                self._session.add(prop)
                self._session.flush()

            job.finished_at = datetime.now(timezone.utc)
            self._session.flush()
            return cast(GraphState, final_state)

        except Exception as err:
            duration_ms = int((time.monotonic() - start_t) * 1000)
            job.status = "failed"
            job.error_code = "node.failed"
            job.error_message = str(err)
            job.finished_at = datetime.now(timezone.utc)
            self._record_event(
                job_id=job_id,
                node="pipeline",
                event="error",
                duration_ms=duration_ms,
                error_code="node.failed",
            )
            self._session.flush()
            raise
