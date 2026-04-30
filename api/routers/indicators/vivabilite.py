"""Family liveability indicator endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import PaginationDep
from api.models.common import PaginatedResponse
from api.models.indicators.vivabilite import VivabiliteArrondissementStats, VivabiliteIndicator
from api.services.indicators import vivabilite_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[VivabiliteIndicator], summary="List family liveability scores by IRIS zone")
def list_vivabilite_indicators(
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=10),
    max_score: Optional[float] = Query(None, ge=0, le=10),
):
    return vivabilite_service.list_vivabilite_indicators(
        arrondissement=arrondissement, min_score=min_score, max_score=max_score, **pagination
    )


@router.get("/arrondissements", response_model=List[VivabiliteArrondissementStats], summary="Family liveability by arrondissement")
def list_vivabilite_arrondissements():
    return vivabilite_service.list_vivabilite_arrondissements()


@router.get("/arrondissements/{arrondissement}", response_model=VivabiliteArrondissementStats)
def get_vivabilite_arrondissement(arrondissement: str):
    result = vivabilite_service.get_vivabilite_arrondissement(arrondissement)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Arrondissement '{arrondissement}' not found.")
    return result


@router.get("/{code_iris}", response_model=VivabiliteIndicator, summary="Family liveability for a single IRIS zone")
def get_vivabilite_indicator(code_iris: str):
    result = vivabilite_service.get_vivabilite_indicator(code_iris)
    if result is None:
        raise HTTPException(status_code=404, detail=f"IRIS zone '{code_iris}' not found.")
    return result
