"""Authentication context and multi-tenancy dependency per docs/15 section 1 and docs/14."""

from uuid import UUID

from fastapi import Depends, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.errors import ForbiddenError, UnauthenticatedError
from app.core.logging import logger

DEV_BUSINESS_ID = UUID("00000000-0000-0000-0000-000000000001")
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
DEMO_TENANT_B_ID = UUID("00000000-0000-0000-0000-000000000011")
DEMO_OPERATOR_ID = UUID("00000000-0000-0000-0000-000000000003")

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


async def get_auth_context(request: Request) -> AuthContext:
    """Extract authenticated tenant context from session/headers, or fallback to dev stub when in dev mode."""
    # Check if context already set by middleware/session
    ctx: AuthContext | None = getattr(request.state, "auth_context", None)
    if ctx is not None:
        return ctx

    # Check for authorization header / cookie / session
    auth_header = request.headers.get("Authorization")
    session_cookie = request.cookies.get("bizsaathi_session")

    # In production/staging, missing auth fails immediately
    if not auth_header and not session_cookie:
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

    # When header/cookie is present, validation will happen in auth service (Phase 1.4)
    # For now, if invalid or unsupported, raise 401
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
