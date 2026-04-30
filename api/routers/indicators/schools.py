"""School-accessibility indicator endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import PaginationDep
from api.models.common import PaginatedResponse
from api.models.indicators.schools import SchoolArrondissementStats, SchoolIndicator
from api.services.indicators import schools_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[SchoolIndicator], summary="List school-accessibility scores by IRIS zone")
def list_school_indicators(
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
):
    return schools_service.list_school_indicators(
        arrondissement=arrondissement, min_score=min_score, max_score=max_score, **pagination
    )


@router.get("/arrondissements", response_model=List[SchoolArrondissementStats], summary="School-accessibility by arrondissement")
def list_school_arrondissements():
    return schools_service.list_school_arrondissements()


@router.get("/arrondissements/{arrondissement}", response_model=SchoolArrondissementStats)
def get_school_arrondissement(arrondissement: str):
    result = schools_service.get_school_arrondissement(arrondissement)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Arrondissement '{arrondissement}' not found.")
    return result


@router.get("/{code_iris}", response_model=SchoolIndicator, summary="School-accessibility score for a single IRIS zone")
def get_school_indicator(code_iris: str):
    result = schools_service.get_school_indicator(code_iris)
    if result is None:
        raise HTTPException(status_code=404, detail=f"IRIS zone '{code_iris}' not found.")
    return result
