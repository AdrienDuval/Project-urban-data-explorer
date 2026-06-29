"""Map layer endpoints consumed by the interactive frontend."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from api.dependencies import SpatialStoreDep
from api.services import map_service

router = APIRouter()


@router.get("/vivabilite-familiale", response_model=None, summary="IRIS GeoJSON with liveability scores")
def get_vivabilite_map(spatial: SpatialStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_vivabilite_geojson(spatial)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/vivabilite-familiale/arrondissement", response_model=None, summary="Arrondissement GeoJSON with liveability")
def get_vivabilite_arrondissement_map(spatial: SpatialStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_vivabilite_arrondissement_geojson(spatial)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/thermal-comfort", response_model=None, summary="IRIS GeoJSON with thermal comfort scores")
def get_thermal_comfort_map(spatial: SpatialStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_thermal_comfort_geojson(spatial)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/housing/rent", response_model=None, summary="Arrondissement GeoJSON with rent scores")
def get_rent_map(spatial: SpatialStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_rent_geojson(spatial)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/housing/sale", response_model=None, summary="Arrondissement GeoJSON with sale price scores")
def get_sale_map(spatial: SpatialStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_sale_geojson(spatial)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/housing/sale/timeline",
    response_model=None,
    summary="Arrondissement sale-price GeoJSON with a full quarterly time series",
    description=(
        "Return arrondissement polygons where each feature carries "
        "`prices_by_period` and `scores_by_period` dicts plus a top-level "
        "`periods` list, so the frontend timeline can replay the historical "
        "evolution of median sale prices per m²."
    ),
)
def get_sale_timeline_map(spatial: SpatialStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_sale_timeline_geojson(spatial)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/demographics",
    response_model=None,
    summary="IRIS GeoJSON enriched with demographic and socio-economic scores",
)
def get_demographics_map(spatial: SpatialStoreDep) -> dict[str, Any]:
    try:
        return map_service.build_demographics_geojson(spatial)
    except map_service.MapDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
