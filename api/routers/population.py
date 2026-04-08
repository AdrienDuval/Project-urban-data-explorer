"""Population endpoints.

All routes live under the ``/population`` prefix (registered in ``main.py``).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import DataStoreDep, PaginationDep
from api.models.common import PaginatedResponse
from api.models.population import PopulationZone
from api.services import population_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[PopulationZone],
    summary="List population zones",
    description=(
        "Return a paginated list of residential Paris IRIS zones with their "
        "2019 INSEE census population.  Only zones with population > 500 and "
        "type TYP_IRIS='H' (residential) are included."
    ),
)
def list_population_zones(
    store: DataStoreDep,
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(
        None,
        description=(
            "Case-insensitive partial match on the arrondissement name "
            "(e.g. '7e' matches 'Paris 7e Arrondissement')."
        ),
    ),
):
    return population_service.list_population_zones(
        store, arrondissement=arrondissement, **pagination
    )


@router.get(
    "/{code_iris}",
    response_model=PopulationZone,
    summary="Get population for an IRIS zone",
    description=(
        "Return the 2019 census population for a single residential IRIS zone.  "
        "Returns 404 for non-residential or unmatched zones."
    ),
)
def get_population_zone(code_iris: str, store: DataStoreDep):
    result = population_service.get_population_zone(store, code_iris)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Population data not found for IRIS zone '{code_iris}'.",
        )
    return result
