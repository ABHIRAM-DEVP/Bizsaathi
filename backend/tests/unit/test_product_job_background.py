"""Tests for durable asynchronous photo-extraction jobs."""

from uuid import uuid4

import pytest

from app.agents.models import InputBundle
from app.core.tenancy import AuthContext
from app.models.domain import Media
from app.routers import products
from app.schemas.products import ProductFromPhotoRequest


class FakeResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar_one_or_none(self) -> object:
        return self.value


class FakeSession:
    def __init__(self, media: Media | None = None) -> None:
        self.media = media
        self.committed = False
        self.closed = False
        self.job_status = "queued"
        self.records: list[object] = []

    def execute(self, _statement: object) -> FakeResult:
        return FakeResult(self.media)

    def add(self, record: object) -> None:
        self.records.append(record)

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def close(self) -> None:
        self.closed = True


class FakeBackgroundTasks:
    def __init__(self, db: FakeSession) -> None:
        self.db = db
        self.tasks: list[tuple[object, tuple[object, ...]]] = []

    def add_task(self, task: object, *args: object) -> None:
        assert self.db.committed
        self.tasks.append((task, args))


@pytest.mark.anyio
async def test_photo_job_is_committed_before_background_task_is_scheduled() -> None:
    business_id = uuid4()
    media_id = uuid4()
    media = Media(
        id=media_id,
        business_id=business_id,
        kind="photo",
        storage_key=f"{business_id}/uploads/photo.jpg",
        mime="image/jpeg",
        size_bytes=10,
        status="verified",
    )
    db = FakeSession(media)
    background_tasks = FakeBackgroundTasks(db)

    response = await products.create_product_from_photo(
        req=ProductFromPhotoRequest(media_ids=[media_id]),
        background_tasks=background_tasks,  # type: ignore[arg-type]
        auth=AuthContext(business_id=business_id, user_id=uuid4(), role="owner"),
        idempotency_key=None,
        db=db,  # type: ignore[arg-type]
    )

    assert db.committed
    assert response["status"] == "queued"
    assert len(background_tasks.tasks) == 1


@pytest.mark.anyio
async def test_background_agent_failure_commits_failed_job(monkeypatch: pytest.MonkeyPatch) -> None:
    business_id = uuid4()
    job_id = uuid4()
    db = FakeSession()

    class FailingRunner:
        def __init__(self, session: FakeSession, business_id: object) -> None:
            assert session is db
            assert business_id == business_id_expected

        async def run_job(self, job_id: object, input_bundle: InputBundle) -> None:
            assert job_id == job_id_expected
            assert input_bundle.kind == "product_from_photo"
            db.job_status = "failed"
            raise RuntimeError("vision provider timed out")

    business_id_expected = business_id
    job_id_expected = job_id
    monkeypatch.setattr(products, "get_session", lambda: db)
    monkeypatch.setattr(products, "AgentJobRunner", FailingRunner)

    await products._run_agent_bg(
        business_id,
        job_id,
        InputBundle(kind="product_from_photo"),
    )

    assert db.committed
    assert db.job_status == "failed"
    assert db.closed
