"""Population endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import PaginationDep
from api.models.common import PaginatedResponse
from api.models.population import PopulationZone
from api.services import population_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[PopulationZone], summary="List population zones")
def list_population_zones(
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(None),
):
    return population_service.list_population_zones(arrondissement=arrondissement, **pagination)


@router.get("/{code_iris}", response_model=PopulationZone, summary="Get population for an IRIS zone")
def get_population_zone(code_iris: str):
    result = population_service.get_population_zone(code_iris)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Population data not found for IRIS zone '{code_iris}'.",
        )
    return result
