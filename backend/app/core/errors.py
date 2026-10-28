"""RFC 7807 Problem Details and Domain Exceptions per docs/15 section 4."""

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ProblemFieldError(BaseModel):
    field: str
    message: str


class ProblemDetails(BaseModel):
    type: str = Field(description="URI reference identifying problem type")
    title: str = Field(description="Short human-readable summary of problem")
    status: int = Field(description="HTTP status code")
    detail: str = Field(description="Human-readable explanation specific to this occurrence")
    request_id: str = Field(description="Request ID for tracing and debugging")
    errors: list[ProblemFieldError] | None = None


class AppException(Exception):
    status_code: int = 500
    type_slug: str = "internal-error"
    title: str = "Internal server error"

    def __init__(
        self,
        detail: str,
        errors: list[dict[str, str]] | list[ProblemFieldError] | None = None,
        status_code: int | None = None,
        type_slug: str | None = None,
        title: str | None = None,
    ):
        super().__init__(detail)
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if type_slug is not None:
            self.type_slug = type_slug
        if title is not None:
            self.title = title
        self.errors = [e if isinstance(e, ProblemFieldError) else ProblemFieldError(**e) for e in (errors or [])]


class ValidationError(AppException):
    status_code = 422
    type_slug = "validation-error"
    title = "Validation error"


class UnauthenticatedError(AppException):
    status_code = 401
    type_slug = "unauthenticated"
    title = "Authentication required"


class ForbiddenError(AppException):
    status_code = 403
    type_slug = "forbidden"
    title = "Forbidden access"


class NotFoundError(AppException):
    status_code = 404
    type_slug = "not-found"
    title = "Resource not found"


class ConflictError(AppException):
    status_code = 409
    type_slug = "conflict"
    title = "Conflict"


class StaleVersionError(AppException):
    status_code = 409
    type_slug = "stale-version"
    title = "Stale version"


class IdempotencyConflictError(AppException):
    status_code = 409
    type_slug = "idempotency-conflict"
    title = "Idempotency conflict"


class InvalidStateError(AppException):
    status_code = 400
    type_slug = "invalid-state"
    title = "Invalid state"


class UnsupportedMediaError(AppException):
    status_code = 415
    type_slug = "unsupported-media"
    title = "Unsupported media type"


class PayloadTooLargeError(AppException):
    status_code = 413
    type_slug = "payload-too-large"
    title = "Payload too large"


class RateLimitedError(AppException):
    status_code = 429
    type_slug = "rate-limited"
    title = "Rate limit exceeded"


class NotImplementedError(AppException):
    status_code = 501
    type_slug = "not-implemented"
    title = "Not implemented"


class ModelUnavailableError(AppException):
    status_code = 503
    type_slug = "model-unavailable"
    title = "Model provider unavailable"


class ConfigurationError(AppException):
    status_code = 500
    type_slug = "configuration-error"
    title = "Configuration error"


class ExternalServiceError(AppException):
    status_code = 502
    type_slug = "external-service-error"
    title = "External service error"

    def __init__(self, service: str, message: str):
        super().__init__(detail=f"{service}: {message}")
        self.service = service


class PolicyDeniedError(AppException):
    status_code = 403
    type_slug = "policy-denied"
    title = "Action denied by policy"


class EvidenceMissingError(AppException):
    status_code = 422
    type_slug = "evidence-missing"
    title = "Required evidence missing"


def build_problem_response(
    status: int,
    type_slug: str,
    title: str,
    detail: str,
    request: Request,
    errors: list[ProblemFieldError] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    payload = ProblemDetails(
        type=f"https://bizsaathi.dev/problems/{type_slug}",
        title=title,
        status=status,
        detail=detail,
        request_id=request_id,
        errors=errors or None,
    ).model_dump(exclude_none=True)
    resp_headers = {"X-Request-ID": request_id}
    if headers:
        resp_headers.update(headers)
    return JSONResponse(status_code=status, content=payload, headers=resp_headers)
