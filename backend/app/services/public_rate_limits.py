"""PostgreSQL-backed rate limiting for public endpoints."""

import hashlib
from datetime import UTC, datetime, timedelta
from itertools import count

from sqlalchemy import case, delete
from sqlalchemy.dialects.postgresql import insert

from app.core.errors import RateLimitedError
from app.models.base import get_session
from app.models.domain import PublicRateLimitBucket

_cleanup_counter = count(1)


def rate_limit_key_hash(key: str) -> str:
    return hashlib.sha256(f"bizsaathi-public-rate-v1:{key}".encode("utf-8")).hexdigest()


def check_public_rate_limit(key: str, max_requests: int, window_seconds: int) -> None:
    now = datetime.now(UTC)
    window_start = datetime.fromtimestamp(
        int(now.timestamp()) // window_seconds * window_seconds,
        tz=UTC,
    )
    key_hash = rate_limit_key_hash(key)
    db = get_session()
    try:
        if next(_cleanup_counter) % 100 == 0:
            db.execute(
                delete(PublicRateLimitBucket).where(
                    PublicRateLimitBucket.window_start < now - timedelta(days=1)
                )
            )

        statement = insert(PublicRateLimitBucket).values(
            key_hash=key_hash,
            window_start=window_start,
            request_count=1,
        )
        same_window = PublicRateLimitBucket.window_start == statement.excluded.window_start
        statement = statement.on_conflict_do_update(
            index_elements=[PublicRateLimitBucket.key_hash],
            set_={
                "window_start": case(
                    (same_window, PublicRateLimitBucket.window_start),
                    else_=statement.excluded.window_start,
                ),
                "request_count": case(
                    (same_window, PublicRateLimitBucket.request_count + 1),
                    else_=1,
                ),
            },
            where=PublicRateLimitBucket.window_start <= statement.excluded.window_start,
        ).returning(PublicRateLimitBucket.request_count)
        request_count = db.execute(statement).scalar_one_or_none()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    if request_count is None or request_count > max_requests:
        raise RateLimitedError(
            detail=f"Maximum {max_requests} requests per {window_seconds}s exceeded."
        )
