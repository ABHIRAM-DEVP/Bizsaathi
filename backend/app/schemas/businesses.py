"""Schemas for owner business profile information used to share public store links."""

from uuid import UUID

from pydantic import BaseModel


class BusinessProfileResponse(BaseModel):
    id: UUID
    name: str
    slug: str
