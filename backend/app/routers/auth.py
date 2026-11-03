"""Development-only local account registration and session lifecycle."""

import re
import unicodedata
from uuid import UUID, uuid4

import bcrypt
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dev_sessions import create_dev_session_token, verify_dev_session_token
from app.core.errors import ConflictError, ForbiddenError, UnauthenticatedError
from app.models.base import get_db
from app.models.domain import AppUser, Business
from app.schemas.auth import (
    LocalAccountBusinessResponse,
    LocalAccountLoginRequest,
    LocalAccountRegistrationRequest,
    LocalAccountRegistrationResponse,
    LocalAccountUserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
DEV_SESSION_COOKIE = "bizsaathi_session"
DEV_SESSION_COOKIE_MAX_AGE_SECONDS = 400 * 24 * 60 * 60
PASSWORD_ROUNDS = 12


def _business_slug(name: str, suffix: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    base = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "business"
    return f"{base[:49].rstrip('-')}-{suffix[:12]}"


def _set_local_session_cookie(
    response: Response,
    user_id: UUID,
    business_id: UUID,
    session_version: int,
) -> None:
    token = create_dev_session_token(
        user_id=user_id,
        business_id=business_id,
        secret=settings.SECRET_KEY.get_secret_value(),
        session_version=session_version,
    )
    response.set_cookie(
        key=DEV_SESSION_COOKIE,
        value=token,
        max_age=DEV_SESSION_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        secure=False,
        samesite="strict",
        path="/",
    )


def _registration_response(user: AppUser, business: Business) -> LocalAccountRegistrationResponse:
    return LocalAccountRegistrationResponse(
        user=LocalAccountUserResponse(id=user.id, display_name=user.display_name or "", role="owner"),
        business=LocalAccountBusinessResponse(
            id=business.id,
            name=business.name,
            slug=business.slug,
        ),
    )


@router.post(
    "/local/register",
    response_model=LocalAccountRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="registerLocalDevelopmentAccount",
    summary="Create a local development owner and business",
)
def register_local_account(
    request: LocalAccountRegistrationRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LocalAccountRegistrationResponse:
    """Create an isolated owner and issue a signed, development-only session."""
    if settings.ENV != "dev":
        raise ForbiddenError(detail="Local account registration is only available in development.")

    user_id = uuid4()
    business_id = uuid4()
    business = Business(
        id=business_id,
        name=request.business_name,
        slug=_business_slug(request.business_name, business_id.hex),
    )
    user = AppUser(
        id=user_id,
        business_id=business_id,
        phone_e164=None,
        local_email=request.email,
        local_password_hash=bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt(rounds=PASSWORD_ROUNDS)),
        local_session_version=0,
        identity_type="local_dev",
        role="owner",
        display_name=request.owner_name,
        language="en",
    )
    db.add_all([business, user])
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(detail="An account with this email already exists.") from exc

    _set_local_session_cookie(response, user.id, business.id, user.local_session_version)
    return _registration_response(user, business)


@router.post(
    "/local/login",
    response_model=LocalAccountRegistrationResponse,
    operation_id="loginLocalDevelopmentAccount",
    summary="Sign in to an existing local development account",
)
def login_local_account(
    request: LocalAccountLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LocalAccountRegistrationResponse:
    """Verify local account credentials and issue a signed session for its tenant."""
    if settings.ENV != "dev":
        raise ForbiddenError(detail="Local account sign-in is only available in development.")

    account = db.execute(
        select(AppUser, Business)
        .join(Business, AppUser.business_id == Business.id)
        .where(
            AppUser.local_email == request.email,
            AppUser.identity_type == "local_dev",
            AppUser.role == "owner",
            Business.status == "active",
        )
    ).one_or_none()
    if account is None:
        raise UnauthenticatedError(detail="Email or password is incorrect.")

    user, business = account
    if user.local_password_hash is None or not bcrypt.checkpw(
        request.password.encode("utf-8"),
        user.local_password_hash,
    ):
        raise UnauthenticatedError(detail="Email or password is incorrect.")

    _set_local_session_cookie(response, user.id, business.id, user.local_session_version)
    return _registration_response(user, business)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="logoutLocalDevelopmentAccount",
    summary="Revoke local sessions and clear the session cookie",
)
def logout_local_account(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Response:
    """Revoke this owner's local sessions and clear the browser cookie."""
    token = request.cookies.get(DEV_SESSION_COOKIE)
    if token and settings.ENV == "dev":
        try:
            claims = verify_dev_session_token(token, settings.SECRET_KEY.get_secret_value())
        except ValueError:
            claims = None

        if claims is not None:
            user = db.execute(
                select(AppUser).where(
                    AppUser.id == claims.user_id,
                    AppUser.business_id == claims.business_id,
                    AppUser.identity_type == "local_dev",
                    AppUser.role == "owner",
                )
            ).scalar_one_or_none()
            if user and user.local_session_version == claims.session_version:
                user.local_session_version += 1

    response.delete_cookie(
        key=DEV_SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=False,
        samesite="strict",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
