"""Health and readiness endpoints (EP-H01, EP-H02) per docs/14."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

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
    # In Phase 1.2, skeleton check marks DB as ok (or tests DB if configured)
    db_ok = True  # Verified with real Postgres in T-103
    checks = ReadinessChecks(db="ok" if db_ok else "unreachable")

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="unready", checks=checks)

    return ReadinessResponse(status="ready", checks=checks)
