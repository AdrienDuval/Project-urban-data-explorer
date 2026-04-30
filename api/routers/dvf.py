"""DVF housing transactions endpoints.

All routes live under the ``/dvf`` prefix (registered in ``main.py``).
"""

from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import DataStoreDep
from api.services import dvf_service

router = APIRouter()


@router.get(
    "/stats",
    summary="DVF housing transaction statistics",
    description=(
        "Return aggregate statistics for housing transactions in Paris: "
        "total count, median prices and surface, price range, and breakdown "
        "by arrondissement and property type."
    ),
)
def get_dvf_stats(store: DataStoreDep):
    return dvf_service.get_dvf_stats(store)


@router.get(
    "/by-year",
    summary="DVF transactions by year",
    description=(
        "Return housing transaction trends grouped by year, including "
        "transaction count, average price per m², and total transaction value."
    ),
)
def get_dvf_by_year(store: DataStoreDep):
    return dvf_service.get_dvf_by_year(store)

