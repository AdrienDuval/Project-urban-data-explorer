from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from api.dependencies import PaginationDep, SpatialStoreDep
from api.models.common import PaginatedResponse
from api.models.indicators.thermal_comfort import (
    ThermalComfortArrondissementStats,
    ThermalComfortIndicator,
)
from api.services.indicators import thermal_comfort_service

router = APIRouter()


@router.get("/map", summary="GeoJSON FeatureCollection for thermal comfort choropleth")
def get_thermal_comfort_map(spatial: SpatialStoreDep):
    geojson = thermal_comfort_service.get_thermal_comfort_map(spatial)
    if not geojson["features"]:
        raise HTTPException(status_code=404, detail="No thermal comfort data available.")
    return JSONResponse(content=geojson)


@router.get("", response_model=PaginatedResponse[ThermalComfortIndicator], summary="List thermal comfort scores")
def list_thermal_comfort_indicators(
    spatial: SpatialStoreDep,
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=10),
):
    return thermal_comfort_service.list_thermal_comfort_indicators(
        spatial,
        arrondissement=arrondissement,
        min_score=min_score,
        offset=(pagination["page"] - 1) * pagination["size"],
        size=pagination["size"],
    )


@router.get("/arrondissements", response_model=List[ThermalComfortArrondissementStats])
def list_thermal_comfort_arrondissements(spatial: SpatialStoreDep):
    return thermal_comfort_service.list_thermal_comfort_arrondissements(spatial)


@router.get("/{code_iris}", response_model=ThermalComfortIndicator)
def get_thermal_comfort_indicator(code_iris: str, spatial: SpatialStoreDep):
    result = thermal_comfort_service.get_thermal_comfort_indicator(spatial, code_iris)
    if result is None:
        raise HTTPException(status_code=404, detail=f"IRIS '{code_iris}' not found.")
    return result
