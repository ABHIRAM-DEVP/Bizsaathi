"""SQLAlchemy base and database engine configuration."""

from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import DateTime, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.core.config import settings

# Naming convention for Alembic autogenerate
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    metadata = metadata


class TimestampMixin:
    """Mixin adding created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


@lru_cache(maxsize=1)
def get_sync_engine():
    """Create a synchronous engine from DATABASE_URL (converts async URL if needed)."""
    url = settings.DATABASE_URL
    # Convert asyncpg URL to psycopg for sync usage
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg")
    return create_engine(url, echo=False)


def get_session() -> Session:
    """Create a new database session."""
    engine = get_sync_engine()
    return Session(engine)


def get_db():
    """FastAPI dependency yielding a managed database session."""
    session = get_session()
    try:
        if settings.ENV == "dev":
            from app.core.tenancy import ensure_development_business

            ensure_development_business(session)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
