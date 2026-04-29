"""Request/response models for zone interest analytics (MongoDB)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ZoneClickBody(BaseModel):
    """Client sends an anonymous ``user_key`` (e.g. UUID in localStorage) and zone identifiers."""

    user_key: str = Field(..., min_length=8, max_length=128, description="Anonymous visitor id (persisted client-side).")
    zone_id: str = Field(..., min_length=1, max_length=64, description="Stable zone id — prefer IRIS code.")
    zone_name: str | None = Field(None, description="Human-readable label for dashboards.")
    geography: str | None = Field(None, description='e.g. "iris" or "arrondissement".')


class ZoneClickResponse(BaseModel):
    recorded: bool
    message: str | None = None


class ZoneTotalRow(BaseModel):
    zone_id: str
    total_clicks: int
    zone_name: str | None = None
    geography: str | None = None


class UserInterestRow(BaseModel):
    user_key: str
    zone_id: str
    clicks: int
    zone_name: str | None = None
    geography: str | None = None


class ZoneTotalsResponse(BaseModel):
    zones: list[ZoneTotalRow]


class UserInterestsResponse(BaseModel):
    interests: list[UserInterestRow]
