"""Zone click analytics backed by MongoDB (see ``src.mongodb``)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models.zone_analytics import (
    UserInterestRow,
    UserInterestsResponse,
    ZoneClickBody,
    ZoneClickResponse,
    ZoneTotalRow,
    ZoneTotalsResponse,
)
from src import mongodb as mongo

router = APIRouter()


@router.post(
    "",
    response_model=ZoneClickResponse,
    summary="Record a zone click",
    description=(
        "Increments interest for ``user_key`` × ``zone_id``. "
        "Call this when the user selects an IRIS / zone polygon on the map."
    ),
)
def post_zone_click(body: ZoneClickBody) -> ZoneClickResponse:
    if mongo.get_mongo_db() is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is not configured (set MONGO_URI).",
        )
    ok = mongo.record_zone_click(
        user_key=body.user_key.strip(),
        zone_id=body.zone_id.strip(),
        zone_name=body.zone_name,
        geography=body.geography,
    )
    if not ok:
        raise HTTPException(status_code=503, detail="Could not write to MongoDB.")
    return ZoneClickResponse(recorded=True)


@router.get(
    "/zones/top",
    response_model=ZoneTotalsResponse,
    summary="Most-clicked zones (all users)",
)
def get_top_zones(limit: int = 50) -> ZoneTotalsResponse:
    if mongo.get_mongo_db() is None:
        raise HTTPException(status_code=503, detail="MongoDB is not configured (set MONGO_URI).")
    rows = mongo.aggregate_zone_totals(limit=min(limit, 200))
    return ZoneTotalsResponse(
        zones=[ZoneTotalRow(**r) for r in rows],
    )


@router.get(
    "/users/{user_key}",
    response_model=UserInterestsResponse,
    summary="Zone interests for one anonymous user",
)
def get_user_zone_interests(user_key: str, limit: int = 50) -> UserInterestsResponse:
    if mongo.get_mongo_db() is None:
        raise HTTPException(status_code=503, detail="MongoDB is not configured (set MONGO_URI).")
    raw = mongo.user_zone_interests(user_key=user_key.strip(), limit=min(limit, 200))
    interests = [
        UserInterestRow(
            user_key=r["user_key"],
            zone_id=r["zone_id"],
            clicks=r["clicks"],
            zone_name=r.get("zone_name"),
            geography=r.get("geography"),
        )
        for r in raw
    ]
    return UserInterestsResponse(interests=interests)
