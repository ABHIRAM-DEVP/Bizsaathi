"""Unit tests for jobs endpoint and tenant isolation."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.base import get_db
from app.models.domain import Job


class FakeJobDbSession:
    """In-memory mock session for Job queries."""

    def __init__(self, jobs: list[Job]):
        self.jobs = jobs

    def execute(self, stmt):
        class ScalarResult:
            def __init__(self, items):
                self._items = items

            def scalar_one_or_none(self):
                return self._items[0] if self._items else None

            def scalars(self):
                return self

        compiled = stmt.compile()
        params = compiled.params
        param_values = list(params.values())

        matching = []
        for j in self.jobs:
            if j.id in param_values and j.business_id in param_values:
                matching.append(j)

        return ScalarResult(matching)

    def close(self):
        pass


def test_tenant_b_cannot_read_tenant_a_job():
    job_id = uuid4()
    tenant_a_id = uuid4()
    tenant_b_id = uuid4()

    tenant_a_job = Job(
        id=job_id,
        business_id=tenant_a_id,
        kind="product_from_photo",
        status="running",
        progress_step=1,
        progress_total=3,
        created_at=datetime.now(timezone.utc),
    )

    fake_db = FakeJobDbSession([tenant_a_job])
    app.dependency_overrides[get_db] = lambda: fake_db

    with TestClient(app) as client:
        # Tenant B requests Tenant A's job
        headers = {
            "X-Business-ID": str(tenant_b_id),
            "X-User-ID": str(uuid4()),
            "X-User-Role": "owner",
        }
        response = client.get(f"/v1/jobs/{job_id}", headers=headers)

        # Must return 404 RFC 7807 problem details
        assert response.status_code == 404
        data = response.json()
        assert data["type"] == "https://bizsaathi.dev/problems/not-found"
        assert "not found" in data["detail"].lower()

    app.dependency_overrides.pop(get_db, None)


def test_tenant_reads_own_job_succeeds():
    job_id = uuid4()
    tenant_a_id = uuid4()

    tenant_a_job = Job(
        id=job_id,
        business_id=tenant_a_id,
        kind="product_from_photo",
        status="succeeded",
        progress_step=3,
        progress_total=3,
        result_ref={"product_id": str(uuid4())},
        created_at=datetime.now(timezone.utc),
    )

    fake_db = FakeJobDbSession([tenant_a_job])
    app.dependency_overrides[get_db] = lambda: fake_db

    with TestClient(app) as client:
        headers = {
            "X-Business-ID": str(tenant_a_id),
            "X-User-ID": str(uuid4()),
            "X-User-Role": "owner",
        }
        response = client.get(f"/v1/jobs/{job_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(job_id)
        assert data["business_id"] == str(tenant_a_id)
        assert data["status"] == "succeeded"
        assert data["progress_step"] == 3

    app.dependency_overrides.pop(get_db, None)
