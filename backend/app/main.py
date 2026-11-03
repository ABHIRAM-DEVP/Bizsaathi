"""FastAPI main application entrypoint for BizSaathi."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import (
    AppException,
    ProblemFieldError,
    build_problem_response,
)
from app.core.logging import logger, setup_logging
from app.routers import (
    approvals,
    audit,
    auth,
    businesses,
    conversations,
    dashboard,
    evidence,
    health,
    jobs,
    metrics,
    orders,
    posts,
    products,
    public_store,
    uploads,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    setup_logging()
    logger.info(
        "BizSaathi API starting up",
        extra={"env": settings.ENV, "api_prefix": settings.API_PREFIX},
    )
    async with httpx.AsyncClient(
        timeout=settings.MODEL_REQUEST_TIMEOUT_SECONDS,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    ) as model_http_client:
        app.state.model_http_client = model_http_client
        yield
    logger.info("BizSaathi API shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url=f"{settings.API_PREFIX}/docs",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)
cors_origins = [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
if "*" in cors_origins:
    raise ValueError("CORS_ALLOWED_ORIGINS must not contain a wildcard when credentials are enabled.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "If-Match",
        "Idempotency-Key",
        "X-Demo-Account",
        "X-Local-Account-Required",
        "X-Customer-Request",
        "X-Request-ID",
    ],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Response:
    """Assign X-Request-ID, track duration, and log request lifecycle."""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = f"req_{uuid.uuid4().hex}"
    request.state.request_id = request_id

    start_time = time.perf_counter()
    raw_response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    response: Response = raw_response
    response.headers["X-Request-ID"] = request_id

    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code}",
        extra={
            "request_id": request_id,
            "duration_ms": duration_ms,
        },
    )
    return response


# --- RFC 7807 Exception Handlers ---


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> Response:
    return build_problem_response(
        status=exc.status_code,
        type_slug=exc.type_slug,
        title=exc.title,
        detail=exc.detail,
        request=request,
        errors=exc.errors,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    field_errors = [
        ProblemFieldError(
            field=".".join(str(loc) for loc in err.get("loc", []) if loc != "body"),
            message=err.get("msg", "Validation error"),
        )
        for err in exc.errors()
    ]
    return build_problem_response(
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        type_slug="validation-error",
        title="Validation error",
        detail="The request body or parameters failed validation.",
        request=request,
        errors=field_errors,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
    type_slug = "not-found" if exc.status_code == 404 else "http-error"
    title = "Resource not found" if exc.status_code == 404 else "HTTP error"
    return build_problem_response(
        status=exc.status_code,
        type_slug=type_slug,
        title=title,
        detail=str(exc.detail),
        request=request,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    logger.error(
        "Unhandled server exception",
        extra={
            "request_id": getattr(request.state, "request_id", "req_unknown"),
            "exception_type": type(exc).__name__,
        },
    )
    return build_problem_response(
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        type_slug="internal-server-error",
        title="Internal server error",
        detail="An unexpected internal error occurred.",
        request=request,
    )


# Mount routers under /v1
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(businesses.router, prefix=settings.API_PREFIX)
app.include_router(uploads.router, prefix=settings.API_PREFIX)
app.include_router(jobs.router, prefix=settings.API_PREFIX)
app.include_router(products.router, prefix=settings.API_PREFIX)
app.include_router(orders.router, prefix=settings.API_PREFIX)
app.include_router(approvals.router, prefix=settings.API_PREFIX)
app.include_router(posts.router, prefix=settings.API_PREFIX)
app.include_router(conversations.router, prefix=settings.API_PREFIX)
app.include_router(evidence.router, prefix=settings.API_PREFIX)
app.include_router(audit.router, prefix=settings.API_PREFIX)
app.include_router(public_store.router, prefix=settings.API_PREFIX)

app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(metrics.router, prefix=settings.API_PREFIX)
