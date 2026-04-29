from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from api.dependencies import DataStoreDep, PaginationDep
from api.models.common import PaginatedResponse
from api.models.indicators.thermal_comfort import (
    ThermalComfortArrondissementStats,
    ThermalComfortIndicator,
)
from api.services.indicators import thermal_comfort_service

router = APIRouter()


@router.get(
    "/map",
    summary="GeoJSON FeatureCollection for Mapbox choropleth",
    description="Returns all IRIS zones with thermal comfort scores as GeoJSON.",
)
def get_thermal_comfort_map(store: DataStoreDep):
    geojson = thermal_comfort_service.get_thermal_comfort_map(store)
    if not geojson["features"]:
        raise HTTPException(status_code=404, detail="No thermal comfort data available. Run the Gold pipeline first.")
    return JSONResponse(content=geojson)


@router.get(
    "",
    response_model=PaginatedResponse[ThermalComfortIndicator],
    summary="List thermal comfort scores by IRIS zone",
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
    summary="Thermal comfort aggregated by arrondissement",
)
def list_thermal_comfort_arrondissements(store: DataStoreDep):
    return thermal_comfort_service.list_thermal_comfort_arrondissements(store)


@router.get(
    "/{code_iris}",
    response_model=ThermalComfortIndicator,
    summary="Thermal comfort score for a single IRIS zone",
)
def get_thermal_comfort_indicator(code_iris: str, store: DataStoreDep):
    result = thermal_comfort_service.get_thermal_comfort_indicator(store, code_iris)
    if result is None:
        raise HTTPException(status_code=404, detail=f"IRIS '{code_iris}' not found.")
    return result