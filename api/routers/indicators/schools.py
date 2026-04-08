"""School-accessibility indicator endpoints.

All routes live under the ``/indicators/schools`` prefix (registered in
``main.py``).  Each response combines IRIS administrative data, census
population, and gold-layer school-density metrics.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import DataStoreDep, PaginationDep
from api.models.common import PaginatedResponse
from api.models.indicators.schools import SchoolArrondissementStats, SchoolIndicator
from api.services.indicators import schools_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[SchoolIndicator],
    summary="List school-accessibility scores by IRIS zone",
    description=(
        "Return a paginated list of Paris IRIS zones with their combined "
        "administrative metadata, census population, and school-density metrics "
        "(count, rate per 1 000 residents, normalised 0–100 score).  "
        "Filter by arrondissement or score range."
    ),
)
def list_school_indicators(
    store: DataStoreDep,
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(
        None,
        description=(
            "Case-insensitive partial match on the arrondissement name "
            "(e.g. '7e' matches 'Paris 7e Arrondissement')."
        ),
    ),
    min_score: Optional[float] = Query(
        None, ge=0, le=100, description="Minimum school_score (inclusive)."
    ),
    max_score: Optional[float] = Query(
        None, ge=0, le=100, description="Maximum school_score (inclusive)."
    ),
):
    return schools_service.list_school_indicators(
        store,
        arrondissement=arrondissement,
        min_score=min_score,
        max_score=max_score,
        **pagination,
    )


@router.get(
    "/arrondissements",
    response_model=List[SchoolArrondissementStats],
    summary="School-accessibility aggregated by arrondissement",
    description=(
        "Return population-weighted school-accessibility statistics for every "
        "Paris arrondissement, sorted alphabetically."
    ),
)
def list_school_arrondissements(store: DataStoreDep):
    return schools_service.list_school_arrondissements(store)


@router.get(
    "/arrondissements/{arrondissement}",
    response_model=SchoolArrondissementStats,
    summary="School-accessibility for a single arrondissement",
    description=(
        "Return aggregated school-accessibility metrics for one arrondissement.  "
        "The path parameter is matched case-insensitively (e.g. ``7e``, ``Paris 7e``)."
    ),
)
def get_school_arrondissement(arrondissement: str, store: DataStoreDep):
    result = schools_service.get_school_arrondissement(store, arrondissement)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Arrondissement '{arrondissement}' not found.",
        )
    return result


@router.get(
    "/{code_iris}",
    response_model=SchoolIndicator,
    summary="School-accessibility score for a single IRIS zone",
    description=(
        "Return the full school-accessibility indicator for one IRIS zone: "
        "administrative metadata, census population, and school-density metrics."
    ),
)
def get_school_indicator(code_iris: str, store: DataStoreDep):
    result = schools_service.get_school_indicator(store, code_iris)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"IRIS zone '{code_iris}' not found.",
        )
    return result
