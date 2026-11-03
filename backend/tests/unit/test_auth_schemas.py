"""Tests for local account registration input validation."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import LocalAccountRegistrationRequest


def test_local_account_registration_accepts_six_character_password() -> None:
    request = LocalAccountRegistrationRequest(
        owner_name="Owner",
        business_name="Toy Shop",
        email="owner@example.com",
        password="seller1",
    )

    assert request.password == "seller1"


def test_local_account_registration_trims_names() -> None:
    request = LocalAccountRegistrationRequest(
        owner_name="  Asha Rao  ",
        business_name="  Asha Toys  ",
        email=" ASHA@Example.COM ",
        password="a-strong-local-password",
    )

    assert request.owner_name == "Asha Rao"
    assert request.business_name == "Asha Toys"
    assert request.email == "asha@example.com"


@pytest.mark.parametrize(
    ("owner_name", "business_name"),
    [
        (" ", "Toy Shop"),
        ("Owner", " "),
        ("x" * 121, "Toy Shop"),
        ("Owner", "x" * 121),
    ],
)
def test_local_account_registration_rejects_blank_or_oversized_names(
    owner_name: str, business_name: str
) -> None:
    with pytest.raises(ValidationError):
        LocalAccountRegistrationRequest(
            owner_name=owner_name,
            business_name=business_name,
            email="owner@example.com",
            password="a-strong-local-password",
        )


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("not-an-email", "a-strong-local-password"),
        ("owner@example.com", "short"),
        ("owner@example.com", "é" * 40),
    ],
)
def test_local_account_registration_rejects_invalid_credentials(email: str, password: str) -> None:
    with pytest.raises(ValidationError):
        LocalAccountRegistrationRequest(
            owner_name="Owner",
            business_name="Toy Shop",
            email=email,
            password=password,
        )
