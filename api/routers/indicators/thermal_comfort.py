"""Thermal comfort indicator endpoints."""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from api.dependencies import DataStoreDep, PaginationDep
from api.models.common import PaginatedResponse
from api.models.indicators.thermal_comfort import (
    ThermalComfortIndicator,
    ThermalComfortArrondissementStats
)
from api.services.indicators import thermal_comfort_service

router = APIRouter()

@router.get(
    "",
    response_model=PaginatedResponse[ThermalComfortIndicator],
    summary="List thermal comfort scores by IRIS zone",
    description="Return scores based on tree density and fresh islands (îlots de fraîcheur)."
)
def list_thermal_comfort_indicators(
    store: DataStoreDep,
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=10),
):
    return thermal_comfort_service.list_thermal_comfort_indicators(
        store,
        arrondissement=arrondissement,
        min_score=min_score,
        **pagination,
    )

@router.get(
    "/arrondissements",
    response_model=List[ThermalComfortArrondissementStats],
    summary="Thermal comfort aggregated by arrondissement"
)
def list_thermal_comfort_arrondissements(store: DataStoreDep):
    return thermal_comfort_service.list_thermal_comfort_arrondissements(store)

@router.get(
    "/{code_iris}",
    response_model=ThermalComfortIndicator,
    summary="Thermal comfort score for a single IRIS zone"
)
def get_thermal_comfort_indicator(code_iris: str, store: DataStoreDep):
    result = thermal_comfort_service.get_thermal_comfort_indicator(store, code_iris)
    if result is None:
        raise HTTPException(status_code=404, detail=f"IRIS '{code_iris}' not found.")
    return result