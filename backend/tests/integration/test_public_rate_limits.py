"""PostgreSQL-backed public rate-limit behavior."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.errors import RateLimitedError
from app.models.base import get_session
from app.models.domain import PublicRateLimitBucket
from app.services.public_rate_limits import check_public_rate_limit, rate_limit_key_hash


def test_public_rate_limit_is_shared_and_persists_only_a_hashed_key(db_engine) -> None:
    key = f"rate-limit-test:{uuid4()}"

    check_public_rate_limit(key, max_requests=2, window_seconds=60)
    check_public_rate_limit(key, max_requests=2, window_seconds=60)
    with pytest.raises(RateLimitedError) as limited:
        check_public_rate_limit(key, max_requests=2, window_seconds=60)

    assert limited.value.status_code == 429
    with get_session() as db:
        bucket = db.execute(
            select(PublicRateLimitBucket).where(
                PublicRateLimitBucket.key_hash == rate_limit_key_hash(key)
            )
        ).scalar_one()
    assert bucket.request_count == 3
    assert key not in bucket.key_hash
