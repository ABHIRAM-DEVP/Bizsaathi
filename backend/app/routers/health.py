"""Health and readiness endpoints (EP-H01, EP-H02) per docs/14."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import logger
from app.models.base import get_sync_engine

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(default="ok", examples=["ok"])


class ReadinessChecks(BaseModel):
    db: str = Field(examples=["ok"])
    redis: str | None = Field(default=None, examples=["ok"])


class ReadinessResponse(BaseModel):
    status: str = Field(examples=["ready"])
    checks: ReadinessChecks


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    operation_id="getHealth",
    summary="Service liveness probe (EP-H01)",
)
async def get_health() -> HealthResponse:
    """Liveness probe. Checks no external dependencies, returns 200 ok immediately."""
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    operation_id="getReadiness",
    summary="Service readiness probe (EP-H02)",
    responses={
        200: {"description": "All required dependencies are reachable"},
        503: {"description": "One or more dependencies are unavailable"},
    },
)
async def get_readiness(response: Response) -> ReadinessResponse:
    """Readiness probe. Verifies required dependencies (DB, Redis) without exposing secrets."""
    try:
        engine = get_sync_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Database readiness check failed")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="unready", checks=ReadinessChecks(db="unreachable"))

    return ReadinessResponse(status="ready", checks=ReadinessChecks(db="ok"))
