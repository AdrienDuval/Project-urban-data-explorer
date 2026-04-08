"""Statistics endpoints.

All routes live under the ``/stats`` prefix (registered in ``main.py``).
"""

from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import DataStoreDep
from api.models.stats import CityStats
from api.services import stats_service

router = APIRouter()


@router.get(
    "",
    response_model=CityStats,
    summary="City-wide statistics",
    description=(
        "Return aggregate statistics for the entire Paris school-accessibility "
        "index: total counts, score distribution, and a breakdown of the school "
        "catalog by type."
    ),
)
def get_city_stats(store: DataStoreDep):
    return stats_service.get_city_stats(store)
