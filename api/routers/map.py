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
