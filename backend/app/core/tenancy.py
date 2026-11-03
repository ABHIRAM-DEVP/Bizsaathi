"""Authentication context and multi-tenancy dependency per docs/15 section 1 and docs/14."""

from uuid import UUID

from fastapi import Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dev_sessions import verify_dev_session_token
from app.core.errors import ForbiddenError, UnauthenticatedError
from app.core.logging import logger
from app.models.base import get_db
from app.models.domain import AppUser, Business

DEV_BUSINESS_ID = UUID("00000000-0000-0000-0000-000000000001")
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
DEMO_TENANT_B_ID = UUID("00000000-0000-0000-0000-000000000011")
DEMO_OPERATOR_ID = UUID("00000000-0000-0000-0000-000000000003")


def ensure_development_business(session: Session) -> None:
    """Create the configured development tenant when a real DB-backed request arrives."""
    if settings.ENV != "dev":
        return

    from app.models.domain import Business

    business = session.execute(select(Business).where(Business.id == DEV_BUSINESS_ID)).scalar_one_or_none()
    if business is None:
        session.add(
            Business(
                id=DEV_BUSINESS_ID,
                name=settings.DEV_BUSINESS_NAME,
                slug=settings.DEV_BUSINESS_SLUG,
            )
        )
        session.flush()


DEMO_ACCOUNTS = {
    "demo-owner": (DEV_BUSINESS_ID, DEV_USER_ID, "owner"),
    "demo-operator": (DEV_BUSINESS_ID, DEMO_OPERATOR_ID, "operator"),
    "demo-tenant-b-owner": (DEMO_TENANT_B_ID, UUID("00000000-0000-0000-0000-000000000012"), "owner"),
}


class AuthContext(BaseModel):
    business_id: UUID = Field(description="Tenant identifier")
    user_id: UUID = Field(description="Authenticated user identifier")
    role: str = Field(default="owner", description="Role: owner, operator, or public")
    is_dev_stub: bool = Field(default=False, description="True if generated from dev stub")


async def get_auth_context(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    """Extract authenticated tenant context from session/headers, or fallback to dev stub when in dev mode."""
    # Check if context already set by middleware/session
    ctx: AuthContext | None = getattr(request.state, "auth_context", None)
    if ctx is not None:
        return ctx

    session_cookie = request.cookies.get("bizsaathi_session")
    if session_cookie:
        if settings.ENV != "dev":
            raise UnauthenticatedError(detail="Local development sessions are not available in this environment.")
        try:
            claims = verify_dev_session_token(session_cookie, settings.SECRET_KEY.get_secret_value())
        except ValueError as exc:
            raise UnauthenticatedError(detail="Invalid or expired local development session.") from exc

        user = db.execute(
            select(AppUser)
            .join(Business, AppUser.business_id == Business.id)
            .where(
                AppUser.id == claims.user_id,
                AppUser.business_id == claims.business_id,
                AppUser.identity_type == "local_dev",
                AppUser.role == "owner",
                Business.status == "active",
            )
        ).scalar_one_or_none()
        if user is None:
            raise UnauthenticatedError(detail="Local development account is unavailable.")
        if user.local_session_version != claims.session_version:
            raise UnauthenticatedError(detail="Your local session was signed out. Sign in again.")

        session_ctx = AuthContext(
            business_id=user.business_id,
            user_id=user.id,
            role=user.role,
            is_dev_stub=False,
        )
        request.state.auth_context = session_ctx
        return session_ctx

    if request.headers.get("x-local-account-required") == "true":
        raise UnauthenticatedError(
            detail="Sign in to your local account to continue."
        )

    # In production/staging, missing auth fails immediately
    if not request.headers.get("Authorization"):
        if settings.ENV in ("dev", "test"):
            # Dev stub: strictly allowed in dev/test only and clearly labelled
            dev_b_id = DEV_BUSINESS_ID
            dev_u_id = DEV_USER_ID
            dev_role = "owner"

            demo_account = request.headers.get("x-demo-account")
            if demo_account in DEMO_ACCOUNTS:
                dev_b_id, dev_u_id, dev_role = DEMO_ACCOUNTS[demo_account]
            elif demo_account:
                raise UnauthenticatedError(detail="Unknown demo account")
            if "x-business-id" in request.headers and not demo_account:
                try:
                    dev_b_id = UUID(request.headers["x-business-id"])
                except ValueError:
                    pass
            if "x-user-id" in request.headers and not demo_account:
                try:
                    dev_u_id = UUID(request.headers["x-user-id"])
                except ValueError:
                    pass
            if "x-user-role" in request.headers and not demo_account:
                dev_role = request.headers["x-user-role"]

            logger.debug(
                "Using DEV STUB auth context",
                extra={"request_id": getattr(request.state, "request_id", None)},
            )
            stub_ctx = AuthContext(
                business_id=dev_b_id,
                user_id=dev_u_id,
                role=dev_role,
                is_dev_stub=True,
            )
            request.state.auth_context = stub_ctx
            return stub_ctx

        raise UnauthenticatedError(detail="Missing authentication credentials")

    raise UnauthenticatedError(detail="Invalid session or token")


async def require_tenant(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    """Ensure valid tenant context exists."""
    if not ctx.business_id:
        raise UnauthenticatedError(detail="No tenant business associated with context")
    return ctx


async def require_owner_role(ctx: AuthContext = Depends(require_tenant)) -> AuthContext:
    """Ensure user has 'owner' role."""
    if ctx.role != "owner":
        raise ForbiddenError(detail="Owner privileges required for this action")
    return ctx
