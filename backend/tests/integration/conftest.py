"""Integration test fixtures with graceful skip if DB is not running."""

import pytest
from sqlalchemy import text

from app.models.base import get_session, get_sync_engine


@pytest.fixture(scope="session")
def db_engine():
    """Check if the DB is reachable; skip integration tests if not."""
    try:
        engine = get_sync_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        pytest.skip(f"Database not reachable ({e}). Skipping integration tests.")


@pytest.fixture
def db_session(db_engine):
    """Provide a database session inside a transaction that is rolled back."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = get_session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
