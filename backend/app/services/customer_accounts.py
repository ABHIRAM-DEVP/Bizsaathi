"""Customer account registration and revocable browser sessions."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, Header, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, ForbiddenError, UnauthenticatedError
from app.models.base import get_db
from app.models.domain import CustomerAccount, CustomerAuthSession
from app.schemas.customer_accounts import (
    CustomerAccountLoginRequest,
    CustomerAccountRegisterRequest,
    CustomerAccountResponse,
)

CUSTOMER_SESSION_COOKIE = "bizsaathi_customer"
CUSTOMER_SESSION_TTL = timedelta(days=30)
_PASSWORD_ROUNDS = 12


def validate_customer_request_origin(
    request: Request,
    customer_intent: Annotated[
        str | None,
        Header(alias="X-Customer-Request", description="Required on customer account mutations."),
    ] = None,
) -> None:
    origin = request.headers.get("origin")
    allowed_origins = {
        value.strip()
        for value in settings.CORS_ALLOWED_ORIGINS.split(",")
        if value.strip()
    }
    if (
        customer_intent != "1"
        or origin is None
        or origin not in allowed_origins
    ):
        raise ForbiddenError(detail="Customer requests must come from an approved browser origin.")


def _account_response(account: CustomerAccount) -> CustomerAccountResponse:
    return CustomerAccountResponse(
        id=account.id,
        email=account.email,
        display_name=account.display_name,
    )


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def set_customer_cookie(response: Response, token: str, expires_at: datetime) -> None:
    secure = _secure_cookie_environment()
    response.set_cookie(
        key=CUSTOMER_SESSION_COOKIE,
        value=token,
        max_age=int(CUSTOMER_SESSION_TTL.total_seconds()),
        expires=expires_at,
        httponly=True,
        secure=secure,
        samesite="none" if secure else "lax",
        path="/v1/public",
    )


def _secure_cookie_environment() -> bool:
    from app.core.config import settings

    return settings.ENV in ("staging", "prod")


def clear_customer_cookie(response: Response) -> None:
    secure = _secure_cookie_environment()
    response.delete_cookie(
        key=CUSTOMER_SESSION_COOKIE,
        httponly=True,
        secure=secure,
        samesite="none" if secure else "lax",
        path="/v1/public",
    )


def _start_login_session(
    db: Session,
    response: Response,
    account: CustomerAccount,
) -> CustomerAccountResponse:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + CUSTOMER_SESSION_TTL
    db.add(
        CustomerAuthSession(
            customer_account_id=account.id,
            token_hash=_token_digest(token),
            expires_at=expires_at,
        )
    )
    db.flush()
    set_customer_cookie(response, token, expires_at)
    return _account_response(account)


def register_customer_account(
    db: Session,
    response: Response,
    request: CustomerAccountRegisterRequest,
) -> CustomerAccountResponse:
    account = CustomerAccount(
        email=request.email,
        display_name=request.display_name,
        password_hash=bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt(rounds=_PASSWORD_ROUNDS)),
    )
    db.add(account)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(detail="An account with this email already exists.") from exc
    return _start_login_session(db, response, account)


def login_customer_account(
    db: Session,
    response: Response,
    request: CustomerAccountLoginRequest,
) -> CustomerAccountResponse:
    account = db.execute(
        select(CustomerAccount).where(CustomerAccount.email == request.email)
    ).scalar_one_or_none()
    if account is None or not bcrypt.checkpw(request.password.encode("utf-8"), account.password_hash):
        raise UnauthenticatedError(detail="Email or password is incorrect.")
    return _start_login_session(db, response, account)


def get_authenticated_customer(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerAccount:
    token = request.cookies.get(CUSTOMER_SESSION_COOKIE)
    if not token:
        raise UnauthenticatedError(detail="Sign in with a customer account to use store chat.")
    session = db.execute(
        select(CustomerAuthSession).where(
            CustomerAuthSession.token_hash == _token_digest(token),
            CustomerAuthSession.revoked_at.is_(None),
        )
    ).scalar_one_or_none()
    if session is None or session.expires_at <= datetime.now(UTC):
        raise UnauthenticatedError(detail="Customer session is invalid or expired. Sign in again.")
    account = db.execute(
        select(CustomerAccount).where(CustomerAccount.id == session.customer_account_id)
    ).scalar_one_or_none()
    if account is None:
        raise UnauthenticatedError(detail="Customer account is unavailable. Sign in again.")
    return account


def logout_customer_account(request: Request, response: Response, db: Session) -> None:
    token = request.cookies.get(CUSTOMER_SESSION_COOKIE)
    if token:
        session = db.execute(
            select(CustomerAuthSession).where(
                CustomerAuthSession.token_hash == _token_digest(token),
                CustomerAuthSession.revoked_at.is_(None),
            )
        ).scalar_one_or_none()
        if session is not None:
            session.revoked_at = datetime.now(UTC)
            db.flush()
    clear_customer_cookie(response)
