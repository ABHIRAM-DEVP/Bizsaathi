"""PostgreSQL coverage for photo jobs that fail in the background."""

from collections.abc import Iterator
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.models.base import get_db
from app.models.domain import Business, Job, Media
from app.routers import products


def test_failed_photo_job_remains_queryable(db_engine, monkeypatch) -> None:
    connection = db_engine.connect()
    transaction = connection.begin()
    business_id = uuid4()
    media_id = uuid4()
    monkeypatch.setattr(settings, "ENV", "dev")

    with Session(bind=connection, join_transaction_mode="create_savepoint") as seed:
        seed.add(
            Business(
                id=business_id,
                name="Photo Job Test",
                slug=f"photo-job-{business_id.hex[:12]}",
            )
        )
        seed.add(
            Media(
                id=media_id,
                business_id=business_id,
                kind="photo",
                storage_key=f"{business_id}/uploads/test.jpg",
                mime="image/jpeg",
                size_bytes=10,
                status="verified",
            )
        )
        seed.commit()

    def override_get_db() -> Iterator[Session]:
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_background_session() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    class FailingRunner:
        def __init__(self, session: Session, business_id: object) -> None:
            self.session = session
            self.business_id = business_id

        async def run_job(self, job_id, input_bundle) -> None:
            job = self.session.execute(
                select(Job).where(Job.id == job_id, Job.business_id == self.business_id)
            ).scalar_one()
            job.status = "failed"
            job.error_code = "node.failed"
            job.error_message = "ai_model: Model provider timed out."
            self.session.flush()
            raise RuntimeError("model provider failed")

    monkeypatch.setattr(products, "get_session", get_background_session)
    monkeypatch.setattr(products, "AgentJobRunner", FailingRunner)
    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)

    try:
        with TestClient(app) as client:
            headers = {
                "X-Business-ID": str(business_id),
                "X-User-ID": str(uuid4()),
                "X-User-Role": "owner",
            }
            response = client.post(
                "/v1/products/from-photo",
                json={"media_ids": [str(media_id)]},
                headers=headers,
            )
            assert response.status_code == 202
            job_id = response.json()["job_id"]

            poll = client.get(f"/v1/jobs/{job_id}", headers=headers)

            assert poll.status_code == 200
            assert poll.json()["status"] == "failed"
            assert poll.json()["error_message"] == "ai_model: Model provider timed out."
    finally:
        app.dependency_overrides.pop(get_db, None)
        transaction.rollback()
        connection.close()
