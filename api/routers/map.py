"""Map layer endpoints consumed by the interactive frontend."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from api.dependencies import DataStoreDep
from api.services import map_service

router = APIRouter()


@router.get(
    "/vivabilite-familiale",
    response_model=None,
    summary="IRIS GeoJSON enriched with family liveability scores",
    description=(
        "Return a GeoJSON FeatureCollection for the interactive map. Each "
        "feature is an IRIS polygon with vivabilite score, rank, population, "
        "and the four sub-scores used by the composite indicator."
    ),
)
def get_vivabilite_map(store: DataStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_vivabilite_geojson(store)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/vivabilite-familiale/arrondissement",
    response_model=None,
    summary="Arrondissement GeoJSON with aggregated family liveability scores",
)
def get_vivabilite_arrondissement_map(store: DataStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_vivabilite_arrondissement_geojson(store)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/thermal-comfort",
    response_model=None,
    summary="IRIS GeoJSON enriched with thermal comfort scores",
    description=(
        "Return an IRIS-level GeoJSON FeatureCollection with the thermal "
        "comfort composite, tree-density sub-score, and cooling-area sub-score."
    ),
)
def get_thermal_comfort_map(store: DataStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_thermal_comfort_geojson(store)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/housing/rent",
    response_model=None,
    summary="Arrondissement GeoJSON enriched with median rent scores",
    description=(
        "Return an arrondissement-level GeoJSON FeatureCollection with median "
        "rent per square metre and an affordability score."
    ),
)
def get_rent_map(store: DataStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_rent_geojson(store)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/housing/sale",
    response_model=None,
    summary="Arrondissement GeoJSON enriched with median sale price scores",
    description=(
        "Return the latest arrondissement-level sale price GeoJSON with median "
        "price per square metre and an affordability score."
    ),
)
def get_sale_map(store: DataStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_sale_geojson(store)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    

@router.get(
    "/demographics",
    response_model=None,
    summary="IRIS GeoJSON enriched with demographic and socio-economic scores",
)
def get_demographics_map(store: DataStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_demographics_geojson(store)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
