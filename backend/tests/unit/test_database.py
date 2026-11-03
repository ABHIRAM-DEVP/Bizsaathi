"""Tests for the request-scoped database transaction boundary."""

import pytest

from app.models import base


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_get_db_commits_successful_request(monkeypatch):
    monkeypatch.setattr(base.settings, "ENV", "test")
    session = FakeSession()
    monkeypatch.setattr(base, "get_session", lambda: session)
    dependency = base.get_db()

    assert next(dependency) is session
    with pytest.raises(StopIteration):
        next(dependency)

    assert session.committed
    assert not session.rolled_back
    assert session.closed


def test_get_db_rolls_back_failed_request(monkeypatch):
    monkeypatch.setattr(base.settings, "ENV", "test")
    session = FakeSession()
    monkeypatch.setattr(base, "get_session", lambda: session)
    dependency = base.get_db()
    next(dependency)

    with pytest.raises(RuntimeError, match="failed"):
        dependency.throw(RuntimeError("failed"))

    assert not session.committed
    assert session.rolled_back
    assert session.closed


def test_development_request_seeds_only_the_configured_tenant(monkeypatch):
    from app.core.tenancy import DEV_BUSINESS_ID, ensure_development_business

    class Result:
        def scalar_one_or_none(self):
            return None

    class DevelopmentSession(FakeSession):
        def __init__(self):
            super().__init__()
            self.added = []
            self.flushed = False

        def execute(self, statement):
            return Result()

        def add(self, entity):
            self.added.append(entity)

        def flush(self):
            self.flushed = True

    monkeypatch.setattr(base.settings, "ENV", "dev")
    session = DevelopmentSession()
    ensure_development_business(session)

    assert len(session.added) == 1
    assert session.added[0].id == DEV_BUSINESS_ID
    assert session.added[0].name == base.settings.DEV_BUSINESS_NAME
    assert session.added[0].slug == base.settings.DEV_BUSINESS_SLUG
    assert session.flushed
