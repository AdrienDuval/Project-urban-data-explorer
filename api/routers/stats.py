"""Statistics endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.models.stats import CityStats
from api.services import stats_service

router = APIRouter()


@router.get("", response_model=CityStats, summary="City-wide statistics")
def get_city_stats():
    return stats_service.get_city_stats()
