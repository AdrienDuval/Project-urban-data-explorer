"""Family liveability indicator endpoints.

All routes live under the ``/indicators/vivabilite-familiale`` prefix.
Each response combines IRIS administrative metadata, census population,
expanded non-price family sub-scores, and the composite vivabilite_score.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import DataStoreDep, PaginationDep
from api.models.common import PaginatedResponse
from api.models.indicators.vivabilite import (
    VivabiliteArrondissementStats,
    VivabiliteIndicator,
)
from api.services.indicators import vivabilite_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[VivabiliteIndicator],
    summary="List family liveability scores by IRIS zone",
    description=(
        "Return a paginated list of Paris IRIS zones sorted by vivabilite_rank "
        "(rank 1 = most family-friendly zone). Each record includes expanded "
        "sub-scores for schools, childcare, safety, healthcare, environment, "
        "green spaces, transport, and daily services. Filter by arrondissement "
        "or score range."
    ),
)
def list_vivabilite_indicators(
    store: DataStoreDep,
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(
        None,
        description="Case-insensitive partial match on the arrondissement name.",
    ),
    min_score: Optional[float] = Query(
        None, ge=0, le=10, description="Minimum vivabilite_score (inclusive)."
    ),
    max_score: Optional[float] = Query(
        None, ge=0, le=10, description="Maximum vivabilite_score (inclusive)."
    ),
):
    return vivabilite_service.list_vivabilite_indicators(
        store,
        arrondissement=arrondissement,
        min_score=min_score,
        max_score=max_score,
        **pagination,
    )


@router.get(
    "/arrondissements",
    response_model=List[VivabiliteArrondissementStats],
    summary="Family liveability aggregated by arrondissement",
    description=(
        "Return population-weighted liveability statistics for every Paris "
        "arrondissement, sorted alphabetically. Includes averages for all "
        "expanded family sub-scores and the composite score."
    ),
)
def list_vivabilite_arrondissements(store: DataStoreDep):
    return vivabilite_service.list_vivabilite_arrondissements(store)


@router.get(
    "/arrondissements/{arrondissement}",
    response_model=VivabiliteArrondissementStats,
    summary="Family liveability for a single arrondissement",
    description=(
        "Return aggregated family liveability metrics for one arrondissement. "
        "The path parameter is matched case-insensitively (e.g. ``7e``, ``Paris 7e``)."
    ),
)
def get_vivabilite_arrondissement(arrondissement: str, store: DataStoreDep):
    result = vivabilite_service.get_vivabilite_arrondissement(store, arrondissement)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Arrondissement '{arrondissement}' not found.",
        )
    return result


@router.get(
    "/{code_iris}",
    response_model=VivabiliteIndicator,
    summary="Family liveability score for a single IRIS zone",
    description=(
        "Return the full family liveability indicator for one IRIS zone: "
        "administrative metadata, census population, expanded sub-scores, "
        "composite score, and Paris-wide rank."
    ),
)
def get_vivabilite_indicator(code_iris: str, store: DataStoreDep):
    result = vivabilite_service.get_vivabilite_indicator(store, code_iris)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"IRIS zone '{code_iris}' not found.",
        )
    return result
